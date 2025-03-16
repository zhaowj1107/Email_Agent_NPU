import os
import sys
import base64
import pickle
import re
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

module_path = os.path.abspath("toolkit")
sys.path.append(module_path)

import log_IO as log

# Gmail API 需要的作用域（权限）
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def authenticate_gmail():
    """ 认证 Gmail API 并返回服务对象 """
    creds = None

    # 加载保存的 token
    if os.path.exists("token_gmail.pickle"):
        with open("token_gmail.pickle", "rb") as token:
            creds = pickle.load(token)

    # 如果没有凭据或凭据失效，则重新认证
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Get the directory of the current script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Construct the path to the credentials file
            credentials_path = os.path.join(current_dir, "credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # 保存新的 token
        with open("token_gmail.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)

def read_emails(service, max_results=1):
    """ 读取 Gmail 收件箱中的最新邮件并返回详细信息 """
    results = service.users().messages().list(userId="me", maxResults=max_results).execute()
    messages = results.get("messages", [])
    
    if not messages:
        return {"sender": "", "subject": "", "body": "No messages found."}
    
    # 获取最新邮件
    msg = messages[0]
    msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
    
    # 提取信息
    headers = msg_data["payload"]["headers"]
    sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Unknown Sender")
    subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")
    
    # 提取邮件正文
    body = ""
    if "parts" in msg_data["payload"]:
        for part in msg_data["payload"]["parts"]:
            if part["mimeType"] == "text/plain":
                if "data" in part["body"]:
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break
    elif "body" in msg_data["payload"] and "data" in msg_data["payload"]["body"]:
        body = base64.urlsafe_b64decode(msg_data["payload"]["body"]["data"]).decode("utf-8")
    
    # Add message_id to the returned data for use in archiving
    email_info = {
        "sender": sender,
        "subject": subject,
        "body": body,
        "message_id": msg["id"]
    }
    
    print("Latest email retrieved successfully")
    return email_info

def create_email(sender, to, subject, body):
    """ 创建邮件(MIME 格式) """
    message = MIMEText(body)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_email(service, sender, to, subject, body):
    """ 发送邮件 """
    message = create_email(sender, to, subject, body)
    message = service.users().messages().send(userId="me", body=message).execute()
    log.log_email(subject, to, body, "Sent")
    print(f"Email sent! Message ID: {message['id']}")

def reply_email(service, sender, to, subject, body, thread_id=None, message_id=None):
    """
    Reply to an existing email thread.
    
    Args:
        service: The Gmail API service object
        sender: The sender's email address
        to: The recipient's email address
        subject: The email subject (will be prefixed with 'Re:' if not already)
        body: The email body
        thread_id: The ID of the thread to reply to (optional)
        message_id: The ID of the specific message to reply to (optional)
    
    Returns:
        dict: The sent message details or None if an error occurred
    """
    try:
        # Ensure subject has 'Re:' prefix
        if not subject.startswith('Re:'):
            subject = f'Re: {subject}'
        
        # Create a MIMEText message
        message = MIMEText(body)
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        
        # If thread_id is provided, include it in headers
        raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        
        if thread_id:
            # Add the threadId to the request
            sent_message = service.users().messages().send(
                userId='me', 
                body=raw_message,
                threadId=thread_id
            ).execute()
        else:
            # Standard send without threadId
            sent_message = service.users().messages().send(
                userId='me', 
                body=raw_message
            ).execute()
        
        print(f'Reply sent! Message ID: {sent_message["id"]}')
        return sent_message
    
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def archive_emails(service, message_id=None, query=None):
    """Archives a specific email by ID or emails matching the given query.

    Args:
        service: The Gmail API service object.
        message_id: The ID of the specific email to archive. If provided, query is ignored.
        query: The search query to find emails to archive. Only used if message_id is None.
               Example: "from:someone@example.com subject:Important"
    """
    try:
        messages = []
        
        if message_id:
            # Archive a specific email by ID
            messages = [{"id": message_id}]
            print(f"Archiving specific email with ID: {message_id}")
        elif query:
            # List messages matching the query
            results = service.users().messages().list(userId="me", q=query).execute()
            messages = results.get("messages", [])
            
            if not messages:
                print("No messages found matching the query.")
                return
        else:
            print("Error: Either message_id or query must be provided.")
            return

        for message in messages:
            message_id = message["id"]

            # Modify the message to remove the INBOX label
            modify_request_body = {
                "removeLabelIds": ["INBOX"]
            }
            service.users().messages().modify(
                userId="me", id=message_id, body=modify_request_body
            ).execute()

            print(f"Archived message with ID: {message_id}")

    except HttpError as error:
        print(f"An error occurred: {error}")


def simple_draft(service, sender_email, to_email, subject, message_content):
    """
    Generate a simple draft WITHOUT calling RAG
    
    Args:
        service: The Gmail API service object
        sender_email: The sender's email address
        to_email: The recipient's email address
        subject: Email subject line
        message_content: Original content to be processed by deepseek
    
    Returns:
        The created draft object
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
        sys.path.append(parent_dir)

        from ALLM_api import Chatbot
        
        # Define the prompt in English
        system_msg = """
        This is an email body. Please generate a reply draft based on the content.
        Requirements:
        - Be professional and concise
        - Address the key points in the original email
        - Maintain a respectful tone
        - Keep the response under 300 words
        """
        
        # Create a new Chatbot object and process the content
        chatbot = Chatbot()
        processed_content = chatbot.chat(message_content, system_msg)
        
        # Create a MIMEText message
        message = MIMEText(processed_content)
        message["to"] = to_email
        message["from"] = sender_email
        message["subject"] = subject
        
        # Encode the message to base64url format
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Create the draft message
        draft = {
            'message': {
                'raw': encoded_message
            }
        }
        
        # Call the Gmail API to create the draft
        created_draft = service.users().drafts().create(userId="me", body=draft).execute()
        
        print(f"Draft created successfully with ID: {created_draft['id']}")
        return created_draft
    
    except ImportError:
        print("Error: Could not import Chatbot from local_model.ALLM_api")
        return None
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


def draft_rag(service, sender_email, to_email, subject, message_content):
    """
    根据邮件内容生成一组关键词如[school, deadline, client]
    向RAG求这些关键词的返回值形成字典,如{school：NEU, Deadline: 2025-03-15, client: Zhaowj}   
    根据字典信息生成邮件的草稿
    
    Args:
        service: The Gmail API service object
        sender_email: The sender's email address
        to_email: The recipient's email address
        subject: Email subject line
        message_content: Original email content
    
    Returns:
        The created draft object
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
        sys.path.append(parent_dir)
        
        from ALLM_api import Chatbot
        
        # Step 1: Use LLM to extract keywords
        keyword_extraction_system_msg = """
        Extract keywords from the following email content as a comma-separated list.
        For example: school, deadline, client, project
        Return only the keyword list without any other content.
        """
        
        # Create a Chatbot instance for keyword extraction
        keyword_chatbot = Chatbot()
        keywords_text = keyword_chatbot.chat(message_content, keyword_extraction_system_msg)
        
        # Process the keyword text, convert to list
        keywords = [keyword.strip() for keyword in keywords_text.split(',')]
        print(f"Extracted keywords: {keywords}")
        
        # Step 2: Interface with RAG system
        # This is a placeholder for the actual RAG system call
        def call_rag_system(keywords):
            """
            Call the RAG system to get information related to the keywords
            This will be replaced with actual RAG implementation
            """
            # Simulate RAG results
            rag_results = {
                # This will be replaced with real RAG system return values
                keyword: f"Sample value for {keyword}" for keyword in keywords
            }
            return rag_results
        
        # Get RAG results
        rag_info = call_rag_system(keywords)
        print(f"RAG information: {rag_info}")
        
        # Step 3: Generate draft using LLM with RAG information
        draft_system_msg = f"""
        Generate a professional email reply draft based on the following information:
        
        Original email subject: {subject}
        
        Key information:
        {', '.join([f'{k}: {v}' for k, v in rag_info.items()])}
        
        Requirements:
        1. Use formal, professional language
        2. Ensure the reply addresses the original email content
        3. Include all necessary key information
        4. Keep it concise, under 300 words
        """
        
        # Create a Chatbot instance for draft generation
        draft_chatbot = Chatbot()
        draft_content = draft_chatbot.chat(message_content, draft_system_msg)
        
        # Create MIME message
        message = MIMEText(draft_content)
        message["to"] = to_email
        message["from"] = sender_email
        message["subject"] = f"Re: {subject}"
        
        # Encode message to base64url format
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Create draft message
        draft = {
            'message': {
                'raw': encoded_message
            }
        }
        
        # Call Gmail API to create draft
        created_draft = service.users().drafts().create(userId="me", body=draft).execute()
        
        print(f"Draft created successfully with ID: {created_draft['id']}")
        return created_draft
    
    except ImportError:
        print("Error: Could not import Chatbot from local_model.ALLM_api")
        return None
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None


if __name__ == "__main__":
    service = authenticate_gmail()
    
    # 读取邮件
    print("Reading Emails...\n")
    dict_latest_email = read_emails(service)
    print(dict_latest_email)

    # 发送邮件
    sender_email = "fiveguysteam0@gmail.com"  # 你的 Gmail 地址
    receiver_email = "zhaowj1107@gmail.com"  # 收件人 Gmail 地址
    subject = "Test Email from Python_0310"
    body = "Hello! This is a test email sent using Gmail API and Python."

    send_email(service, sender_email, receiver_email, subject, body)
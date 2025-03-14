import os
import base64
import pickle
import re
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
    
    email_info = {
        "sender": sender,
        "subject": subject,
        "body": body
    }
    
    print("Latest email retrieved successfully")
    return email_info

def create_email(sender, to, subject, body):
    """ 创建邮件（MIME 格式） """
    message = MIMEText(body)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_email(service, sender, to, subject, body):
    """ 发送邮件 """
    message = create_email(sender, to, subject, body)
    message = service.users().messages().send(userId="me", body=message).execute()
    print(f"Email sent! Message ID: {message['id']}")


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
        from local_model.ds_api import deepseek
        # 这里deepseek()是之前生邮件summary的prompt
        # 考虑deepseek函数可以将prompt作为另一个参数传入
        
        # Define the prompt directly within the function
        # This prompt can be easily edited as needed
        prompt = """
        这是邮件的正文，请根据内容生成一个回复邮件的草稿
        要求：
        
        """
        
        # Process the content using deepseek with the defined prompt
        # Note: The current deepseek function doesn't accept a prompt parameter
        # If deepseek function is updated to accept a prompt, this should be modified
        processed_content = deepseek(message_content)
        
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
        print("Error: Could not import deepseek from local_model.ds_api")
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
    sender_email = "zhaowj1107@gmail.com"  # 你的 Gmail 地址
    receiver_email = "zhao.weij@northeastern.edu"  # 收件人 Gmail 地址
    subject = "Test Email from Python_0310"
    body = "Hello! This is a test email sent using Gmail API and Python."

    send_email(service, sender_email, receiver_email, subject, body)

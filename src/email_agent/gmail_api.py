<<<<<<< HEAD:src/email_agent/gmail_api.py
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
    log.log_email(subject, to, body, "Sent")
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


=======
>>>>>>> cfd45ae4e16e4ec25c34c34e278b51834fdf2922:email_agent/gmail_api.py
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
<<<<<<< HEAD:src/email_agent/gmail_api.py
        from local_model.ds_api import deepseek
=======
        from local_model.ALLM_api import Chatbot
>>>>>>> cfd45ae4e16e4ec25c34c34e278b51834fdf2922:email_agent/gmail_api.py
        
        # 步骤1: 使用LLM提取关键词
        keyword_extraction_prompt = """
        请从以下邮件内容中提取关键词，以逗号分隔的列表形式返回。
        例如：school, deadline, client, project
        只返回关键词列表，不要有其他内容。
        """
        
<<<<<<< HEAD:src/email_agent/gmail_api.py
        # 调用LLM提取关键词
        keywords_text = deepseek(message_content + "\n\n" + keyword_extraction_prompt)
=======
        # 创建Chatbot实例并调用提取关键词
        keyword_chatbot = Chatbot()
        keywords_text = keyword_chatbot.chat(message_content, keyword_extraction_prompt)
>>>>>>> cfd45ae4e16e4ec25c34c34e278b51834fdf2922:email_agent/gmail_api.py
        
        # 处理关键词文本，转换为列表
        keywords = [keyword.strip() for keyword in keywords_text.split(',')]
        print(f"Extracted keywords: {keywords}")
        
        # 步骤2: 预留RAG接口调用
        # 这里应该是调用外部RAG系统的代码
        # 示例代码，实际实现需要替换为真实的RAG调用
        def call_rag_system(keywords):
            """
            调用RAG系统获取关键词的相关信息
            实际使用时需要替换为真实的RAG系统调用
            """
            # 模拟RAG返回的字典
            rag_results = {
                # 这里将来会被真实的RAG系统返回值替换
                keyword: f"Sample value for {keyword}" for keyword in keywords
            }
            return rag_results
        
        # 获取RAG结果
        rag_info = call_rag_system(keywords)
        print(f"RAG information: {rag_info}")
        
        # 步骤3: 赋值prompt变量
        prompt = f"""
<<<<<<< HEAD:src/email_agent/gmail_api.py
        请根据以下信息生成1封专业的邮件回复草稿:
=======
        请根据以下信息生成一封专业的邮件回复草稿:
>>>>>>> cfd45ae4e16e4ec25c34c34e278b51834fdf2922:email_agent/gmail_api.py
        
        原始邮件主题: {subject}
        
        关键信息:
        {', '.join([f'{k}: {v}' for k, v in rag_info.items()])}
        
        要求:
        1. 使用正式、专业的语言
        2. 确保回复针对原始邮件的内容
        3. 包含所有必要的关键信息
        4. 保持简洁明了，不超过300字
        """
        
        # 步骤4: 调用LLM生成邮件草稿
<<<<<<< HEAD:src/email_agent/gmail_api.py
        draft_content = deepseek(message_content + "\n\n" + prompt)
=======
        draft_chatbot = Chatbot()
        draft_content = draft_chatbot.chat(message_content, prompt)
>>>>>>> cfd45ae4e16e4ec25c34c34e278b51834fdf2922:email_agent/gmail_api.py
        
        # 创建MIME消息
        message = MIMEText(draft_content)
        message["to"] = to_email
        message["from"] = sender_email
        message["subject"] = f"Re: {subject}"
        
        # 编码消息为base64url格式
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # 创建草稿消息
        draft = {
            'message': {
                'raw': encoded_message
            }
        }
        
        # 调用Gmail API创建草稿
        created_draft = service.users().drafts().create(userId="me", body=draft).execute()
        
        print(f"Draft created successfully with ID: {created_draft['id']}")
        return created_draft
    
    except ImportError:
<<<<<<< HEAD:src/email_agent/gmail_api.py
        print("Error: Could not import deepseek from local_model.ds_api")
=======
        print("Error: Could not import Chatbot from local_model.ALLM_api")
>>>>>>> cfd45ae4e16e4ec25c34c34e278b51834fdf2922:email_agent/gmail_api.py
        return None
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

<<<<<<< HEAD:src/email_agent/gmail_api.py

if __name__ == "__main__":
    service = authenticate_gmail()
    
    # 读取邮件
    print("Reading Emails...\n")
    dict_latest_email = read_emails(service)
    print(dict_latest_email)

    # 发送邮件
    sender_email = "fiveguysteam0@gmail.com"  # 你的 Gmail 地址
    receiver_email = "zhaowj1107@gmail.com"  # 收件人 Gmail 地址
    subject = "Test Email from Python_0315"
    body = "Hello! This is a test email sent using Gmail API and Python."

    send_email(service, sender_email, receiver_email, subject, body)
=======
def simple_draft(service, sender_email, to_email, subject, message_content):
    """
    Generate a simple draft WITHOUT calling RAG
    
    Args:
        service: The Gmail API service object
        sender_email: The sender's email address
        to_email: The recipient's email address
        subject: Email subject line
        message_content: Original content to be processed by LLM
    
    Returns:
        The created draft object
    """
    try:
        from local_model.ALLM_api import Chatbot
        
        # Define the prompt directly within the function
        # This prompt can be easily edited as needed
        prompt = """
        这是我从邮件里面提取出来的body内容，请返回一份纯净版可读的文本格式。返回内容控制在500个字以内
        """
        
        # Process the content using ALLM_api with the defined prompt
        chatbot = Chatbot()
        processed_content = chatbot.chat(message_content, prompt)
        
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
>>>>>>> cfd45ae4e16e4ec25c34c34e278b51834fdf2922:email_agent/gmail_api.py

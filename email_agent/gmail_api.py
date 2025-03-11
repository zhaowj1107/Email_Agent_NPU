import os
import base64
import pickle
import re
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API 需要的作用域（权限）
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def authenticate_gmail():
    """ 认证 Gmail API 并返回服务对象 """
    creds = None

    # 加载保存的 token
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
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
        with open("token.pickle", "wb") as token:
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

import os
import sys
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from gmail_auth import authenticate_gmail

# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
# sys.path.append(parent_dir)
# path file是全局生效, 所以即便在gmail.api中不设置绝对路径, 也能够找到src下的模块.

from toolkit.whatsapp_sender import whatsapp_sender

def read_inbox(service, max_results=1):
    """ 读取 Gmail 收件箱中的邮件（仅包含 INBOX 标签的邮件）
    
    Args:
        service: The Gmail API service object
        max_results: Maximum number of messages to retrieve (default: 1)
    
    Returns:
        dict: Dictionary containing email details (sender, subject, body, message_id)
    """
    try:
        # List messages with INBOX label only
        results = service.users().messages().list(
            userId="me", 
            maxResults=max_results,
            labelIds=["INBOX"]  # Only get messages with INBOX label
        ).execute()
        
        messages = results.get("messages", [])
        
        if not messages: # if no messages found in mailbox
            return {"sender": "", "subject": "", "body": "No messages found in inbox."}
        
        # Get the latest message
        msg = messages[0]
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        
        # Extract information
        headers = msg_data["payload"]["headers"]
        snippet = msg_data["snippet"]
        sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Unknown Sender")
        subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")
        
        # Extract email body(the body is not readable without decoding, we could use LLM to decode it)
        body = ""
        if "parts" in msg_data["payload"]:
            for part in msg_data["payload"]["parts"]:
                if part["mimeType"] == "text/plain":
                    if "data" in part["body"]:
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        break
        elif "body" in msg_data["payload"] and "data" in msg_data["payload"]["body"]:
            body = base64.urlsafe_b64decode(msg_data["payload"]["body"]["data"]).decode("utf-8")
        
        # Add message_id to the returned data
        email_info = {
            "sender": sender,
            "subject": subject,
            "snippet": snippet,
            "body": body,
            "message_id": msg["id"]
        }
        
        print("Latest inbox email retrieved successfully")
        return email_info
        
    except HttpError as error:
        print(f"An error occurred: {error}")
        return {"sender": "", "subject": "", "body": f"Error: {error}"}

if __name__ == "__main__":    
    # 读取邮件
    service = authenticate_gmail()
    print("Reading Emails...\n")
    dict_latest_email = read_inbox(service)
    print(dict_latest_email)
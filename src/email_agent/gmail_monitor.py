import time
import os
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pickle

import gmail_api as ga

"""
Gmail API 并没有直接提供实时监控邮件的功能，但你可以定期查询 Gmail 邮箱并获取新邮件。这意味着你可以设置一个定时任务（例如，每分钟查询一次 Gmail）检查是否有新邮件。

"""

# 获取最新邮件并返回邮件的字典信息
def get_latest_email(service):
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
    messages = results.get("messages", [])
    
    if not messages:
        print("No new messages.")
        return None

    # 获取最新的邮件 ID
    msg = service.users().messages().get(userId="me", id=messages[0]['id']).execute()
    headers = msg['payload']['headers']

    # 提取邮件信息
    email_data = {}
    for header in headers:
        if header["name"] == "From":
            email_data["From"] = header["value"]
        if header["name"] == "Subject":
            email_data["Subject"] = header["value"]
        if header["name"] == "Date":
            email_data["Date"] = header["value"]

    return email_data

# 定时查询新邮件
def monitor_email(last_email_id = None):
    service = ga.authenticate_gmail()
    # 存储上次检查时的最新邮件ID
    
    while True:
        print("Checking for new emails...")
        # 获取未读邮件
        results = service.users().messages().list(userId="me", labelIds=["INBOX"], q="is:unread").execute()
        messages = results.get("messages", [])
        
        if not messages:
            print("No unread messages.")
        else:
            # 检查最新邮件ID是否与上次不同
            newest_email_id = messages[0]['id']
            
            if last_email_id != newest_email_id:
                # 有新邮件
                email_data = get_latest_email(service)
                if email_data:
                    print("New email received:")
                    
                    
                    # 使用read_emails获取详细信息
                    email_details = ga.read_emails(service)
                    print(email_details)
                    
                    # 添加系统时间
                    email_details['system_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    # Construct the path to the credentials file
                    credentials_path = os.path.join(current_dir, "email_log.txt")
                    # 写入日志文件
                    with open(credentials_path, 'a', encoding='utf-8') as f:
                        f.write(f"--- New Email at {email_details['system_time']} ---\n")
                        for key, value in email_details.items():
                            f.write(f"{key}: {value}\n")
                        f.write("\n")
                    
                # 更新最新邮件ID
                last_email_id = newest_email_id
                return email_data, last_email_id
            else:
                print("No new emails since last check.")
        
        # 等待10秒后再检查一次
        time.sleep(10)

if __name__ == "__main__":
    monitor_email()

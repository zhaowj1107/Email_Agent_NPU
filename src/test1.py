"""
This script demonstrates how to insert working dir into sys.path, and then import packages and modules under the src folder.
path file是全局生效, 所以即便在gmail.api中不设置绝对路径, 也能够找到src下的模块。
"""

import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

import toolkit.gmail_api as tool

service = tool.authenticate_gmail()
sender_email = "zhaowj1107@gmail.com"  # 你的 Gmail 地址
receiver_email = "zhaowj1107@gmail.com"  # 收件人 Gmail 地址

# test simple_draft
print("\nTesting simple_draft function...")

# Define test parameters
test_subject = "Draft Test - Meeting Preparation"
test_content = """
Dear Team,

I would like to discuss our project progress at the upcoming meeting.
Please prepare updates on your assigned tasks.

The meeting is scheduled for Friday at 2 PM.

Best regards,
Project Manager
"""

# Create a draft email
draft_result = tool.simple_draft(
    service, 
    sender_email, 
    receiver_email, 
    test_subject, 
    test_content
)
if draft_result:
    print(draft_result)
    print(f"Draft created with ID: {draft_result['id']}")
else:
    print("Failed to create draft")
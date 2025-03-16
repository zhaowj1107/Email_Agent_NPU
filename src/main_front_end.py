import os
import sys
from pywebio.input import input
from pywebio.output import put_text, put_markdown, put_html, put_scrollable, use_scope, clear
from pywebio import start_server
import time

module_path = os.path.abspath("email_action")
sys.path.append(module_path)
import gmail_categorization as gc
import gmail_api as ga
import gmail_monitor as gm
from datetime import datetime
# import google_calendar.calendar_api as gc

def log_message(message, message_type="info"):
    """Add a message to the chat log with appropriate styling"""
    current_time = datetime.now().strftime("%H:%M:%S")
    
    if message_type == "email":
        background = "#e3f2fd"  # Light blue
    elif message_type == "system":
        background = "#f5f5f5"  # Light gray
    elif message_type == "success":
        background = "#e8f5e9"  # Light green
    elif message_type == "error":
        background = "#ffebee"  # Light red
    else:
        background = "#ffffff"  # White
    
    html = f"""
    <div style="margin-bottom: 10px; padding: 10px; border-radius: 5px; background-color: {background};">
        <div style="font-size: 0.8em; color: #666;">{current_time}</div>
        <div style="white-space: pre-wrap;">{message}</div>
    </div>
    """
    with use_scope('chat_log', clear=False):
        put_html(html)

def main():
    # Set up the UI
    put_markdown("# Email Monitoring System")
    put_markdown("### Automatically monitoring, categorizing, and responding to emails")
    
    # Create a scrollable area for chat messages
    with use_scope('chat_log'):
        pass  # Initialize an empty scope
    put_scrollable('chat_log', height=500, keep_bottom=True)
    
    log_message("Starting email monitoring service...", "system")
    
    service = ga.authenticate_gmail()
    sender_email = "fiveguysteam0@gmail.com"
    email_id = None
    
    log_message("Authentication successful. Waiting for new emails...", "system")
    
    while True:
        email, email_id = gm.monitor_email(email_id)
        
        # Format email details for display
        log_message("New email received", "system")
        email_details = f"From: {email['sender']}\nSubject: {email['subject']}\n\n{email['body']}"
        log_message(email_details, "email")
        
        custom_prompt = """
        Analyze this email and categorize it:
        A: Archive (low priority)
        B: Reply (medium priority)
        M: Meeting/Important (high priority)
        
        Return only a single letter.
        """
        log_message("Categorizing email...", "system")
        # category_custom = "B"
        category_custom = gc.categorize_email(email, custom_prompt)
        log_message(f"Category: {category_custom} - " + 
                   ("Archive (low priority)" if category_custom == "A" else
                    "Auto-Reply" if category_custom == "B" else
                    "Meeting/Important (high priority)"), "email")

        if category_custom == "A":
            # Test archive by query (recent emails from newsletters)
            ga.archive_emails(service, email_id)
            log_message("Email archived successfully", "success")
            
        elif category_custom == "B":
            # test simple_draft
            log_message("Preparing reply to email...", "system")
            reply_result = ga.reply_email(service, sender_email, email["sender"], email["subject"], email["body"])
            if reply_result:
                log_message(f"Reply sent with Message ID: {reply_result['id']}", "success")
            else:
                log_message("Failed to send reply", "error")
            log_message("Calendar checking...", "system")
            gc.check_calendar_need(email, category_custom)
            log_message("Calendar created", "success")
            
            # time.sleep(100)
    
        elif category_custom == "M":
            log_message("Creating draft for important email...", "system")
            draft_result = ga.simple_draft(service, sender_email, email["sender"], email["subject"], email["body"])
            if draft_result:
                log_message(f"Draft created with ID: {draft_result['id']}", "success")
            else:
                log_message("Failed to create draft", "error")
            log_message("Calendar checking...", "system")
            gc.check_calendar_need(email, category_custom)
            log_message("Calendar created", "success")

            # time.sleep(100)

        log_message("Waiting for new emails...", "system")
        

if __name__ == "__main__":
    start_server(main, port=8080, debug=True)
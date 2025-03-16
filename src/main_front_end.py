import os
import sys
from pywebio.input import input
from pywebio.output import put_text, put_markdown, put_html, put_scrollable, use_scope, clear, put_button, put_row
from pywebio import start_server
import time

module_path = os.path.abspath("email_action")
sys.path.append(module_path)
import gmail_categorization as gc
import gmail_api as ga
import gmail_monitor as gm
import daily_report as dr



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

def send_daily_report():
    """Generate and send a daily email report"""
    log_message("Generating daily report...", "system")
    try:
        # Replace this with your actual report generation code
        report_data = dr.daily_report()
        # Example: send_email_report(report_data)
        
        # Simulating report generation with a delay
        time.sleep(1)
        log_message("Daily report sent successfully!", "success")
        log_message(report_data, "email")
    except Exception as e:
        log_message(f"Error sending daily report: {str(e)}", "error")

def main():
    # Set up the UI
    put_row(
        [
            put_markdown("# Email Monitoring System"),
            None,  # This creates flexible space between the elements
            put_button("Send Daily Report", onclick=send_daily_report, color='primary', outline=True)
        ],
        size="auto 1fr auto"  # First and last columns auto-sized, middle takes remaining space
    )
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
                log_message(f"Reply sent with content:{reply_result['body']}", "success")
            else:
                log_message("Failed to send reply", "error")
            log_message("Calendar need checking...", "system")
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
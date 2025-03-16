import os
import sys
import flask as fl
import time

module_path = os.path.abspath("email_action")
sys.path.append(module_path)
import gmail_categorization as gc
import gmail_api as ga
import gmail_monitor as gm
from datetime import datetime
# import google_calendar.calendar_api as gc

def main():
    service = ga.authenticate_gmail()
    sender_email = "fiveguysteam0@gmail.com"
    email_id = None
    while True:
        email, email_id = gm.monitor_email(email_id)
        print(email)
        print("")
        # print(email_id)

        custom_prompt = """
        Analyze this email and categorize it:
        A: Archive (low priority)
        B: Reply (medium priority)
        M: Meeting/Important (high priority)
        
        Return only a single letter.
        """
        print("Categoring email...\n")
        # category_custom = "B"
        category_custom = gc.categorize_email(email, custom_prompt)
        print(f"Category with custom prompt: {category_custom}")

        
        if category_custom == "A":
            # Test archive by query (recent emails from newsletters)
            ga.archive_emails(service, email_id)
            print("")
            
        elif category_custom == "B":
            # test simple_draft
            print("\nReply email directly...")
            
            reply_result = ga.reply_email(service, sender_email, email["sender"], email["subject"], email["body"])
            gc.check_calendar_need(email, category_custom)
            if reply_result:
                # print(f"Reply sent with Message ID: {reply_result}")
                print(f"Reply sent: \n {reply_result['body']}")
            else:
                print("Failed to send reply")
    
        elif category_custom == "M":
            print("\nDraft email directly...")
            draft_result = ga.simple_draft(service, sender_email, email["sender"], email["subject"], email["body"])
            gc.check_calendar_need(email, category_custom)
            if draft_result:
                print(f"Draft created with ID: {draft_result['id']}")
            else:
                print("Failed to create draft")

        time.sleep(10)

if __name__ == "__main__":
    main()
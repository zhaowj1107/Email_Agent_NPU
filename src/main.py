import os
import sys
import flask as fl

module_path = os.path.abspath("email_agent")
sys.path.append(module_path)
import gmail_monitor as gm

module_path = os.path.abspath("email_action")
sys.path.append(module_path)
import gmail_categorization as gc
import gmail_api as ga
from datetime import datetime
# import google_calendar.calendar_api as gc

def main():
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
        category_custom = gc.categorize_email(email, custom_prompt)
        print(f"Category with custom prompt: {category_custom}")

if __name__ == "__main__":
    main()

        # if category_custom == "A":
        #     ga.archive_emails(email)
        # elif category_custom == "B":
        #     ga.reply_email(email)
        #     gc.if_calendar(email)
        # elif category_custom == "M":
        #     ga.simple_draft(email)
        #     gc.if_calendar(email)

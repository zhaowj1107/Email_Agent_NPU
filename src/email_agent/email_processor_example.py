#!/usr/bin/env python3
"""
Example script demonstrating how to use the email categorization and calendar processing functions.
"""

from gmail_api import authenticate_gmail, read_emails
from gmail_categorization import process_email

def main():
    """
    Main function to demonstrate email processing workflow.
    """
    # Step 1: Authenticate with Gmail
    print("Authenticating with Gmail...")
    gmail_service = authenticate_gmail()
    
    # Step 2: Read the latest email
    print("Reading the latest email...")
    email_data = read_emails(gmail_service, max_results=1)
    
    # Display email details
    print("\nLatest Email:")
    print(f"From: {email_data['sender']}")
    print(f"Subject: {email_data['subject']}")
    print(f"Body (first 100 chars): {email_data['body'][:100]}...")
    
    # Step 3: Process the email with custom prompts
    print("\nProcessing email...")
    
    # Custom categorization prompt
    categorization_prompt = """
    Analyze the following email content and categorize it into one of the four types:
    A: Low priority email that should be archived (e.g., advertisements, notifications, receipt confirmations)
    B: Email that requires a direct reply (e.g., simple questions, event confirmations)
    D: Email that needs a draft reply (e.g., complex questions, requests requiring thought)
    M: Important email that requires notification (e.g., urgent requests, important meetings)
    
    Return only a single letter (A, B, D, or M) without any other content.
    """
    
    # Custom calendar prompt
    calendar_prompt = """
    Analyze the following email content and determine if it should be added to the calendar:
    - If the email contains clear date, time, and event information, answer "YES"
    - If the email has been replied to with a rejection, answer "NO"
    - If the email does not contain date and time information, answer "NO"
    - If uncertain, answer "NO"
    
    If your answer is "YES", extract the following information from the email:
    - Date: in YYYY-MM-DD format
    - Start Time: in HH:MM format
    - End Time: in HH:MM format (if not specified, assume 1 hour after start time)
    - Event Title: brief description of the event (usually can be the email subject)
    - Event Description: detailed explanation (can include email content summary)
    - Location: event location (if mentioned in the email)
    
    Return this information in JSON format, like:
    {"Calendar_Needed": "YES", "Date": "2025-03-20", "Start_Time": "14:00", "End_Time": "15:30", "Event_Title": "Project Meeting", "Event_Description": "Discuss project progress", "Location": "Online"}
    or
    {"Calendar_Needed": "NO"}
    """
    
    # Process the email
    result = process_email(
        email_data,
        categorization_prompt=categorization_prompt,
        calendar_prompt=calendar_prompt
    )
    
    # Step 4: Display results
    print("\nProcessing Results:")
    print(f"Category: {result['email_processing']['category']}")
    print(f"Action Taken: {result['email_processing']['action_taken']}")
    
    if result['calendar_processing']['calendar_needed']:
        print("\nCalendar Event Created:")
        event_details = result['calendar_processing']['event_details']
        print(f"Title: {event_details['title']}")
        print(f"Date: {event_details['date']}")
        print(f"Time: {event_details['start_time']} - {event_details['end_time']}")
        print(f"Location: {event_details['location']}")
    else:
        print(f"\nNo calendar event needed: {result['calendar_processing']['reason']}")

if __name__ == "__main__":
    main() 
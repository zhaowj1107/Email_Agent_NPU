import os
import sys
import json 
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(parent_dir)

from ALLM_api import Chatbot
from google_calendar.calendar_api import authenticate_calendar, add_calendar_event

def categorize_email(email_data, custom_prompt=None):
    """
    Categorize the email into one of four categories:
    A: Archive the email
    B: Reply directly to the email
    D: Generate a draft reply
    M: Push a notification message
    
    Args:
        email_data: Get email data from read_emails() in gmail_api.py 
        custom_prompt: Optional custom prompt to use for categorization
    
    Returns:
        str: A single letter (A, B, D, or M) representing the category
    """
    try:
        from ALLM_api import Chatbot
        
        # Extract relevant email information for analysis
        sender = email_data.get('sender', '')
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        
        # Prepare email content for analysis
        email_content = f"From: {sender}\nSubject: {subject}\n\n{body}"
        
        # Default prompt for categorization
        default_prompt = """
        Analyze the following email content and categorize it into one of the four types.
        Follow these rules strictly and return only a single letter (A, B, D, or M).

        A: Archive - No response needed
        - Automated messages, newsletters, or robot-generated emails
        - Advertisements or promotional content
        - System notifications or alerts that don't require action
        - Confirmation emails (order confirmations, delivery notifications)
        - Spam or unsolicited emails
        Examples:
        - "Your order has been shipped"
        - "Weekly Newsletter"
        - "Limited time offer!"
        - "Your subscription is active"

        B: Reply Directly - Simple, quick response
        - Yes/No questions
        - Meeting attendance confirmations
        - Simple schedule coordination
        - Basic information requests
        - Quick acknowledgments needed
        Examples:
        - "Can you attend the meeting tomorrow?"
        - "Did you receive my document?"
        - "Are you available next Tuesday?"
        - "Please confirm receipt"

        D: Draft Reply - Needs thoughtful response
        - Emails from important contacts (professors, supervisors, landlords)
        - Complex questions or requests
        - Project-related discussions
        - Academic or professional matters
        - Requires detailed information or explanation
        - Any email requiring careful wording
        Examples:
        - Email from professor about research
        - Project feedback or discussion
        - Housing-related inquiries
        - Academic collaboration requests

        M: Important/Emergency - Immediate attention
        - Urgent deadlines or time-sensitive matters
        - Emergency situations
        - Critical issues requiring immediate response
        - Security alerts or warnings
        - Important updates from key stakeholders
        Examples:
        - "Urgent: Server down"
        - "Emergency meeting in 1 hour"
        - "Immediate action required"
        - "Security breach detected"

        Additional Rules:
        1. If sender is a known important contact (professor, supervisor, landlord), default to D unless urgent (then M)
        2. If subject contains words like "urgent", "emergency", "immediate", categorize as M
        3. If email is clearly automated or promotional, always choose A
        4. If response can be given in one sentence, choose B
        5. When in doubt between B and D, choose D for safer handling

        Return ONLY a single letter (A, B, D, or M) without any explanation.
        """
        
        # Use custom prompt if provided, otherwise use default
        prompt = custom_prompt if custom_prompt else default_prompt
        
        # Create a Chatbot instance and call chat to categorize the email
        chatbot = Chatbot()
        category = chatbot.chat(email_content, prompt).strip()
        
        # Ensure we only return a single valid letter
        if category and len(category) >= 1:
            category = category[0].upper()
            if category in ['A', 'B', 'D', 'M']:
                return category
        
        # Default to 'A' (archive) if invalid response
        return 'A'
        
    except Exception as e:
        print(f"Error categorizing email: {e}")
        # Default to 'A' (archive) on error
        return 'A'


def check_calendar_need(email_data, category):
    """
    Check if email needs calendar event and create it if needed.
    
    Args:
        email_data: Email details (sender, subject, body)
        category: Email category (A, B, D, M)
    
    Returns:
        dict: Calendar event details or reason why not created
    """
    try:
        if category == 'A':
            return {"calendar_needed": False, "reason": "Category A emails are not processed for calendar events"}
            
        sender = email_data.get('sender', '')
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        email_content = f"From: {sender}\nSubject: {subject}\n\n{body}"
        
        default_prompt = """
        Analyze this email and determine if it needs a calendar event.
        You must return a valid JSON format exactly as specified below.
        Do not include any other text or explanation.
        
        Required Information:
        - Specific date (YYYY-MM-DD)
        - Start time (HH:MM)
        - End time (HH:MM)
        - Event title
        - Description
        - Location (optional)
        
        2. Required Information:
           - Must have specific date (YYYY-MM-DD format)
           - Must have specific start time (HH:MM format)
           - Must have specific or calculable end time (HH:MM format)
           - Must have clear purpose or agenda
        
        3. Rejection Criteria:
           - Reject if it's a cancellation notice
           - Reject if it's a past event
           - Reject if it's just an FYI or optional event
           - Reject if critical details are missing
        
        If calendar event is needed, return ONLY this JSON:
        {
            "Calendar_Needed": "YES",
            "Date": "YYYY-MM-DD",
            "Start_Time": "HH:MM",
            "End_Time": "HH:MM",
            "Event_Title": "title",
            "Event_Description": "description",
            "Location": "location"
        }
        
        If not needed, return EXACTLY:
        {
            "Calendar_Needed": "NO",
            "Reason": "why"
        }
        """
        
        from ALLM_api import Chatbot
        chatbot = Chatbot()
        response = chatbot.chat(email_content, default_prompt)
        
        if not response:
            return {"calendar_needed": False, "reason": "No response from chatbot"}
        
        # Clean up response and print for debugging
        response = response.strip()
        print("\nDebug - Chatbot response:")
        print(response)
        
        try:
            import json
            calendar_data = json.loads(response)
            
            # Validate JSON structure
            if not isinstance(calendar_data, dict):
                return {"calendar_needed": False, "reason": "Invalid JSON structure - not a dictionary"}
            
            if "Calendar_Needed" not in calendar_data:
                return {"calendar_needed": False, "reason": "Invalid JSON structure - missing Calendar_Needed field"}
            
            if calendar_data.get("Calendar_Needed") == "YES":
                required_fields = ["Date", "Start_Time", "End_Time", "Event_Title"]
                missing_fields = [field for field in required_fields if field not in calendar_data]
                
                if missing_fields:
                    return {"calendar_needed": False, "reason": f"Missing required fields: {', '.join(missing_fields)}"}
                
                calendar_service = authenticate_calendar()
                event = add_calendar_event(
                    calendar_service,
                    calendar_data["Date"],
                    calendar_data["Start_Time"],
                    calendar_data["End_Time"],
                    calendar_data["Event_Title"],
                    calendar_data.get("Event_Description", ""),
                    calendar_data.get("Location", ""),
                    [sender]
                )
                
                if event:
                    return {
                        "calendar_needed": True,
                        "event_details": {
                            "date": calendar_data["Date"],
                            "start_time": calendar_data["Start_Time"],
                            "end_time": calendar_data["End_Time"],
                            "title": calendar_data["Event_Title"]
                        }
                    }
                    
            return {"calendar_needed": False, "reason": calendar_data.get("Reason", "Not needed")}
                
        except json.JSONDecodeError as e:
            print(f"\nDebug - JSON Error details:")
            print(f"Error message: {str(e)}")
            print(f"Error position: character {e.pos}")
            print(f"Line with error: {e.doc[max(0, e.pos-20):min(len(e.doc), e.pos+20)]}")
            return {"calendar_needed": False, "reason": f"Invalid JSON format: {str(e)}"}
            
    except Exception as e:
        print(f"Error checking calendar need: {e}")
        return {"calendar_needed": False, "reason": str(e)}


if __name__ == "__main__":
    # Test the categorize_email function
    print("Testing categorize_email function...")
    
    # Sample email data for testing
    test_email = {
        'sender': 'test@example.com',
        'subject': 'Important Meeting Request',
        'body': '''
        Hello Team,
        
        I'd like to schedule a meeting to discuss our Q2 targets and strategy.
        Could we meet next Tuesday at 2pm?
        
        Please let me know if this works for everyone.
        
        Best regards,
        John Doe
        '''
    }
    
    # Test with default prompt
    category = categorize_email(test_email)
    print(f"Category with default prompt: {category}")
    
    # Test with custom prompt
    custom_prompt = """
    Analyze this email and categorize it:
    A: Archive (low priority)
    B: Reply (medium priority)
    D: Draft (needs thoughtful response)
    M: Meeting/Important (high priority)
    
    Return only a single letter.
    """
    
    category_custom = categorize_email(test_email, custom_prompt)
    print(f"Category with custom prompt: {category_custom}")
    
    # Test with different email content
    test_email2 = {
        'sender': 'newsletter@example.com',
        'subject': 'Weekly Newsletter: Industry Updates',
        'body': '''
        This week in tech:
        - New product launches
        - Industry trends
        - Upcoming webinars
        
        Click here to read more.
        '''
    }
    
    category2 = categorize_email(test_email2)
    print(f"Category for newsletter email: {category2}")


    # Test check_calendar_need function
    print("\nTesting check_calendar_need function...")
    
    # Test email with clear calendar event details
    test_email = {
        'sender': 'test@example.com',
        'subject': 'Team Meeting Next Week',
        'body': '''
        Hi team,
        
        Let's have our weekly team meeting next Tuesday (2025-03-15) from 14:00 to 15:00.
        We will discuss the Q1 project progress.
        
        Location: Conference Room A
        
        Best regards,
        Team Lead
        '''
    }
    
    # Test with category B (should create calendar)
    result = check_calendar_need(test_email, 'B')
    
    if result.get('calendar_needed'):
        print("✓ Calendar event created successfully!")
        print("Event details:", result['event_details'])
    else:
        print("✗ Failed to create calendar event")
        print("Reason:", result.get('reason'))
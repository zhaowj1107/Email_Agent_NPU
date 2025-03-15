import os
import sys
from datetime import datetime
import re

# Add parent directory to system path to access other modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import required modules
from email_agent.gmail_api import authenticate_gmail, archive_emails, simple_draft, draft_rag
from google_calendar.calendar_api import authenticate_calendar, add_calendar_event

# Import deepseek LLM
try:
    from local_model.ds_api import deepseek
except ImportError:
    print("Warning: Could not import deepseek from local_model.ds_api")
    # Define a fallback function if deepseek is not available
    def deepseek(text, prompt=None):
        print("Using fallback LLM function (no actual processing)")
        return "A"  # Default categorization

def categorize_email(email_data, custom_prompt=None):
    """
    Categorize an email using an LLM and perform actions based on the category.
    
    Categories:
    A: Archive the email
    C: Add events to calendar
    D: Generate a reply draft
    M: Push notification
    
    Args:
        email_data: Dictionary containing email information (sender, subject, body)
        custom_prompt: Optional custom prompt for the LLM
        
    Returns:
        Dictionary with categorization results and actions taken
    """
    # Default categorization prompt if none provided
    default_prompt = """
    Based on the email content below, categorize it into one of the following categories:
    A: Archive (low priority, newsletters, promotional content)
    C: Calendar (contains meeting invites, events, or deadlines)
    D: Draft Reply (requires a response)
    M: Message/Notification (important information that should be pushed as notification)
    
    Only respond with a single letter (A, C, D, or M) representing the best category.
    
    Email Subject: {subject}
    
    Email Body:
    {body}
    """
    
    # Use custom prompt if provided
    prompt = custom_prompt if custom_prompt else default_prompt
    
    # Format the prompt with email data
    formatted_prompt = prompt.format(
        subject=email_data.get('subject', ''),
        body=email_data.get('body', '')
    )
    
    # Call LLM to categorize the email
    try:
        category = deepseek(formatted_prompt).strip().upper()
        # Ensure the response is just one of the valid categories
        if category not in ['A', 'C', 'D', 'M']:
            print(f"Invalid category from LLM: {category}, defaulting to 'A'")
            category = 'A'
    except Exception as e:
        print(f"Error calling LLM: {e}")
        category = 'A'  # Default to Archive on error
    
    result = {
        'category': category,
        'action_taken': None,
        'details': {}
    }
    
    # Perform actions based on category
    if category == 'A':
        # Archive the email
        try:
            gmail_service = authenticate_gmail()
            # Assuming email_data contains message_id or we can build a query from sender/subject
            query = f"from:{email_data.get('sender', '')} subject:{email_data.get('subject', '')}"
            archive_emails(gmail_service, query=query)
            result['action_taken'] = 'archived'
        except Exception as e:
            print(f"Error archiving email: {e}")
            result['action_taken'] = 'failed_to_archive'
            result['details']['error'] = str(e)
    
    elif category == 'C':
        # Add to calendar
        try:
            # Extract date, time, and event details from email body
            calendar_info = extract_calendar_info(email_data.get('body', ''))
            
            if calendar_info:
                calendar_service = authenticate_calendar()
                event = add_calendar_event(
                    calendar_service,
                    calendar_info['date'],
                    calendar_info['start_time'],
                    calendar_info['end_time'],
                    calendar_info['summary'],
                    calendar_info.get('description', ''),
                    calendar_info.get('location', '')
                )
                result['action_taken'] = 'added_to_calendar'
                result['details']['event'] = calendar_info
            else:
                result['action_taken'] = 'failed_to_extract_calendar_info'
        except Exception as e:
            print(f"Error adding to calendar: {e}")
            result['action_taken'] = 'failed_to_add_to_calendar'
            result['details']['error'] = str(e)
    
    elif category == 'D':
        # Generate reply draft
        try:
            gmail_service = authenticate_gmail()
            sender_email = email_data.get('receiver', '')  # The email user is using to reply
            to_email = email_data.get('sender', '')  # Original sender becomes recipient
            subject = email_data.get('subject', '')
            
            # Use RAG-enhanced draft or simple draft based on availability
            try:
                draft = draft_rag(gmail_service, sender_email, to_email, subject, email_data.get('body', ''))
            except:
                draft = simple_draft(gmail_service, sender_email, to_email, subject, email_data.get('body', ''))
                
            result['action_taken'] = 'draft_created'
            result['details']['draft_id'] = draft.get('id') if draft else None
        except Exception as e:
            print(f"Error creating draft: {e}")
            result['action_taken'] = 'failed_to_create_draft'
            result['details']['error'] = str(e)
    
    elif category == 'M':
        # Push notification message
        try:
            # This would connect to a notification service
            notification_text = f"Important email from {email_data.get('sender', 'Unknown')}: {email_data.get('subject', 'No Subject')}"
            
            # Placeholder for notification service integration
            # Ideally this would call a notification service API
            print(f"NOTIFICATION: {notification_text}")
            result['action_taken'] = 'notification_pushed'
            result['details']['notification_text'] = notification_text
        except Exception as e:
            print(f"Error pushing notification: {e}")
            result['action_taken'] = 'failed_to_push_notification'
            result['details']['error'] = str(e)
    
    return result

def extract_calendar_info(email_body):
    """
    Extract calendar event information from email body.
    This is a basic implementation and might need to be enhanced with more
    sophisticated NLP for production use.
    
    Returns a dictionary with date, start_time, end_time, summary, description, location
    or None if extraction fails
    """
    try:
        # Use regex patterns to extract date, time, and event details
        # This is a simplified version - a real implementation would use more robust NLP
        
        # Example patterns (very basic)
        date_pattern = r'(\d{4}-\d{1,2}-\d{1,2})'
        time_pattern = r'(\d{1,2}:\d{2})'
        
        # Try to find date
        date_match = re.search(date_pattern, email_body)
        if not date_match:
            # If no ISO format date found, return None
            return None
            
        # Try to find times
        time_matches = re.findall(time_pattern, email_body)
        if len(time_matches) < 2:
            # Need at least start and end time
            return None
            
        # Extract potential event title - first line or subject-like text
        lines = email_body.split('\n')
        summary = next((line for line in lines if line.strip()), "Event from Email")
        
        # Create calendar info
        calendar_info = {
            'date': date_match.group(1),
            'start_time': time_matches[0],
            'end_time': time_matches[1],
            'summary': summary[:50],  # Limit length
            'description': email_body[:500],  # Use part of email as description
            'location': ''  # Default empty location
        }
        
        return calendar_info
        
    except Exception as e:
        print(f"Error extracting calendar info: {e}")
        return None
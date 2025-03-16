from local_model.ALLM_api import Chatbot
from google_calendar.calendar_api import authenticate_calendar, add_calendar_event

def categorize_email(email_data, custom_prompt=None):
    """
    Categorize the email into one of four categories and handle it accordingly:
    A: Archive the email
    B: Reply directly to the email
    D: Generate a draft reply
    M: Push a notification message
    
    Args:
        email_data: Dictionary containing email details (sender, subject, body)
        custom_prompt: Optional custom prompt to use for categorization
    
    Returns:
        dict: Result of the categorization and action taken
    """
    # Default prompt for categorization
    default_prompt = """
    Analyze the following email content and categorize it into one of the four types:
    A: Low priority email that should be archived
    B: Email that requires a direct reply
    D: Email that needs a draft reply
    M: Important email that requires notification
    
    Return only a single letter (A, B, D, or M) without any other content.
    """
    
    # Use custom prompt if provided, otherwise use default
    prompt = custom_prompt if custom_prompt else default_prompt
    
    # Get email details
    sender = email_data.get("sender", "")
    subject = email_data.get("subject", "")
    body = email_data.get("body", "")
    
    # Create the input for the LLM
    llm_input = f"From: {sender}\nSubject: {subject}\n\n{body}"
    
    # Call the LLM to categorize the email using Chatbot
    chatbot = Chatbot()
    category = chatbot.chat(llm_input, prompt).strip().upper()
    
    # Validate the category
    if category not in ["A", "B", "D", "M"]:
        print(f"Invalid category: {category}. Defaulting to D.")
        category = "D"
    
    # Process the email based on the category
    result = {
        "category": category,
        "sender": sender,
        "subject": subject,
        "action_taken": None
    }
    
    from email_agent.gmail_api import archive_emails, send_email, simple_draft, draft_rag
    
    # Get the Gmail service
    from email_agent.gmail_api import authenticate_gmail
    gmail_service = authenticate_gmail()
    
    # Handle the email based on its category
    if category == "A":
        # Archive the email
        # Assuming email_data contains a message_id
        if "message_id" in email_data:
            archive_emails(gmail_service, message_id=email_data["message_id"])
            result["action_taken"] = "Email archived"
        else:
            # Use query based on subject if message_id not available
            query = f"subject:{subject}"
            archive_emails(gmail_service, query=query)
            result["action_taken"] = f"Emails matching '{query}' archived"
    
    elif category == "B":
        # Generate reply content
        reply_prompt = """
        Generate a short, professional reply directly responding to this email.
        The reply should be concise and not exceed 100 words.
        """
        
        # Create a new Chatbot for reply generation
        reply_chatbot = Chatbot()
        reply_content = reply_chatbot.chat(f"From: {sender}\nSubject: {subject}\n\n{body}", reply_prompt)
        
        # Send the reply
        send_email(gmail_service, "me", sender, f"Re: {subject}", reply_content)
        result["action_taken"] = "Direct reply sent"
        result["reply_content"] = reply_content
    
    elif category == "D":
        # Create a draft reply
        # Use simple_draft (now updated to use Chatbot)
        draft = simple_draft(gmail_service, "me", sender, f"Re: {subject}", body)
        if draft:
            result["action_taken"] = "Draft reply created"
            result["draft_id"] = draft["id"]
    
    elif category == "M":
        # Create a draft and mark as important (now updated to use Chatbot)
        draft = draft_rag(gmail_service, "me", sender, f"IMPORTANT: {subject}", body)
        result["action_taken"] = "Draft created and marked as important"
        if draft:
            result["draft_id"] = draft["id"]
    
    return result

def check_calendar_need(email_result, custom_prompt=None):
    """
    Determine if the email should be added to the calendar based on the previous action.
    
    Args:
        email_result: Result from categorize_email function
        custom_prompt: Optional custom prompt for the LLM
    
    Returns:
        dict: Result including calendar event details if created
    """
    # Default prompt for calendar determination
    default_prompt = """
    Analyze the following email content and determine if it should be added to the calendar:
    - If the email contains clear date, time, and event information, answer "YES"
    - If the email has been replied to with a rejection, answer "NO"
    - If the email does not contain date and time information, answer "NO"
    - If uncertain, answer "NO"
    
    If your answer is "YES", extract the following information from the email:
    - Date: in YYYY-MM-DD format
    - Start Time: in HH:MM format
    - End Time: in HH:MM format
    - Event Title: brief description of the event
    - Event Description: detailed explanation
    - Location: event location
    
    Return this information in JSON format, like:
    {"Calendar_Needed": "YES", "Date": "2025-03-20", "Start_Time": "14:00", "End_Time": "15:30", "Event_Title": "Project Meeting", "Event_Description": "Discuss project progress", "Location": "Online"}
    or
    {"Calendar_Needed": "NO"}
    """
    
    # Use custom prompt if provided, otherwise use default
    prompt = custom_prompt if custom_prompt else default_prompt
    
    # Check if we should even consider adding to calendar
    # If email was archived or directly replied with a rejection, don't add to calendar
    category = email_result.get("category")
    if category == "A":
        return {"calendar_needed": False, "reason": "Email was archived"}
    
    if category == "B" and "reply_content" in email_result:
        # Check if the reply is a rejection
        reply = email_result["reply_content"].lower()
        rejection_words = ["reject", "decline", "cannot attend", "unable to attend"]
        if any(word in reply for word in rejection_words):
            return {"calendar_needed": False, "reason": "Email was rejected"}
    
    # Prepare input for the LLM
    subject = email_result.get("subject", "")
    sender = email_result.get("sender", "")
    
    # We need the original email body for context
    body = email_result.get("body", "")
    if not body and "original_email" in email_result:
        body = email_result["original_email"].get("body", "")
    
    llm_input = f"From: {sender}\nSubject: {subject}\n\n{body}"
    
    # Call the LLM to determine if calendar event is needed using Chatbot
    calendar_chatbot = Chatbot()
    response = calendar_chatbot.chat(llm_input, prompt)
    
    try:
        # Try to parse as JSON
        import json
        import re
        
        # Extract JSON part from the response
        json_match = re.search(r'({.*})', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            calendar_data = json.loads(json_str)
        else:
            # Fallback to simple YES/NO detection
            calendar_needed = "YES" in response.upper()
            calendar_data = {"Calendar_Needed": "YES" if calendar_needed else "NO"}
        
        # Check if calendar event is needed
        if calendar_data.get("Calendar_Needed") == "YES":
            # Extract event details
            date = calendar_data.get("Date", "")
            start_time = calendar_data.get("Start_Time", "")
            end_time = calendar_data.get("End_Time", "")
            title = calendar_data.get("Event_Title", subject)
            description = calendar_data.get("Event_Description", "")
            location = calendar_data.get("Location", "")
            
            # Validate the date and time formats
            if not (date and start_time and end_time):
                return {"calendar_needed": False, "reason": "Incomplete event details"}
            
            # Add event to calendar
            calendar_service = authenticate_calendar()
            event = add_calendar_event(
                calendar_service,
                date,
                start_time,
                end_time,
                title,
                description,
                location
            )
            
            # Return the result
            return {
                "calendar_needed": True,
                "calendar_event": event,
                "event_details": {
                    "date": date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "title": title,
                    "description": description,
                    "location": location
                }
            }
        else:
            return {"calendar_needed": False, "reason": "LLM determined no calendar event needed"}
            
    except Exception as e:
        print(f"Error processing calendar need: {e}")
        return {"calendar_needed": False, "reason": f"Error: {str(e)}"}

def process_email(email_data, categorization_prompt=None, calendar_prompt=None):
    """
    Complete process for handling an email: categorize it, take action, and check if calendar event is needed.
    
    Args:
        email_data: Dictionary containing email details (sender, subject, body)
        categorization_prompt: Optional custom prompt for categorization
        calendar_prompt: Optional custom prompt for calendar determination
    
    Returns:
        dict: Complete result of processing
    """
    # Step 1: Categorize the email and take action
    email_result = categorize_email(email_data, categorization_prompt)
    
    # Add the original email body to the result for reference in the calendar check
    email_result["original_email"] = email_data
    
    # Step 2: Check if a calendar event is needed
    calendar_result = check_calendar_need(email_result, calendar_prompt)
    
    # Combine results
    result = {
        "email_processing": email_result,
        "calendar_processing": calendar_result
    }
    
    return result

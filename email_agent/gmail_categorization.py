from local_model.ds_api import deepseek
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
    请分析以下邮件内容并将其分类为以下四种类型之一:
    A: 需要归档的低优先级邮件
    B: 需要直接回复的邮件
    D: 需要生成回复草稿的邮件
    M: 需要发送通知提醒的重要邮件
    
    请仅返回一个字母 (A、B、D 或 M)，不要有其他内容。
    """
    
    # Use custom prompt if provided, otherwise use default
    prompt = custom_prompt if custom_prompt else default_prompt
    
    # Get email details
    sender = email_data.get("sender", "")
    subject = email_data.get("subject", "")
    body = email_data.get("body", "")
    
    # Create the input for the LLM
    llm_input = f"发件人: {sender}\n主题: {subject}\n\n{body}\n\n{prompt}"
    
    # Call the LLM to categorize the email
    category = deepseek(llm_input).strip().upper()
    
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
        请生成一个简短、专业的回复，直接回应这封邮件的内容。
        回复应该简洁明了，不超过100字。
        """
        reply_input = f"发件人: {sender}\n主题: {subject}\n\n{body}\n\n{reply_prompt}"
        reply_content = deepseek(reply_input)
        
        # Send the reply
        send_email(gmail_service, "me", sender, f"Re: {subject}", reply_content)
        result["action_taken"] = "Direct reply sent"
        result["reply_content"] = reply_content
    
    elif category == "D":
        # Create a draft reply
        # You could use either simple_draft or draft_rag
        draft = simple_draft(gmail_service, "me", sender, f"Re: {subject}", body)
        if draft:
            result["action_taken"] = "Draft reply created"
            result["draft_id"] = draft["id"]
    
    elif category == "M":
        # Here you would integrate with a notification service
        # For now, we'll just create a draft and note it needs attention
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
    请分析以下邮件内容，判断是否需要将其添加到日历中:
    - 如果邮件中包含明确的日期、时间和事件信息，回答 "YES"
    - 如果邮件已经被拒绝回复，回答 "NO"
    - 如果邮件中没有包含日期和时间信息，回答 "NO"
    - 如果无法确定，回答 "NO"
    
    请仅返回 "YES" 或 "NO"，不要有其他内容。
    如果回答是 "YES"，请同时从邮件内容中提取以下信息:
    - 日期: YYYY-MM-DD格式
    - 开始时间: HH:MM格式
    - 结束时间: HH:MM格式
    - 事件标题: 简短描述这个事件
    - 事件描述: 详细说明
    - 地点: 事件地点
    
    以JSON格式返回这些信息，如:
    {"需要添加": "YES", "日期": "2025-03-20", "开始时间": "14:00", "结束时间": "15:30", "事件标题": "项目会议", "事件描述": "讨论项目进度", "地点": "线上"}
    或者
    {"需要添加": "NO"}
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
        rejection_words = ["reject", "decline", "cannot attend", "unable to attend", "拒绝", "不能参加"]
        if any(word in reply for word in rejection_words):
            return {"calendar_needed": False, "reason": "Email was rejected"}
    
    # Prepare input for the LLM
    subject = email_result.get("subject", "")
    sender = email_result.get("sender", "")
    
    # We need the original email body for context
    # This assumes we have access to email_data from categorize_email
    # If not available, this would need to be modified
    body = email_result.get("body", "")
    if not body and "original_email" in email_result:
        body = email_result["original_email"].get("body", "")
    
    llm_input = f"发件人: {sender}\n主题: {subject}\n\n{body}\n\n{prompt}"
    
    # Call the LLM to determine if calendar event is needed
    response = deepseek(llm_input)
    
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
            calendar_data = {"需要添加": "YES" if calendar_needed else "NO"}
        
        # Check if calendar event is needed
        if calendar_data.get("需要添加") == "YES":
            # Extract event details
            date = calendar_data.get("日期", "")
            start_time = calendar_data.get("开始时间", "")
            end_time = calendar_data.get("结束时间", "")
            title = calendar_data.get("事件标题", subject)
            description = calendar_data.get("事件描述", "")
            location = calendar_data.get("地点", "")
            
            # Validate the date and time formats
            # Simple validation, can be improved
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

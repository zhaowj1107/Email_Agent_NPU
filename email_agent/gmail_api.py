def draft_rag(service, sender_email, to_email, subject, message_content):
    """
    根据邮件内容生成一组关键词如[school, deadline, client]
    向RAG求这些关键词的返回值形成字典,如{school：NEU, Deadline: 2025-03-15, client: Zhaowj}   
    根据字典信息生成邮件的草稿
    
    Args:
        service: The Gmail API service object
        sender_email: The sender's email address
        to_email: The recipient's email address
        subject: Email subject line
        message_content: Original email content
    
    Returns:
        The created draft object
    """
    try:
        from local_model.ALLM_api import Chatbot
        
        # 步骤1: 使用LLM提取关键词
        keyword_extraction_prompt = """
        请从以下邮件内容中提取关键词，以逗号分隔的列表形式返回。
        例如：school, deadline, client, project
        只返回关键词列表，不要有其他内容。
        """
        
        # 创建Chatbot实例并调用提取关键词
        keyword_chatbot = Chatbot()
        keywords_text = keyword_chatbot.chat(message_content, keyword_extraction_prompt)
        
        # 处理关键词文本，转换为列表
        keywords = [keyword.strip() for keyword in keywords_text.split(',')]
        print(f"Extracted keywords: {keywords}")
        
        # 步骤2: 预留RAG接口调用
        # 这里应该是调用外部RAG系统的代码
        # 示例代码，实际实现需要替换为真实的RAG调用
        def call_rag_system(keywords):
            """
            调用RAG系统获取关键词的相关信息
            实际使用时需要替换为真实的RAG系统调用
            """
            # 模拟RAG返回的字典
            rag_results = {
                # 这里将来会被真实的RAG系统返回值替换
                keyword: f"Sample value for {keyword}" for keyword in keywords
            }
            return rag_results
        
        # 获取RAG结果
        rag_info = call_rag_system(keywords)
        print(f"RAG information: {rag_info}")
        
        # 步骤3: 赋值prompt变量
        prompt = f"""
        请根据以下信息生成一封专业的邮件回复草稿:
        
        原始邮件主题: {subject}
        
        关键信息:
        {', '.join([f'{k}: {v}' for k, v in rag_info.items()])}
        
        要求:
        1. 使用正式、专业的语言
        2. 确保回复针对原始邮件的内容
        3. 包含所有必要的关键信息
        4. 保持简洁明了，不超过300字
        """
        
        # 步骤4: 调用LLM生成邮件草稿
        draft_chatbot = Chatbot()
        draft_content = draft_chatbot.chat(message_content, prompt)
        
        # 创建MIME消息
        message = MIMEText(draft_content)
        message["to"] = to_email
        message["from"] = sender_email
        message["subject"] = f"Re: {subject}"
        
        # 编码消息为base64url格式
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # 创建草稿消息
        draft = {
            'message': {
                'raw': encoded_message
            }
        }
        
        # 调用Gmail API创建草稿
        created_draft = service.users().drafts().create(userId="me", body=draft).execute()
        
        print(f"Draft created successfully with ID: {created_draft['id']}")
        return created_draft
    
    except ImportError:
        print("Error: Could not import Chatbot from local_model.ALLM_api")
        return None
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def simple_draft(service, sender_email, to_email, subject, message_content):
    """
    Generate a simple draft WITHOUT calling RAG
    
    Args:
        service: The Gmail API service object
        sender_email: The sender's email address
        to_email: The recipient's email address
        subject: Email subject line
        message_content: Original content to be processed by LLM
    
    Returns:
        The created draft object
    """
    try:
        from local_model.ALLM_api import Chatbot
        
        # Define the prompt directly within the function
        # This prompt can be easily edited as needed
        prompt = """
        这是我从邮件里面提取出来的body内容，请返回一份纯净版可读的文本格式。返回内容控制在500个字以内
        """
        
        # Process the content using ALLM_api with the defined prompt
        chatbot = Chatbot()
        processed_content = chatbot.chat(message_content, prompt)
        
        # Create a MIMEText message
        message = MIMEText(processed_content)
        message["to"] = to_email
        message["from"] = sender_email
        message["subject"] = subject
        
        # Encode the message to base64url format
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Create the draft message
        draft = {
            'message': {
                'raw': encoded_message
            }
        }
        
        # Call the Gmail API to create the draft
        created_draft = service.users().drafts().create(userId="me", body=draft).execute()
        
        print(f"Draft created successfully with ID: {created_draft['id']}")
        return created_draft
    
    except ImportError:
        print("Error: Could not import Chatbot from local_model.ALLM_api")
        return None
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None 
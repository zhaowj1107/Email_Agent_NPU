import time
import logging
from .core import EmailAgent
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Initialize email agent
    agent = EmailAgent(
        email_address=settings.email_address,
        password=settings.email_password,
        imap_server=settings.imap_server
    )
    
    if not agent.connect():
        logging.error("Failed to connect to email server")
        return
        
    try:
        while True:
            # Fetch and process new emails
            emails = agent.fetch_emails()
            for email in emails:
                process_email(email)
                
            # Sleep before next check
            time.sleep(60)
            
    except KeyboardInterrupt:
        logging.info("Shutting down email agent...")
    finally:
        agent.close()

def process_email(email: dict):
    """Process individual email"""
    logging.info(f"Processing email from {email['from']} - {email['subject']}")
    # TODO: Implement email processing logic
    # - Categorize email
    # - Generate response
    # - Handle calendar events
    # - Send notifications
    
if __name__ == "__main__":
    main()

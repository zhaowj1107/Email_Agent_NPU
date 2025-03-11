import imaplib
import email
from email import policy
from typing import List, Dict
from .config import settings

class EmailAgent:
    def __init__(self, email_address: str, password: str, imap_server: str):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.mail = None

    def connect(self) -> bool:
        """Connect to IMAP server"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_address, self.password)
            self.mail.select('inbox')
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def fetch_emails(self) -> List[Dict]:
        """Fetch new emails from server"""
        if not self.mail:
            return []

        try:
            status, messages = self.mail.search(None, 'UNSEEN')
            if status != 'OK':
                return []

            emails = []
            for msg_id in messages[0].split():
                status, msg_data = self.mail.fetch(msg_id, '(RFC822)')
                if status == 'OK':
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email, policy=policy.default)
                    emails.append(self._parse_email(email_message))
            return emails
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def _parse_email(self, email_message) -> Dict:
        """Parse email message into structured data"""
        return {
            'from': email_message['from'],
            'to': email_message['to'],
            'subject': email_message['subject'],
            'date': email_message['date'],
            'body': self._get_email_body(email_message),
            'attachments': self._get_attachments(email_message)
        }

    def _get_email_body(self, email_message) -> str:
        """Extract email body text"""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == 'text/plain':
                    return part.get_payload(decode=True).decode()
        else:
            return email_message.get_payload(decode=True).decode()
        return ""

    def _get_attachments(self, email_message) -> List[Dict]:
        """Extract email attachments"""
        attachments = []
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    attachments.append({
                        'filename': part.get_filename(),
                        'content_type': part.get_content_type(),
                        'payload': part.get_payload(decode=True)
                    })
        return attachments

    def close(self):
        """Close connection to email server"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
            except Exception as e:
                print(f"Error closing connection: {e}")

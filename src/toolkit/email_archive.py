from googleapiclient.errors import HttpError
from gmail_auth import authenticate_gmail


def archive_emails(service, message_id=None, query=None):
    """
    R
    emoves the INBOX label from the email(s) to archive them.
    This function can be used to archive emails based on a specific ID or a search query.
    Args:
        service: The Gmail API service object.
        message_id: The ID of the specific email to archive. If provided, query is ignored.
        query: The search query to find emails to archive. Only used if message_id is None.
               Example: "from:someone@example.com subject:Important"
    """
    try:
        messages = []
        
        if message_id:
            # Archive a specific email by ID
            messages = [{"id": message_id}]
            print(f"Archiving email with ID: {message_id}")
        elif query:
            # List messages matching the query
            results = service.users().messages().list(userId="me", q=query).execute()
            messages = results.get("messages", [])
            
            if not messages:
                print("No messages found matching the query.")
                return
        else:
            print("Error: Either message_id or query must be provided.")
            return

        for message in messages:
            message_id = message["id"]

            # Retrieve email details before archiving to use in logging
            msg_data = service.users().messages().get(userId="me", id=message_id).execute()
            
            # Extract subject from headers
            headers = msg_data["payload"]["headers"]
            email_subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")

            # Modify the message to remove the INBOX label
            modify_request_body = {
                "removeLabelIds": ["INBOX"]
            }
            service.users().messages().modify(
                userId="me", id=message_id, body=modify_request_body
            ).execute()

            print(f"Archived message with ID: {message_id}")
            # Use the retrieved email details for logging
            # log.log_email(email_subject, None, email_body, "Archived")
            return

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__name__":
    service = authenticate_gmail()
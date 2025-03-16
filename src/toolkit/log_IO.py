import datetime

def log_email(subject, recipient, content, status):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"<Email> [{timestamp}] To: {recipient} | Subject: {subject} | Status: {status} | Content: {content}\n"
    with open("logs.txt", "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)

def log_calendar(start, end, subject, content, status):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"<Calendar> [{timestamp}] {start} to {end} | Subject: {subject} | Status: {status} | Content: {content}\n"
    with open("logs.txt", "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)

if __name__ == '__main__':

    # Example usage
    log_email("Meeting Update", "user@example.com", "Let's meet at 3 PM.", "Sent")
    log_calendar("2025-3-11 10:00", "2025-3-11 12:00", "Christmas Day", "Celebrate Christmas", "Created")

import os
import sys
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import datetime

module_path = os.path.abspath("toolkit")

sys.path.append(module_path)

import log_IO as log

# pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Step 1: 认证并获取授权
# Change from readonly to full access
SCOPES = ['https://www.googleapis.com/auth/calendar']


def authenticate_calendar():
    creds = None

    # 如果存在token_calendar.pickle文件，加载它
    if os.path.exists('token_calendar.pickle'):
        with open('token_calendar.pickle', 'rb') as token:
            creds = pickle.load(token)

    # 如果没有凭据或凭据失效，则重新认证
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Get the directory of the current script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Construct the path to the credentials file
            credentials_path = os.path.join(current_dir, "credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # 保存新的 token
        with open("token_calendar.pickle", "wb") as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)


def get_calendar_events(service, number_of_events=2):
    # 调用 Google Calendar API
    try:
        # 获取当前日期和时间
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z'表示UTC时间

        # 获取下2个事件
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                            maxResults = number_of_events, singleEvents = True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])



        if not events:
            print('No upcoming events found.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"{start} - {event['summary']}")

    except HttpError as error:
        print(f'An error occurred: {error}')

def add_calendar_event(service, date, time_start, time_end, summary, description='', location='', attendees=['zhaowj1107@gmail.com']):
    """
    Add an event to Google Calendar.
    
    Args:
    date (str): Date in YYYY-MM-DD format
    time_start (str): Start time in HH:MM format
    time_end (str): End time in HH:MM format
    summary (str): Title of the event
    description (str, optional): Description of the event
    location (str, optional): Location of the event
    attendees (list, optional): List of email addresses of attendees
    
    Returns:
    dict: The created event details or None if an error occurred
    """
    # 调用 Google Calendar API
    try:
        # Format datetime strings
        start_datetime = f"{date}T{time_start}:00"
        end_datetime = f"{date}T{time_end}:00"
        
        # Build event details
        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
            'dateTime': start_datetime,
            'timeZone': 'America/Los_Angeles',
            },
            'end': {
            'dateTime': end_datetime,
            'timeZone': 'America/Los_Angeles',
            }
        }
        
        # Add attendees if provided
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        
        # Insert the event
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f'Event created: {event.get("htmlLink")}')
        # Log the event
        log.log_calendar(start_datetime, end_datetime, summary, description, "Created")
        return event
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None
    

if __name__ == "__main__":
    service = authenticate_calendar()
    get_calendar_events(service, 2)
    add_calendar_event(service,'2025-3-11', '10:00', '12:00', 'Christmas Day', 'Celebrate Christmas', 'Home')
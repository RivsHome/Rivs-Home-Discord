import os.path
import datetime
import dateparser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

CREDS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_calendar_service():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                raise FileNotFoundError(f"Missing {CREDS_FILE}. Please download it from Google Cloud Console.")
                
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service

def create_event(summary, start_time_str):
    """
    Creates an event with a 24-hour reminder.
    start_time_str: can be natural language like "tomorrow at 5pm"
    """
    service = get_calendar_service()
    
    # Parse the time
    dt = dateparser.parse(start_time_str)
    if not dt:
        return None, "Could not parse date/time."
        
    # Ensure future date if vague (optional, but good practice if user says '5pm' meaning today/tomorrow)
    if dt < datetime.datetime.now():
        # If it's in the past, maybe they meant tomorrow? Or just let it be. 
        # For now, let's assume they might specify the date. 
        pass

    # Create end time (default 1 hour)
    end_dt = dt + datetime.timedelta(hours=1)
    
    event = {
        'summary': summary,
        'start': {
            'dateTime': dt.isoformat(),
            'timeZone': 'UTC', # Adjust if you want local time, usually better to detect or set config
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': 'UTC',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 1440}, # 24 hours
                {'method': 'email', 'minutes': 1440},
            ],
        },
    }

    event_result = service.events().insert(calendarId='primary', body=event).execute()
    return event_result, None

def list_upcoming_events(date_str=None):
    """
    Lists events for a specific day, or upcoming 10 if no day specified.
    """
    service = get_calendar_service()
    
    if date_str:
        target_date = dateparser.parse(date_str)
        if not target_date:
            return None, "Could not parse date."
        
        # Start of day
        time_min_dt = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        # End of day
        time_max_dt = target_date.replace(hour=23, minute=59, second=59, microsecond=0)
        
        time_min = time_min_dt.isoformat() + 'Z'
        time_max = time_max_dt.isoformat() + 'Z'
        
        events_result = service.events().list(calendarId='primary', timeMin=time_min,
                                              timeMax=time_max, singleEvents=True,
                                              orderBy='startTime').execute()
    else:
        # Just next 10 events from now
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()

    events = events_result.get('items', [])
    return events, None

from datetime import datetime, timedelta
import re
import pytz
from email.utils import parseaddr
from langsmith import traceable
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from src.utils import get_credentials

class AddEventToCalendarInput(BaseModel):
    title: str = Field(description="Title of the event")
    description: str = Field(description="Description of the event")
    start_time: str = Field(description="Start time of the event (can be in various formats)")
    duration_minutes: int = Field(description="Duration of the event in minutes", default=60)
    attendees: str = Field(description="Comma-separated list of attendee email addresses", default="")

@tool("AddEventToCalendar", args_schema=AddEventToCalendarInput)
@traceable(run_type="tool", name="AddEventToCalendar")
def add_event_to_calendar(title: str, description: str, start_time: str, duration_minutes: int = 60, attendees: str = ""):
    "Use this to create a new event in my calendar with optional attendees"
    try:
        # Log the attempt
        print(f"Attempting to create calendar event: '{title}' at {start_time}")
        
        # Get credentials - this will raise an exception if auth fails
        creds = get_credentials()
        if not creds or not creds.valid:
            error_msg = "ERROR: Invalid or expired Google credentials"
            print(error_msg)
            return error_msg
            
        # Build the calendar service
        service = build("calendar", "v3", credentials=creds)

        # Parse attendees
        attendee_list = []
        if attendees:
            for email in attendees.split(','):
                email = email.strip()
                _, email_addr = parseaddr(email)
                if email_addr:
                    attendee_list.append({'email': email_addr})
                    print(f"Added attendee: {email_addr}")
        
        # Try to parse different date formats
        event_datetime = parse_datetime(start_time)
        if not event_datetime:
            error_msg = f"ERROR: Could not parse date/time: {start_time}. Please use a common format like 'YYYY-MM-DD HH:MM' or 'today at HH:MM'."
            print(error_msg)
            return error_msg
        
        # Set timezone to IST if "IST" is mentioned, otherwise use UTC
        timezone = 'Asia/Kolkata' if 'ist' in start_time.lower() else 'UTC'
        if timezone == 'Asia/Kolkata':
            # If start_time was parsed as UTC but IST was specified, convert
            if event_datetime.tzinfo is None or event_datetime.tzinfo.utcoffset(event_datetime) is None:
                # Naive datetime, assume it was in the specified timezone
                event_datetime = pytz.timezone(timezone).localize(event_datetime)
                # Convert to UTC for Google Calendar
                event_datetime = event_datetime.astimezone(pytz.UTC)

        # Calculate end time based on duration
        end_datetime = event_datetime + timedelta(minutes=duration_minutes)

        # Create the event
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': event_datetime.isoformat(),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': timezone,
            },
        }

        # Add attendees if specified
        if attendee_list:
            event['attendees'] = attendee_list
        
        # Set email notification for attendees
        event['reminders'] = {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 30},
            ],
        }

        # Insert the event - this is the point where it actually gets created
        print(f"Creating calendar event: {title} at {event_datetime}")
        try:
            created_event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
            event_id = created_event.get('id', 'unknown')
            success_msg = f"SUCCESS: Event '{title}' scheduled for {start_time} with {len(attendee_list)} attendee(s). Event ID: {event_id}"
            print(success_msg)
            return success_msg
        except Exception as api_error:
            error_msg = f"ERROR: Failed to create event in calendar: {str(api_error)}"
            print(error_msg)
            return error_msg

    except HttpError as error:
        error_message = f"ERROR: Google Calendar API error: {str(error)}"
        print(error_message)
        return error_message
    except Exception as e:
        error_message = f"ERROR: An unexpected error occurred: {str(e)}"
        print(error_message)
        return error_message

def parse_datetime(datetime_str):
    """Parse various datetime formats including natural language ones."""
    try:
        # Try standard ISO format first
        return datetime.fromisoformat(datetime_str)
    except ValueError:
        pass
    
    try:
        # Try to parse common date formats
        formats = [
            '%Y-%m-%d %H:%M',
            '%Y/%m/%d %H:%M',
            '%d-%m-%Y %H:%M',
            '%d/%m/%Y %H:%M',
            '%B %d, %Y %H:%M',
            '%b %d, %Y %H:%M',
            '%Y-%m-%d %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        # Check for "today at HH:MM" format
        today_match = re.search(r'today\s+at\s+(\d{1,2}):(\d{2})', datetime_str, re.IGNORECASE)
        if today_match:
            hour, minute = map(int, today_match.groups())
            now = datetime.now()
            return datetime(now.year, now.month, now.day, hour, minute)
        
        # Try to extract time like "20:55 IST"
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(ist|utc|gmt)?', datetime_str, re.IGNORECASE)
        if time_match:
            hour, minute = map(int, time_match.groups()[:2])
            now = datetime.now()
            return datetime(now.year, now.month, now.day, hour, minute)
            
        return None
    except Exception:
        return None
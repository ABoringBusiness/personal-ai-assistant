import os 
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/contacts.readonly",
    'https://www.googleapis.com/auth/gmail.readonly'
]

def get_current_date_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M")
        
def get_credentials():
    """
    Get and refresh Google Contacts API credentials
    """
    creds = None
    token_path = 'token.json'
    
    # Check if token exists and is valid
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            # Test if these credentials actually work
            if creds and creds.valid:
                print("Using existing valid credentials")
                return creds
        except Exception as e:
            print(f"Error loading existing credentials: {e}")
            # Delete invalid token file
            try:
                os.remove(token_path)
                print("Removed invalid token file")
            except:
                pass
    
    # If there are no (valid) credentials, let's create new ones
    try:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("Creating new OAuth credentials...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            
            # Explicitly request access_type=offline to get a refresh token
            # include prompt=consent to force the consent screen and refresh token
            flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Use port 8080 which is registered in credentials.json
            print("Opening browser for OAuth authorization...")
            creds = flow.run_local_server(
                port=8080,
                open_browser=True,
                success_message="Authentication successful! You can close this window and return to the application."
            )
            
            # Verify refresh token is present
            if not hasattr(creds, 'refresh_token') or not creds.refresh_token:
                print("WARNING: No refresh token received. Authentication may need to be repeated.")
        
        # Save the credentials
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            print(f"Credentials saved to {token_path}")
            
        return creds
    except Exception as e:
        print(f"Error in authentication process: {e}")
        raise

def extract_provider_and_model(model_string: str):
    return model_string.split("/", 1)

def get_llm_by_provider(model_string, temperature=0.1):
    llm_provider, model = extract_provider_and_model(model_string)
    # Else find provider
    if llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=model, temperature=temperature)
    # elif llm_provider == "anthropic":
        # from langchain_anthropic import ChatAnthropic
        # llm = ChatAnthropic(model=model, temperature=temperature)  # Use the correct model name
    elif llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model=model, temperature=temperature)  # Correct model name
    elif llm_provider == "groq":
        from langchain_groq import ChatGroq
        llm = ChatGroq(model=model, temperature=temperature)
    # ... add elif blocks for other providers ...
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")
    return llm
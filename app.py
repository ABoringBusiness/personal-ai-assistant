import time
import signal
import os
import sqlite3
from dotenv import load_dotenv
from src.channels.telegram import TelegramChannel
from src.agents.personal_assistant import PersonalAssistant

# Load .env variables
load_dotenv()

# Clean up any old OAuth tokens to ensure a fresh auth flow
token_path = "token.json"
if os.path.exists(token_path):
    try:
        os.remove(token_path)
        print(f"Removed existing token file to force fresh authentication")
    except Exception as e:
        print(f"Error removing token file: {e}")

# Initialize database directory if it doesn't exist
os.makedirs("db", exist_ok=True)

# Clear any existing database
db_path = "db/checkpoints.sqlite"
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    except Exception as e:
        print(f"Error removing existing database: {e}")

# Initialize fresh sqlite3 DB for saving agent memory
conn = sqlite3.connect(db_path, check_same_thread=False)
print(f"Created new database connection: {db_path}")

# Use telegram for communicating with the agent
telegram = TelegramChannel()
# Use Slack for communicating with the agent
# slack = SlackChannel()

# Configuration for the Langgraph checkpoints, specifying thread ID
config = {"configurable": {"thread_id": "1"}}

# Flag to track if cleanup has been done
cleanup_completed = False

def cleanup_and_exit():
    """Handle cleanup and exit gracefully"""
    global cleanup_completed
    if not cleanup_completed:
        try:
            print("\nCleaning up and exiting...")
            # Send goodbye message
            telegram.send_message("👋 Goodbye! Session ended.")
            # Close database connection
            if conn:
                conn.close()
                print("Database connection closed")
            cleanup_completed = True
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            exit(0)

def signal_handler(signum, frame):
    """Handle signal interrupts"""
    print("\nSignal received, ending session...")
    cleanup_and_exit()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Initiate personal assistant
personal_assistant = PersonalAssistant(conn)

def monitor_channel(after_timestamp, config):
    print("Starting to monitor messages...")
    
    while True:
        try:
            new_messages = telegram.receive_messages(after_timestamp)
            
            if new_messages:
                for message in new_messages:                    
                    # Process message
                    print(f"\nProcessing message: {message['text']}")
                    sent_message = (
                        f"Message: {message['text']}\n"
                        f"Current Date/time: {message['date']}"
                    )
                    
                    # Invoke personal assistant and get response
                    try:
                        answer = personal_assistant.invoke(sent_message, config=config)
                        print(f"Sending response: {answer[:100]}...")
                        telegram.send_message(answer)
                    except Exception as e:
                        error_msg = f"Error processing message: {str(e)}"
                        print(error_msg)
                        telegram.send_message(f"Sorry, I encountered an error: {str(e)}")
            
            after_timestamp = int(time.time())
            time.sleep(1)  # Check more frequently with shorter sleep
            
        except Exception as e:
            print(f"Error in monitor_channel: {str(e)}")
            time.sleep(1)

if __name__ == "__main__":
    print("Personal Assistant Manager is running")
    try:
        monitor_channel(int(time.time()), config)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        cleanup_and_exit()
from langgraph.checkpoint.sqlite import SqliteSaver
from src.agents.base import Agent, AgentsOrchestrator
from src.prompts import *
from src.tools.calendar import *
from src.tools.email import *
from src.tools.notion import *
from src.tools.slack import *
from src.tools.research import *
from src.utils import get_current_date_time
import sqlite3

class PersonalAssistant:
    def __init__(self, db_connection):
        # Store db connection
        self.db_connection = db_connection
        
        # Create sqlite checkpointer for managing manager memory
        self.checkpointer = SqliteSaver(db_connection)
        
        # Initialize individual agents
        self.email_agent = Agent(
            name="email_agent",
            description="Email agent can manage GMAIL inbox including read and send emails",
            model="openai/gpt-4o-mini",
            system_prompt=EMAIL_AGENT_PROMPT.format(date_time=get_current_date_time()),
            tools=[read_emails, send_email, find_contact_email],
            sub_agents=[],
            temperature=0.1
        )

        self.calendar_agent = Agent(
            name="calendar_agent",
            description="Calendar agent can manage Google Calendar including get events and create events",
            model="openai/gpt-4o-mini",
            system_prompt=CALENDAR_AGENT_PROMPT.format(date_time=get_current_date_time()),
            tools=[get_calendar_events, add_event_to_calendar, find_contact_email],
            sub_agents=[],
            temperature=0.1
        )

        self.notion_agent = Agent(
            name="notion_agent",
            description="Notion agent can manage Notion including get my todo list and add task in todo list",
            model="openai/gpt-4o-mini",
            system_prompt=NOTION_AGENT_PROMPT.format(date_time=get_current_date_time()),
            tools=[get_my_todo_list, add_task_in_todo_list],
            sub_agents=[],
            temperature=0.1
        )

        self.slack_agent = Agent(
            name="slack_agent",
            description="Slack agent can read and send messages through Slack",
            model="openai/gpt-4o-mini",
            system_prompt=SLACK_AGENT_PROMPT.format(date_time=get_current_date_time()),
            tools=[get_slack_messages, send_slack_message],
            sub_agents=[],
            temperature=0.1
        )

        self.researcher_agent = Agent(
            name="researcher_agent",
            description="Researcher agent can search the web, scrape websites or LinkedIn profiles",
            model="openai/gpt-4o-mini",
            system_prompt=RESEARCHER_AGENT_PROMPT.format(date_time=get_current_date_time()),
            tools=[search_web, scrape_website_to_markdown, search_linkedin_tool],
            sub_agents=[],
            temperature=0.1
        )

        # Initialize the manager agent
        self.manager_agent = Agent(
            name="manager_agent",
            description="Manager agent",
            model="openai/gpt-4o",
            system_prompt=ASSISTANT_MANAGER_PROMPT.format(date_time=get_current_date_time()),
            tools=[],
            sub_agents=[
                self.email_agent,
                self.calendar_agent,
                self.notion_agent,
                self.slack_agent,
                self.researcher_agent
            ],
            temperature=0.1,
            memory=self.checkpointer # only manager has memory feature
        )

        # Initialize the orchestrator
        self.assistant_orchestrator = AgentsOrchestrator(
            main_agent=self.manager_agent,
            agents=[
                self.manager_agent,
                self.email_agent,
                self.calendar_agent,
                self.notion_agent,
                self.slack_agent,
                self.researcher_agent
            ]
        )

    def clear_state(self):
        """Clear all stored state from the database"""
        try:
            print("Completely clearing database state...")
            # Get a cursor for the database
            cursor = self.db_connection.cursor()
            
            # Drop all tables in the database to completely clear the state
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
            
            # Commit the changes
            self.db_connection.commit()
            
            # Reinitialize the checkpointer after clearing the database
            self.checkpointer = SqliteSaver(self.db_connection)
            
            # Reinitialize the manager agent with the new checkpointer
            self.manager_agent.memory = self.checkpointer
            self.manager_agent.agent = None
            self.manager_agent.initiat_agent()
            
            print("Database state cleared successfully")
        except Exception as e:
            print(f"Error clearing database state: {e}")

    def invoke(self, message, **kwargs):
        """Invoke the personal assistant with a fresh state"""
        # Clear any existing state before processing
        self.clear_state()
        
        # Now invoke with a fresh state
        print("Invoking assistant with fresh state...")
        return self.assistant_orchestrator.invoke(message, **kwargs)

    def __getattr__(self, name):
        return getattr(self.assistant_orchestrator, name)

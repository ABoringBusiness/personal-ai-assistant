from datetime import datetime
from enum import Enum
import os
from langsmith import traceable
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from notion_client import Client, APIResponseError

class TaskStatus(Enum):
    NOT_STARTED = "Not started"
    IN_PROGRESS = "In progress"
    COMPLETED = "Completed"

class AddTaskInTodoListInput(BaseModel):
    task: str = Field(description="Task to be added")
    date: str = Field(description="Date and time for the task (YYYY-MM-DD) (HH:MM)")

@tool("AddTaskInTodoList", args_schema=AddTaskInTodoListInput)
@traceable(run_type="tool", name="AddTaskInTodoList")
def add_task_in_todo_list(task: str, date: str):
    "Use this to add a new task to my todo list"
    try:
        # Check if environment variables are set
        notion_token = os.getenv("NOTION_TOKEN")
        notion_db_id = os.getenv("NOTION_DATABASE_ID")
        
        if not notion_token:
            error_msg = "ERROR: NOTION_TOKEN environment variable is not set"
            print(error_msg)
            return error_msg
            
        if not notion_db_id:
            error_msg = "ERROR: NOTION_DATABASE_ID environment variable is not set"
            print(error_msg)
            return error_msg
        
        print(f"Adding task to Notion: '{task}' for {date}")
        
        # Initialize the Notion client
        notion = Client(auth=notion_token)

        # Create new task
        new_task = {
            "Title": {"title": [{"text": {"content": task}}]},
            "Status": {"status": {"name": TaskStatus.NOT_STARTED.value}},
        }
        if date:
            new_task["Date"] = {"date": {"start": date}}

        # Add task to Notion
        try:
            page = notion.pages.create(
                parent={"database_id": notion_db_id},
                properties=new_task
            )
            success_msg = f"SUCCESS: Task '{task}' added successfully to Todo list for {date}."
            print(success_msg)
            return success_msg
        except APIResponseError as api_error:
            error_msg = f"ERROR: Notion API error: {str(api_error)}"
            print(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"ERROR: An unexpected error occurred: {str(e)}"
        print(error_msg)
        return error_msg
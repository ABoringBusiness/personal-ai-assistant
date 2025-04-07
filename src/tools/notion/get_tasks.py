import os
from langsmith import traceable
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from notion_client import Client, APIResponseError

class GetMyTodoListInput(BaseModel):
    status: str = Field(description="Status filter (optional): 'not started', 'in progress', 'completed'", default="")

@tool("GetMyTodoList", args_schema=GetMyTodoListInput)
@traceable(run_type="tool", name="GetMyTodoList")
def get_my_todo_list(status: str = ""):
    "Use this to get all my tasks from notion database (to-do list)"
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

        print(f"Retrieving Notion tasks with status filter: '{status if status else 'all'}'")
        
        # Initialize the Notion client
        notion = Client(auth=notion_token)

        # Prepare filter if status is provided
        filter_params = {}
        if status:
            filter_params = {
                "filter": {
                    "property": "Status",
                    "status": {
                        "equals": status.capitalize()
                    }
                }
            }

        # Query the database
        try:
            response = notion.databases.query(
                database_id=notion_db_id,
                **filter_params
            )
            
            # Parse tasks
            tasks = []
            for page in response["results"]:
                try:
                    # Get task title
                    title = "Unnamed Task"
                    if "Title" in page["properties"]:
                        title_content = page["properties"]["Title"]["title"]
                        if title_content:
                            title = title_content[0]["plain_text"]
                    
                    # Get task status
                    task_status = "Unknown"
                    if "Status" in page["properties"] and page["properties"]["Status"]["status"]:
                        task_status = page["properties"]["Status"]["status"]["name"]
                    
                    # Get task date
                    task_date = "No date"
                    if "Date" in page["properties"] and page["properties"]["Date"]["date"]:
                        task_date = page["properties"]["Date"]["date"]["start"]
                    
                    tasks.append(f"- {title} | Status: {task_status} | Due: {task_date}")
                except Exception as e:
                    print(f"Error processing a task: {e}")
                    tasks.append("- Error parsing a task")
            
            if not tasks:
                if status:
                    return f"No tasks found with status '{status}'"
                else:
                    return "No tasks found in your todo list"
                    
            tasks_str = "\n".join(tasks)
            success_msg = f"SUCCESS: Here are your tasks:\n{tasks_str}"
            print(f"Retrieved {len(tasks)} tasks from Notion")
            return success_msg
            
        except APIResponseError as api_error:
            error_msg = f"ERROR: Notion API error: {str(api_error)}"
            print(error_msg)
            return error_msg
            
    except Exception as e:
        error_msg = f"ERROR: An unexpected error occurred while fetching tasks: {str(e)}"
        print(error_msg)
        return error_msg
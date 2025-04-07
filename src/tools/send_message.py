from typing import Optional, Type, Dict
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.messages import HumanMessage
from langsmith import traceable
from pydantic import BaseModel
from langchain.tools import BaseTool
from src.agents.base import Agent


class SendMessage(BaseTool):
    name: str = "SendMessage"
    description: str = "Use this to send a message to one of your sub-agents"
    args_schema: Type[BaseModel]
    agent_mapping: Dict[str, "Agent"] = None 

    def send_message(self, recipient: str, message: str) -> str:
        """Send a message to a sub-agent and get its response"""
        print(f"SendMessage tool called: recipient={recipient}, message={message[:50]}...")
        
        if not self.agent_mapping:
            print("Error: agent_mapping is not set")
            return "Error: agent_mapping is not set"
        
        agent = self.agent_mapping.get(recipient)
        if not agent:
            print(f"Error: recipient '{recipient}' not found in agent_mapping")
            return f"Error: recipient '{recipient}' not found. Available agents: {list(self.agent_mapping.keys())}"
        
        try:
            # Create a fresh state with the message
            agent_state = {"messages": [HumanMessage(content=message)]}
            
            # Invoke the agent
            print(f"Invoking {recipient} agent...")
            response = agent.invoke(agent_state)
            
            # Extract the response content
            if isinstance(response, dict) and 'messages' in response:
                messages = response.get('messages', [])
                if messages:
                    last_message = messages[-1]
                    content = last_message.content if hasattr(last_message, 'content') else str(last_message)
                    print(f"Response from {recipient}: {content[:100]}...")
                    return content
            
            # Fallback for other response types
            result = str(response)
            print(f"Response from {recipient}: {result[:100]}...")
            return result
            
        except Exception as e:
            error_msg = f"Error sending message to {recipient}: {str(e)}"
            print(error_msg)
            return error_msg

    @traceable(run_type="tool", name="SendMessage")
    def _run(
        self,
        recipient: str,
        message: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        return self.send_message(recipient, message)
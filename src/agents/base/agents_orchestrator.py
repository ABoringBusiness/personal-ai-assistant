from pydantic import Field, create_model
from .agent import Agent
from src.tools.send_message import SendMessage
from typing import List, Dict, Any, Optional
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool

def execute_send_message(args):
    """
    Execute the SendMessage tool to schedule a meeting or send a message to an agent.
    Args: dict containing 'recipient' and 'message' keys.
    Returns: str indicating the result.
    """
    recipient = args.get("recipient", "unknown")
    message = args.get("message", "")
    # Simulate sending to calendar_agent (replace with actual logic)
    try:
        # Placeholder for actual scheduling logic (e.g., Google Calendar API)
        return f"Message sent to {recipient}: {message}"
    except Exception as e:
        return f"Failed to send message: {str(e)}"

class AgentsOrchestrator:
    def __init__(self, main_agent, agents):
        self.main_agent = main_agent
        self.agents = {agent.name: agent for agent in agents}
        self.agent_mapping = {}
        self._populate_agent_mapping()
        
        # Add send message tools to agents with sub-agents
        self._add_send_message_tool()
        
        # Initialize the main agent
        if not self.main_agent.agent:
            self.main_agent.initiat_agent()
        
        print(f"Initialized orchestrator with {len(self.agents)} agents")
        print(f"Main agent tools: {[tool.name if hasattr(tool, 'name') else str(tool) for tool in self.main_agent.tools]}")
        print(f"Available agents: {list(self.agents.keys())}")

    def _populate_agent_mapping(self):
        """Populate the agent mapping dictionary"""
        for agent in self.agents.values():
            self.agent_mapping[agent.name] = agent

    def _get_agent_by_name(self, name: str):
        """Get an agent by its name"""
        return self.agent_mapping.get(name)

    def _process_tool_call(self, tool_call, config: Dict[str, Any]) -> Optional[ToolMessage]:
        """Process a single tool call and return its ToolMessage response"""
        try:
            # Get the tool call ID and args
            tool_call_id = tool_call.id
            tool_name = getattr(tool_call, 'name', 'SendMessage')
            
            # Get the recipient and message from the arguments
            args = getattr(tool_call, 'args', {})
            recipient = args.get('recipient', 'unknown')
            message = args.get('message', '')
            
            print(f"Processing tool call {tool_call_id} to {recipient}")
            
            # Get the appropriate agent
            agent = self._get_agent_by_name(recipient)
            
            # If we found a valid agent, invoke it
            if agent:
                # Create a clean state for the agent
                agent_state = {"messages": [HumanMessage(content=message)]}
                
                # Invoke the agent
                print(f"Invoking {recipient} agent...")
                agent_response = agent.invoke(agent_state, config=config)
                
                # Extract the content from the response
                if isinstance(agent_response, dict) and 'messages' in agent_response:
                    # Get the last message from the agent response
                    agent_messages = agent_response.get('messages', [])
                    last_message = agent_messages[-1] if agent_messages else None
                    content = last_message.content if hasattr(last_message, 'content') else str(last_message)
                else:
                    # Handle non-dict responses
                    content = str(agent_response)
                    
                print(f"Got response from {recipient}: {content[:50]}...")
            else:
                # No agent found
                content = f"Error: Agent '{recipient}' not found"
                print(f"Agent {recipient} not found")
            
            # Create and return the tool message
            tool_message = ToolMessage(
                tool_call_id=tool_call_id,
                content=content,
                name=tool_name
            )
            
            print(f"Created tool message for {tool_call_id}")
            return tool_message
            
        except Exception as e:
            # Log the error
            print(f"Error processing tool call: {str(e)}")
            
            # Return error message as tool response
            return ToolMessage(
                tool_call_id=tool_call.id,
                content=f"Error: {str(e)}",
                name="SendMessage"
            )

    def invoke(self, message: str, config: Dict[str, Any] = None) -> str:
        """Invoke the orchestrator with a message"""
        try:
            print(f"Processing message: {message}")
            
            # Start with a completely fresh state
            fresh_state = {"messages": [HumanMessage(content=message)]}
            
            # First invocation to get initial response
            print("Getting initial response...")
            response = self.main_agent.invoke(fresh_state, config=config)
            
            if not isinstance(response, dict) or 'messages' not in response:
                print("No messages in response, returning as is")
                return str(response)
            
            response_messages = response.get('messages', [])
            last_message = response_messages[-1] if response_messages else None
            
            # Check for tool calls in the response
            if not (isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls):
                print("No tool calls found, returning response")
                return last_message.content if isinstance(last_message, AIMessage) else str(last_message)
            
            # We have tool calls to process
            print(f"Found {len(last_message.tool_calls)} tool calls to process")
            
            # Process all tool calls in sequence
            updated_messages = response_messages.copy()
            had_errors = False
            error_messages = []
            
            for tool_call in last_message.tool_calls:
                print(f"Processing tool call: {tool_call.name} to {tool_call.args.get('recipient', 'unknown')}")
                tool_response = self._process_tool_call(tool_call, config)
                
                if tool_response:
                    print(f"Adding tool response for {tool_call.id}")
                    updated_messages.append(tool_response)
                    
                    # Check if this tool response contains an error
                    if hasattr(tool_response, 'content') and "ERROR:" in tool_response.content:
                        had_errors = True
                        error_messages.append(tool_response.content)
                
            # Update the graph state with all messages including tool responses
            print(f"Updating state with {len(updated_messages)} messages including tool responses")
            self.main_agent.agent.update_state(config, {"messages": updated_messages})
            
            # If we had errors, modify the state to include error information
            if had_errors:
                error_state = {"messages": updated_messages + [
                    HumanMessage(content=f"There were errors processing the request:\n{', '.join(error_messages)}\nPlease report these errors to the user.")
                ]}
                self.main_agent.agent.update_state(config, error_state)
                print("Added error information to state")
            
            # Get final response after processing all tool calls
            print("Getting final response after tool processing...")
            final_response = self.main_agent.invoke(None, config=config)
            
            # Check the final response for errors
            final_content = ""
            if isinstance(final_response, dict) and 'messages' in final_response:
                final_messages = final_response.get('messages', [])
                final_message = final_messages[-1] if final_messages else None
                final_content = final_message.content if isinstance(final_message, AIMessage) else str(final_response)
            else:
                final_content = str(final_response)
            
            # If we had errors but they're not reflected in the final response, prepend them
            if had_errors and not any(error_msg in final_content for error_msg in error_messages):
                error_summary = "ERROR: The requested operation failed due to the following issues:\n" + "\n".join(error_messages)
                print("Adding error information to final response")
                return error_summary
            
            return final_content
        except Exception as e:
            print(f"Error in orchestrator.invoke: {str(e)}")
            return f"ERROR: I encountered an error processing your request: {str(e)}"

    def stream(self, message, **kwargs):
        """Stream response from the orchestrator"""
        messages = {"messages": [("human", message)]}
        for chunk in self.main_agent.stream(messages, **kwargs):
            yield chunk

    def _create_dynamic_send_message_tool(self, agent: "Agent") -> "SendMessage":
        """
        Creates a dynamic send message tool for agents with sub-agents.
        """
        # Generate a description for the recipients
        recipients_description = "\n".join(
            f"{sub_agent.name}: {sub_agent.description}"
            for sub_agent in agent.sub_agents
            if sub_agent.description
        )

        # Create a dynamic input schema
        DynamicSendMessageInput = create_model(
            f"{agent.name}SendMessageInput",
            recipient=(str, Field(..., description=recipients_description)),
            message=(str, Field(..., description="Message to send to sub-agent.")),
        )

        # Create the SendMessage tool instance
        send_message_tool = SendMessage(args_schema=DynamicSendMessageInput)
        send_message_tool.agent_mapping = self.agent_mapping  # Dynamically bind agent_mapping
        return send_message_tool

    def _add_send_message_tool(self):
        """
        Adds the send message tool to agents with sub-agents.
        """
        for agent in self.agents.values():
            if hasattr(agent, "sub_agents") and agent.sub_agents:
                send_message_tool = self._create_dynamic_send_message_tool(agent)
                agent.tools.append(send_message_tool)

                # Bind the new tool to the agent's LLM model
                agent.initiat_agent()

    def get_agent(self, name: str) -> "Agent":
        """
        Retrieves an agent from the mapping by name.
        """
        return self.agent_mapping.get(name)

from typing import Annotated

from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

# def make_handoff_tool(*, agent_name: str):
#     """Create a tool that can return handoff via a Command"""
#     tool_name = f"transfer_to_{agent_name}"

#     @tool(tool_name)
#     def handoff_to_agent(
#         state: Annotated[dict, InjectedState],
#         tool_call_id: Annotated[str, InjectedToolCallId],
#     ):
#         """Ask another agent for help."""
#         tool_message = {
#             "role": "tool",
#             "content": f"Successfully transferred to {agent_name}",
#             "name": tool_name,
#             "tool_call_id": tool_call_id,
#         }
#         return Command(
#             # navigate to another agent node in the PARENT graph
#             goto=agent_name,
#             graph=Command.PARENT,
#             # This is the state update that the agent `agent_name` will see when it is invoked.
#             # We're passing agent's FULL internal message history AND adding a tool message to make sure
#             # the resulting chat history is valid.
#             update={"messages": state["messages"] + [tool_message]},
#         )

#     return handoff_to_agent

from langchain_core.messages import AIMessage,HumanMessage,ToolMessage

from langchain_core.tools import tool
from langgraph.types import Command
from typing import Annotated

def make_handoff_tool(*, agent_name: str):
    """Create a tool that checks for a specific tool call in state and transfers or continues accordingly."""
    tool_name = f"check_or_transfer_to_{agent_name}"

    @tool(tool_name)
    def handoff_to_agent(
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        """Check for a specific tool in messages and transfer to agent or continue."""
        messages = state.get("messages", [])
        found = False
        tool_to_check ="query_cedemo_db"
        
        for msg in messages:
            
            if isinstance(msg,ToolMessage):
                    # print("Tool Message", msg.content)
                    print("\n \n \n")
                    if msg.name == 'query_cedemo_db':
                        found = True
                        break
           

        if found:
            # Tool was already used -> Transfer to target agent
            tool_message = {
                "role": "tool",
                "content": f"Successfully transferred to {agent_name}",
                "name": tool_name,
                "tool_call_id": tool_call_id,
            }
            return Command(
                goto=agent_name,
                graph=Command.PARENT,
                update={"messages": messages + [tool_message]},
            )
        else:
            # Tool was NOT used -> update messages and stay in current node
            system_message = {
                "role": "tool",
                "content": f"Tool '{tool_to_check}' not found in context. Generate SQl query and use the {tool_to_check} to get result",
                "name": tool_name,
                "tool_call_id": tool_call_id,
            }
            return Command(
                goto=None,
                update={"messages": messages + [system_message]},
            )

    return handoff_to_agent



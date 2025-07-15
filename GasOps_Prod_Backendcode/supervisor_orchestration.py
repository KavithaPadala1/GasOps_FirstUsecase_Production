import logging
import asyncio
import re
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langgraph_swarm import create_swarm, create_handoff_tool
from agents.cedemodb_agent import cedemo_agent  # execution agent for cedemo
from agents.oamscmdb_agent import oamscm_agent  # execution agent for oamscm
from supervisor_prompt import supervisor_prompt
from langchain_core.prompts import ChatPromptTemplate
from agents.azure_llm import load_azureopenai_llm_client  # importing the Azure openai client
from hand_off_tools import transfer_to_cedemo_execution, transfer_to_cedemo_plan, transfer_to_cedemo_validation, transfer_to_oamscm_execution, transfer_to_oamscm_validation, transfer_to_oamscm_plan
from ai_search.ai_search import cedemo_search, oamscm_search
from langchain_core.messages import convert_to_messages, AIMessage, HumanMessage, ToolMessage, AnyMessage, BaseMessage, BaseMessageChunk, MessageLikeRepresentation, RemoveMessage, message_chunk_to_message
from langgraph.graph import MessagesState, StateGraph, START, END, add_messages
from typing import Annotated, Literal
from langgraph.types import Command

def pretty_print_messages(update):
    try:
        if isinstance(update, tuple):
            ns, update = update
            if len(ns) == 0:
                return
            graph_id = ns[-1].split(":")[0]
            print(f"Update from subgraph {graph_id}:")
            print("\n")
        for node_name, node_update in update.items():
            print(f"Update from node {node_name}:")
            print("\n")
            if node_name != "generate_structured_response":
                for m in convert_to_messages(node_update["messages"]):
                    m.pretty_print()
            else:
                print(node_update)
            print("\n")
    except Exception as e:
        logging.error(f"Error in pretty_print_messages: {str(e)}")

# Initialize LLM - Azue OpenAI 
model = load_azureopenai_llm_client()

# --- Prompt templates with Azure AI Search results ---
async def cedemo_prompt_template(state):
    # user_input = state["messages"][0].content
    for message in state["messages"]:
        # if message.role == "user":
        #     user_input = message.content
        if isinstance(message,HumanMessage):
            user_input = message.content

    docs = await cedemo_search(user_input)
    contents = [d.page_content for d in docs]
    examples = "\n".join(contents)
    state["cedemo"] = f"These are sample examples from Azure AI Search. Use them as reference only:\n{examples}"
    return ChatPromptTemplate.from_template(
       """
You are the CEDEMO planning and validation agent.
Your responsibilities are to:
- Carefully read and understand the user's question.
- Review the following reference examples from Azure AI Search.
- Explain, step by step, how you plan to solve the user's request, referencing the examples where helpful.
- Based on your plan, construct an appropriate SQL query to answer the user's question.
- Pass the SQL query to the execution agent for processing.
- When results are returned by the execution agent, critically review and validate them:
    - Check if the execution agent followed all planning steps and executed the correct SQL query.
    - Ensure the results are correct, complete, and relevant to the user's question.
    - If the execution agent indicates the query is still running or incomplete, instruct the execution agent to run the SQL query again.
    - If everything is correct, explicitly state your approval.
    - If there are any issues (e.g., missing steps, incorrect SQL, incomplete or irrelevant results), explain what is wrong and provide specific feedback for correction.

User question:
{user_input}

Reference examples:
{cedemo}

Your step-by-step plan:
(Explain here)

SQL query:
(Write the SQL query here)



Your validation and feedback:
- Analysis:
  (Describe how you checked the steps, SQL, and results.)
- Feedback:
  (State approval, ask for re-execution if needed, or provide clear, actionable corrections.)
"""
    ).format(user_input=user_input, cedemo=state["cedemo"])



async def cedemo_validation_prompt_template(state):
    # user_input = state["messages"][0].content
    for message in state["messages"]:
        # if message.role == "user":
        #     user_input = message.content
        if isinstance(message,HumanMessage):
            user_input = message.content
    docs = await cedemo_search(user_input)
    contents = [d.page_content for d in docs]
    examples = "\n".join(contents)
    state["cedemo"] = f"These are sample examples from Azure AI Search. Use them as reference only:\n{examples}"

    # Try to get from state, else extract from latest ToolMessage
    plan = state.get("plan", "(No plan found in state)")
    sql_query = state.get("sql_query")
    execution_result = state.get("execution_result")

    # If not present, extract from latest ToolMessage
    if sql_query is None or execution_result is None:
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and msg.name == "cedemo_agent":
                tool_content = msg.content if hasattr(msg, "content") else str(msg)
                # Extract SQL query
               
                # Extract results (everything after </sqlquery>)
                execution_result = tool_content
                break
        else:
            sql_query = sql_query or "(No SQL query found in state or messages)"
            execution_result = execution_result or "(No execution result found in state or messages)"

    return ChatPromptTemplate.from_template(
        """
        You are the CEDEMO validation agent.
        1. Review the user's question and the reference examples from Azure AI Search.
        2. Review the step-by-step plan and SQL query generated by the planning agent.
        3. Check if the execution agent followed all planning steps and executed the correct SQL query.
        4. Validate the result returned by the execution agent.
        5. If there are any issues, provide feedback for correction.

        User question: {user_input}

        Reference examples:
        {cedemo}

        Planning agent's step-by-step plan:
        {plan}

        SQL query generated:
        {sql_query}

        Execution agent's result:
        {execution_result}

        Your validation and feedback:
        (Write your validation here)
        """
    ).format(
        user_input=user_input,
        cedemo=state["cedemo"],
        plan=plan,
        sql_query=sql_query,
        execution_result=execution_result
    )

def extract_cedemo_execution(state):
    """
    Extracts the SQL query and execution result from the latest ToolMessage for query_cedemo_db.
    Returns (sql_query, execution_result, full_result_str)
    """
    sql_query = state.get("sql_query")
    execution_result = state.get("execution_result")
    full_result_str = state.get("cedemo_execution_result")
    print(state,"cedemo_execution_result")
    if sql_query is None or execution_result is None or full_result_str is None:
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and msg.name == "cedemo_agent":
                print(msg)
                tool_content = msg.content if hasattr(msg, "content") else str(msg)
                # Extract SQL query
               
                
               
                full_result_str = tool_content
                break
        else:
            sql_query = sql_query or "(No SQL query found in state or messages)"
            execution_result = execution_result or "(No execution result found in state or messages)"
            full_result_str = full_result_str or "(No CEDEMO execution result found in state or messages)"
    return sql_query, execution_result, full_result_str



async def oamscm_prompt_template(state):
    for message in state["messages"]:
        # if message.role == "user":
        #     user_input = message.content
        if isinstance(message,HumanMessage):
            user_input = message.content
    # user_input = state["messages"][0].content
    docs = await oamscm_search(user_input)
    examples = "\n".join([doc.page_content for doc in docs])
    state["oamscm"] = f"These are sample examples from Azure AI Search. Use them as reference only:\n{examples}"
    cedemo_result = state.get("cedemo_execution_result", "(No CEDEMO execution result found in state)")

    # Try to get from state, else extract from latest ToolMessage
    sql_query = state.get("sql_query")
    execution_result = state.get("execution_result")
    sql_query1, execution_result1, cedemo_result = extract_cedemo_execution(state)

    if sql_query is None or execution_result is None:
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage) and msg.name == "query_oamscm_db":
                tool_content = msg.content if hasattr(msg, "content") else str(msg)
                sql_match = re.search(r"<sqlquery>\s*(.*?)\s*</sqlquery>", tool_content, re.DOTALL | re.IGNORECASE)
                sql_query = sql_match.group(1).strip() if sql_match else "(No SQL query found)"
                results_match = re.search(r"</sqlquery>\s*Results:\s*(.*)", tool_content, re.DOTALL | re.IGNORECASE)
                execution_result = results_match.group(1).strip() if results_match else "(No execution result found)"
                break
        else:
            sql_query = sql_query or "(No SQL query found in state or messages)"
            execution_result = execution_result or "(No execution result found in state or messages)"

    return ChatPromptTemplate.from_template(
      """
You are the OAMSCM planning and validation agent.
Your responsibilities are to:
1. Carefully read and understand the user's question.
2. Review the following reference examples from Azure AI Search.
3. Review the results returned by the CEDEMO execution agent (these may be required for your query).
4. Explain, step by step, how you plan to solve the user's request, referencing the examples and CEDEMO results where helpful.
5. Based on your plan, construct an appropriate SQL query that uses the CEDEMO results if needed.
6. Pass the SQL query to the OAMSCM execution agent for processing.
7. If the OAMSCM execution agent responds that the query is still executing, incomplete, or did not return results, instruct the execution agent to run the SQL query again until results are returned.
8. Once results are available, validate them:
   - Check if the execution agent followed all planning steps and executed the correct SQL query.
   - Ensure the results are correct, complete, and relevant to the user's question.
   - If everything is correct, explicitly state your approval.
   - If there are any issues (e.g., missing steps, incorrect SQL, incomplete or irrelevant results), explain what is wrong and provide specific feedback for correction.

User question:
{user_input}

Reference examples:
{oamscm}

CEDEMO execution agent's result:
{cedemo_result}

Your step-by-step plan:
(Explain here)

SQL query:
{sql_query}

Your validation and feedback:
- Analysis:
  (Describe how you checked the steps, SQL, and results.)
- Feedback:
  (State approval, ask for re-execution if needed, or provide clear, actionable corrections.)
"""
    ).format(user_input=user_input, oamscm=state["oamscm"], cedemo_result=cedemo_result, sql_query=sql_query)

async def oamscm_validation_prompt_template(state):
    # user_input = state["messages"][0].content
    for message in state["messages"]:
        # if message.role == "user":
        #     user_input = message.content
        if isinstance(message,HumanMessage):
            user_input = message.content
    docs = await oamscm_search(user_input)
    examples = "\n".join([doc.page_content for doc in docs])
    state["oamscm"] = f"These are sample examples from Azure AI Search. Use them as reference only:\n{examples}"
    plan = state.get("plan", "(No plan found in state)")
    sql_query = state.get("sql_query")
    execution_result = state.get("execution_result")
    cedemo_result = state.get("cedemo_execution_result", "(No CEDEMO execution result found in state)")
    sql_query1, execution_result1, cedemo_result = extract_cedemo_execution(state)
    # If not present, extract from latest ToolMessage
    if sql_query is None or execution_result is None:
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage) and msg.name == "query_oamscm_db":
                tool_content = msg.content if hasattr(msg, "content") else str(msg)
                sql_match = re.search(r"<sqlquery>\s*(.*?)\s*</sqlquery>", tool_content, re.DOTALL | re.IGNORECASE)
                sql_query = sql_match.group(1).strip() if sql_match else "(No SQL query found)"
                results_match = re.search(r"</sqlquery>\s*Results:\s*(.*)", tool_content, re.DOTALL | re.IGNORECASE)
                execution_result = results_match.group(1).strip() if results_match else "(No execution result found)"
                break
        else:
            sql_query = sql_query or "(No SQL query found in state or messages)"
            execution_result = execution_result or "(No execution result found in state or messages)"

    return ChatPromptTemplate.from_template(
        """
        You are the OAMSCM validation agent.
        1. Review the user's question and the reference examples from Azure AI Search.
        2. Review the step-by-step plan and SQL query generated by the planning agent.
        3. Review the results returned by the CEDEMO execution agent (these may be required for your query).
        4. Check if the OAMSCM execution agent followed all planning steps, used the CEDEMO results if needed, and executed the correct SQL query.
        5. Validate the result returned by the OAMSCM execution agent.
        6. If there are any issues, provide feedback for correction.

        User question: {user_input}

        Reference examples:
        {oamscm}

        CEDEMO execution agent's result:
        {cedemo_result}

        Planning agent's step-by-step plan:
        {plan}

        SQL query generated:
        {sql_query}

        OAMSCM execution agent's result:
        {execution_result}

        Your validation and feedback:
        (Write your validation here)
        """
    ).format(
        user_input=user_input,
        oamscm=state["oamscm"],
        cedemo_result=cedemo_result,
        plan=plan,
        sql_query=sql_query,
        execution_result=execution_result
    )


# --- Swarm for CEDEMO ---
cedemo_plan = create_react_agent(
    model=model,
    tools=[transfer_to_cedemo_execution],
    prompt=cedemo_prompt_template,
    name="cedemo_plan",
)
cedemo_validation = create_react_agent(
    model=model,
    tools=[transfer_to_cedemo_execution, transfer_to_cedemo_plan],
    prompt=cedemo_validation_prompt_template,
    name="cedemo_validation",
)
   # imported from supervisor

cedemo_swarm = create_swarm(
    agents=[cedemo_plan, cedemo_validation, cedemo_agent],
    default_active_agent="cedemo_plan"
).compile(name="cedemo_swarm")

# --- Swarm for OAMSCM ---
oamscm_plan = create_react_agent(
    model=model,
    tools=[transfer_to_oamscm_execution],
    prompt=oamscm_prompt_template,
    name="oamscm_plan",
)
oamscm_validation = create_react_agent(
    model=model,
    tools=[transfer_to_oamscm_execution, transfer_to_oamscm_plan],
    prompt=oamscm_validation_prompt_template,
    name="oamscm_validation",
)
  # imported from supervisor

oamscm_swarm = create_swarm(
    agents=[oamscm_plan, oamscm_validation, oamscm_agent],
    default_active_agent="oamscm_plan"
).compile(name="oamscm_swarm")


class SupervisorState(MessagesState, total=False):
    remaining_steps: int
    messages: Annotated[list[AnyMessage], add_messages]
    cedemo_execution_result: str
    oamscm_execution_result: str
    cedemo: str
    oamscm: str
    plan: str
    sql_query: str
    execution_result: str
    user_context: dict[str, str]
    # extra_args:str
    
# --- Supervisor Orchestrator ---
supervisor = create_supervisor(
    agents=[cedemo_swarm, oamscm_swarm],
    model=model,
    prompt=supervisor_prompt,
    state_schema=SupervisorState,
).compile()



if __name__ == "__main__":
    async def main():
        async for chunk in supervisor.astream({
                "messages": [
                    {
                        "role": "user",
                        "content": "what are the covered tasks required for work desc Install Dead Main Plastic" 
                    }
                ]
            }, subgraphs=True):
            pretty_print_messages(chunk)
      
            print("\n")
    asyncio.run(main())
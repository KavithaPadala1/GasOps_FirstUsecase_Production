# cedemodb_agent.py code

from typing import TypedDict
from langgraph.prebuilt import create_react_agent 
from agents.azure_llm import load_azureopenai_llm_client  # importing the Azure openai client 
from agents.tools.cedemodb_query_execution import query_cedemo_db
from agents.utils.abbreviations import ABBREVIATIONS_DICT
import datetime


from langgraph_supervisor import create_handoff_tool # importing the create_handoff_tool function


# handoff tool for transferring to the cedemo plan agent
transfer_to_cedemo_plan = create_handoff_tool(
    agent_name="cedemo_plan",
    description="Transfer to CEDEMO plan agent."
)
# initializing Azure openAI 
model = load_azureopenai_llm_client()

# loading cedemo schema
with open('agents/schemas/schema_CEDEMONEW0314.txt', 'r') as file:
    schema = file.read()

# Format abbreviation dictionary into prompt-friendly string
abbreviations_prompt = "\n".join([f"- {abbr}: {full}" for abbr, full in ABBREVIATIONS_DICT.items()])

# Get current year dynamically
current_year = datetime.datetime.now().year

cedemo_agent = create_react_agent(
    model=model,
    tools=[query_cedemo_db],
    name="cedemo_agent",
    
    prompt=f"""
You are an expert in generating accurate Azure SQL queries and executing them using tools for the user question.

### Schema:
Only use these exact table and column names — no spelling changes, no assumptions, no corrections:
{schema}

### Abbreviations:
You may encounter these abbreviations in user queries. Always expand and interpret them correctly:
{abbreviations_prompt}

### Task:
1. **Generate a valid and executable Azure SQL query based on the user question.**
2. **Pass the generated SQL query to the `query_cedemo_db` tool for execution.**
3. Wait for the tool to return the results.
4. Return both the generated SQL query and the results.

### AI Search Example Enforcement:
- **Always refer to the AI Search example queries for SQL structure, logic, and especially the columns in the SELECT clause. Only include columns present in the example unless the user explicitly requests otherwise.**

### Enforcement:
- **Tool Invocation Required**: After writing the SQL, you must immediately call the `query_cedemo_db` tool with the SQL as input. Do not return any response until the tool's output is included.**
- Do NOT print the SQL alone. Without tool invocation, it will not be executed.
- **If you output a SQL query without invoking the tool, you will be prompted to do so again.**
- Return the AI Message only after the tool completes execution.

### Rules:
- **General SQL Rules:**
    - Never use any data-modifying or schema-altering SQL commands (DELETE, INSERT, UPDATE, TRUNCATE, MERGE, CREATE, DROP, ALTER, ADD, RENAME). Only use SELECT statements.
    - Use only table/column names exactly as shown in the schema.
    - Always consider only active records. Apply `WHERE IsActive = 1` and `WHERE IsDeleted = 0` if those columns exist.
    - Never display these columns 'WorkActivityFunctionID' , 'ContractorRouteSheetTicketDetailsID','IsActive','VendorCode', 'WorkOrderID' , 'ContractorRouteSheetWorkDescriptionID' , 'IsDeleted'and 'VenderCode' to user.
    - For multi-row subqueries, use `IN`.
    - If the user didn't mention the year for the date, always consider current year '{current_year}'.
    - Do not change or fabricate the results data.
- **Never assume VenderCode/VendorCode = ContractorDisplayName directly without lookup.**
- **If the user provides a ContractorDisplayName (e.g., 'CAC', 'ECI', 'BANCKER'), first look up the corresponding VenderCode/VendorCode from the ContractorMaster table, then use that VenderCode in your query. Never assume ContractorDisplayName equals VenderCode/VendorCode.**
- When querying the 'Region' column:
    - Map 'X' to 'Bronx', 'M' to 'Manhattan', 'Q' to 'Queens', and 'W' to 'Westchester'.
    - If the user mentions a region name (e.g., 'Bronx'), translate it into the correct region code ('X') before filtering. And never display the region code user always display the region name.
- **Do not alias the ITSID column in the query. Employee ID refers to ITSID.**
- The terms 'job Description' and 'WorkDescription' are the same.
- **Always use the LIKE operator for the 'WorkDescription' column. Example: `WorkDescription LIKE '%Service Transfers%'`**
- Requirements refer to the corresponding TaskNum and TaskDesc.
- **If the user asks about the requirements for a Work Description/job description (e.g., 'Backfill/Excavate, Service Transfers'), fetch the corresponding WorkActivityFunctionID for the WorkDescription. After executing, always pass the WorkActivityFunctionID(s) to the oamscm agent to get the TaskNum and TaskDesc.**
- **If the user asks about qualified, not qualified, or flagged employees for a WorkDescription, ONLY generate the SQL to get the WorkActivityFunctionID(s) for the WorkDescription. Do NOT join with employee tables or filter by employee status. After executing, always pass the WorkActivityFunctionID(s) to the oamscm agent for further employee lookup.**

"""
)

# Planning_and_Validation_cedemo_agent code

class PlanState(TypedDict):
    instructions: str
    agent_name: str

planning_and_validation_cedemo_agent = create_react_agent(
    model=model,  # No bind_tools since no tool calls are made
    name="planning_and_validation_cedemo_agent",
    tools=[],  # No tools since response is returned as PlanState
    # response_format=PlanState,
    prompt=f"""
You are the planning and validation agent for CEDEMO queries. Your role is to:

1. Receive user input and plan how to query the database to fulfill the request.
2. Generate instructions, including the SQL query, for the execute_cedemo agent.
3. Validate the results returned by execute_cedemo.
4. Decide whether to transfer the results to supervisor_expert or send back to execute_cedemo for refinement.

Instead of performing tool calls, you must return a response in the following format:
- **instructions**: A string containing clear instructions, including the exact SQL query (if applicable) or guidance for the next agent.
- **agent_name**: The name of the agent to transfer to, either 'execute_cedemo' or 'supervisor_expert'.

You cannot end the process yourself; you must always specify an agent_name to transfer to.

### Schema:
Only use these exact table and column names — no spelling changes, no assumptions, no corrections:
{schema}

### Abbreviations:
You may encounter these abbreviations in user queries. Always expand and interpret them correctly:
{abbreviations_prompt}

### AI Search Example Enforcement:
- **Always refer to the AI Search example queries for SQL structure, logic, and especially the columns in the SELECT clause. Only include columns present in the example unless the user explicitly requests otherwise.**

### Rules for Planning the Query:
- **General SQL Rules:**
    - Never use any data-modifying or schema-altering SQL commands (DELETE, INSERT, UPDATE, TRUNCATE, MERGE, CREATE, DROP, ALTER, ADD, RENAME). Only use SELECT statements.
    - Use only table/column names exactly as shown in the schema.
    - Always consider only active records. Apply `WHERE IsActive = 1` and `WHERE IsDeleted = 0` if those columns exist.
    - **Never display these columns 'WorkActivityFunctionID' , 'ContractorRouteSheetTicketDetailsID','IsActive','VendorCode', 'WorkOrderID' , 'ContractorRouteSheetWorkDescriptionID' , 'IsDeleted'and 'VenderCode' to user.**
    - For multi-row subqueries, use `IN`.
    - If the user didn't mention the year for the date, always consider current year '{current_year}'.
    - Do not change or fabricate the results data.
- **Never assume VenderCode/VendorCode = ContractorDisplayName directly without lookup.**
- **If the user provides a ContractorDisplayName (e.g., 'CAC', 'ECI', 'BANCKER'), first look up the corresponding VenderCode/VendorCode from the ContractorMaster table, then use that VenderCode in your query. Never assume ContractorDisplayName equals VenderCode/VendorCode.**
- When querying the 'Region' column:
    - Map 'X' to 'Bronx', 'M' to 'Manhattan', 'Q' to 'Queens', and 'W' to 'Westchester'.
    - If the user mentions a region name (e.g., 'Bronx'), translate it into the correct region code ('X') before filtering. And never display the region code user always display the region name.
- **Do not alias the ITSID column in the query. Employee ID refers to ITSID.**
- The terms 'job Description' and 'WorkDescription' are the same.
- **Always use the LIKE operator for the 'WorkDescription' column. Example: `WorkDescription LIKE '%Service Transfers%'`**
- Requirements refer to the corresponding TaskNum and TaskDesc.
- **If the user asks about the requirements for a Work Description/job description (e.g., 'Backfill/Excavate, Service Transfers'), fetch the corresponding WorkActivityFunctionID for the WorkDescription. After executing, always pass the WorkActivityFunctionID(s) to the oamscm agent to get the TaskNum and TaskDesc.**
- **If the user asks about qualified, not qualified, or flagged employees for a WorkDescription, ONLY generate the SQL to get the WorkActivityFunctionID(s) for the WorkDescription. Do NOT join with employee tables or filter by employee status. After executing, always pass the WorkActivityFunctionID(s) to the oamscm agent for further employee lookup.**

### Generating Instructions for execute_cedemo:
- Based on the user's request and the rules above, formulate the SQL query that execute_cedemo should run.
- Include the exact SQL query in the `instructions` field, along with any additional guidance (e.g., context or specific requirements).
- Set `agent_name` to 'execute_cedemo' when transferring to execute_cedemo.

### Validating Results:
- When execute_cedemo returns the results and the SQL query, verify that:
  - The executed query adheres to the rules (e.g., only SELECT, correct table/column names, active records considered).
  - The results accurately fulfill the user's original request.
  - The data is correct and complete.
- If the results are satisfactory:
  - Set `instructions` to include the validated results and the executed query for reference.
  - Set `agent_name` to 'supervisor_expert'.
- If the results need refinement (e.g., incorrect data, missing information, query errors):
  - Set `instructions` to include a revised SQL query or specific guidance on how to adjust the query.
  - Set `agent_name` to 'execute_cedemo'.
- If no results are found, give instructions to supervisor saying the query may be routed wrongly and suggest trying in oamscm agent before passing it to user. Always pass this info in instructions saying this is more about oamscm agent.
### Response Format:
Always return a response in the following format:
```json

  'instructions': 'SQL query or guidance for the next agent, if user question is not related to cedemo agent **always say try in oamscm agent as query not related cedemo agent**',
  'agent_name': 'execute_cedemo or supervisor_expert'

```
"""
)

## cedemodb_query_execution.py code

from urllib.parse import quote_plus
from langchain.schema import AIMessage # type: ignore




import logging 
import os
import re
from collections.abc import Sequence
from functools import partial
from typing import (
    Annotated,
    Any,
    Callable,
    Literal,
    Optional,
    TypedDict,
    Union,
    cast,
)

from langchain_core.messages import (
    AnyMessage,
    BaseMessage,
    BaseMessageChunk,
    MessageLikeRepresentation,
    RemoveMessage,
    convert_to_messages,
    message_chunk_to_message,
)
from typing_extensions import Literal

from langgraph.prebuilt import create_react_agent
from typing import Annotated
from langgraph.graph import MessagesState, StateGraph, START,END
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

from langgraph.graph import add_messages



import logging
import operator


from langchain_core.messages import AIMessage,HumanMessage,ToolMessage


from langchain_core.messages import convert_to_messages


from dotenv import load_dotenv
import os
import re
import pandas as pd
# import pymssql
from sqlalchemy import create_engine 
# from ..utils.logging_config import setup_logging
import logging
# from langchain_core.tools import tool # type: ignore
import pyodbc

load_dotenv()



logger = logging.getLogger(__name__)




SERVER = os.getenv("SERVER")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
USERNAME = 'QuadrantAIUser'


# === Database Functions ===



# @tool(return_direct=True)
@tool("query_cedemo_db")
def query_cedemo_db(query: str,state: Annotated[MessagesState, InjectedState]) -> str:
    """
    Query CEDEMO Database for ContactorRouteSheetTicketDeatils , Contractor Assigned Employee Details, Contractor RouteSheet Work description and Contactor routeSheet Work Description to work activity function mapping details.
    Extracts SQL from markdown if needed, runs query, and returns formatted result.
    """
    # logging.info(f"\n\n Executing Generated SQL Query: {query} \n\n")
    
    logger.debug("Received query.")
    
    messages = state["messages"]
    Database_CEDEMO = 'no Database_Name found from token'  # Default value
    
    for message in messages:
        if hasattr(message, 'content'):
            content = str(message.content)
        else:
            content = str(message)
        
        # Regex pattern to match Database_Name parameter
        db_pattern = r"'Database_Name':\s*'([^']+)'"
        match = re.search(db_pattern, content)
        
        if match:
            Database_CEDEMO = match.group(1)
            logger.info(f"Extracted Database_Name: {Database_CEDEMO}")
            break

    

    try:
        # Extract SQL from markdown format
        match = re.search(r"```sql\s*(.*?)```", query, re.DOTALL | re.IGNORECASE)
        extracted_query = match.group(1).strip() if match else query
        logger.info(f"Extracted SQL query:\n{extracted_query}")
        logger.info(f"Connecting to {SERVER} with database {Database_CEDEMO} to execute the SQL Query.")
        results = execute_sql_query(extracted_query, DATABASE_CEDEMO=Database_CEDEMO)

        if isinstance(results, str):  # Error string returned
            logger.error(f"SQL execution error: {results}")
            return f"Error: {results}"

        results_str = results.to_string(index=False) if not results.empty else "No results found."
        logger.info("Query executed successfully and results formatted.")


        return f"""
    Generated SQL Query:
    <sqlquery>
    {extracted_query}
    </sqlquery>
    Results:
    {results_str}
    """
    
    except Exception as e:
        error_msg = f"Unexpected error occurred: {str(e)}"
        logger.exception(error_msg)
        return f"Error: {error_msg}"
   

# === SQL Execution Helper ===

# sql_query = """SELECT DISTINCT crswf.WorkActivityFunctionID
# FROM ContractorRouteSheetWorkDescription AS crswd
# JOIN ContractorRouteSheetWorkDescriptiontoWAFMap AS crswf
#   ON crswd.ContractorRouteSheetWorkDescriptionID = crswf.ContractorRouteSheetWorkDescriptionID
# WHERE crswd.WorkDescription LIKE '%Excavate%' AND crswf.IsActive = 1;""" 

def execute_sql_query(sql_query: str,DATABASE_CEDEMO: str = "CEDEMO") -> Union[pd.DataFrame, str]:
    """
    Executes a SQL query against the CEDEMO database using ODBC connection.
    Returns DataFrame or error string.
    """
    try:
        logger.debug(f"Attempting to connect to {DATABASE_CEDEMO} DB using ODBC.")

        conn_str = (
            # "DRIVER={ODBC Driver 18 for SQL Server};"
            "DRIVER={FreeTDS};" 
            f"SERVER={SERVER};"
             "PORT=1433;"
            f"DATABASE={DATABASE_CEDEMO};"
            f"UID={USERNAME};"
            f"PWD={PASSWORD};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )
        logger.info(f"Connecting to {SERVER} with database {DATABASE_CEDEMO}.")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        logger.info(f"Connected to {SERVER} with database {DATABASE_CEDEMO}.")
        logger.info("Connected to DB via ODBC. Executing query.")
        logger.debug(f"Executing SQL query: {sql_query}")
        cursor.execute(sql_query)
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchall()
        # Ensure each row is a tuple and shape matches columns
        if data and len(columns) > 1 and len(data[0]) != len(columns):
            logger.error(f"Shape mismatch: columns={columns}, data={data}")
            raise ValueError(f"Shape of passed values is {len(data), len(data[0])}, indices imply ({len(data)}, {len(columns)})")
        df = pd.DataFrame.from_records(data, columns=columns)
        cursor.close()
        conn.close()
        logger.info("Query executed and connection closed.")
        return df
    except Exception as e:
        error_msg = f"Error executing SQL query: {str(e)}"
        logger.exception(error_msg)
        return error_msg

    #     columns = [column[0] for column in cursor.description]
    #     data = cursor.fetchall()
    #     df = pd.DataFrame(data, columns=columns)
    #     cursor.close()
    #     conn.close()
    #     logger.info("Query executed and connection closed.")
    #     return df

    # except Exception as e:
    #     error_msg = f"Error executing SQL query: {str(e)}"
    #     logger.exception(error_msg)
    #     return error_msg


# execute_sql_query(sql_query)



@tool("transfer_from_plan_cedemo")
def transfer_from_plan_cedemo(
    agent_name: str,
    state: Annotated[dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
):
    """Transfer to another agent.

    Args:
        agent_name (str): The name of the agent to transfer to ('execute_cedemo' or 'supervisor_expert').
        state (dict): The current state of the graph.
        tool_call_id (str): The ID of the tool call.

    Returns:
        Command: A command to navigate to the specified agent with updated state.
    """
    # print("Execute cedemo",agent_name,state,tool_call_id)
    # print("state messages",state["messages"])
    valid_agents = ["execute_cedemo", 'supervisor_expert']
    if agent_name not in valid_agents:
        raise ValueError(f"Invalid agent name: {agent_name}. Must be one of {valid_agents}")
    tool_message = {
        "role": "tool",
        "content": f"Successfully transferred to {agent_name}",
        "name": "transfer_to_agent",
        "tool_call_id": tool_call_id,
    }
    
    
    return Command(
        goto=agent_name,
        graph=Command.PARENT,
        update={"messages": state["messages"] + [tool_message]},
    )





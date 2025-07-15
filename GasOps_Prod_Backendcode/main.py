from supervisor_orchestration import supervisor
from fastapi import FastAPI, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import uuid, secrets, logging
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import re
from decryption import decode  # Import decode from app.py's decryption module
import json
from pydantic import BaseModel
from typing import List, Optional, Dict
from llm_validator import llm_validate_response

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)  # Set to DEBUG for detailed logging
logger = logging.getLogger(__name__)


# Suppress noisy INFO logs from httpx and azure
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)

# Optional function to persist chat externally
def update_chat(session_id, role, content):
    pass

class Message(BaseModel):
    role: str
    content: str

class AskRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    token: Optional[str] = None
    prev_msgs: Optional[List[Message]] = None

@app.post("/ask")
async def ask(
    body: AskRequest,
    encoded_string: str = Header(...)
):
    query = body.query
    session_id = body.session_id
    token = body.token
    prev_msgs = body.prev_msgs
    # No session management, just process the incoming query
    try:
        update_chat(session_id, "user", query)
    except Exception as e:
        logger.error(f"Failed to update chat with user message: {e}")

    # Decode token to append user context (similar to app.py)
    decrypted_data = {}
    if token:
        try:
            decrypted_data = decode(token)
            logger.debug(f"Decoded token: {decrypted_data}")
        except Exception as e:
            logger.error(f"Failed to decode token: {e}")

    # Build full message history: previous + current user message
    full_messages = []
    print(f"Previous messages: {prev_msgs}")
    if prev_msgs:
        for msg in prev_msgs:  # Reverse to maintain order from oldest to newest
            # Only add previous messages, do not append the current user message again
            if isinstance(msg, dict):
                # Ensure content is always a string
                content = str(msg["content"]) if not isinstance(msg["content"], str) else msg["content"]
                full_messages.append({"role": msg["role"], "content": content})
            elif isinstance(msg, Message):
                content = str(msg.content) if not isinstance(msg.content, str) else msg.content
                full_messages.append({"role": msg.role, "content": content})
    # Always ensure the last message is the current user query (with context)
    if not full_messages or full_messages[-1]["role"] != "user" or full_messages[-1]["content"] != f"{query} {decrypted_data}":
        full_messages.append({
            "role": "user",
            "content": f"{query} {decrypted_data}"
        })
        
        # # Only send current user message with decrypted context
        # full_messages = [{
        #     "role": "user",
        #     "content": f"{query} {decrypted_data}"
        # }]


    # Print/log the user question and previous questions being passed to supervisor agent
    logger.info(f"Passing message history to supervisor agent:")
    # for idx, msg in enumerate(full_messages):
    #     logger.info(f"Message {idx+1}: role={msg['role']}, content={msg['content']}")

    # Call the compiled workflow
    sql_queries = []
    response_text = ""
    max_supervisor_attempts = 2
    for attempt in range(max_supervisor_attempts):
        try:
            # Collect all chunks to process the final result, similar to app.py
            chunks = []
            print(f"Full messages being sent to supervisor: {full_messages}")
            async for chunk in supervisor.astream({"messages": full_messages}, subgraphs=True):
                logger.debug(f"Chunk received: {chunk}")
                chunks.append(chunk)
                # Extract SQL queries from ToolMessages in any chunk
                if isinstance(chunk, tuple):
                    ns, update = chunk
                    logger.debug(f"Subgraph update from {ns}: {update}")
                    for node_name, node_update in update.items():
                        if "messages" in node_update:
                            for msg in node_update["messages"]:
                                if isinstance(msg, ToolMessage):
                                    if msg.name == 'query_cedemo_db':
                                        match = re.search(r"<sqlquery>(.*?)</sqlquery>", msg.content, re.DOTALL)
                                        if match:
                                            sql_queries.append({"db": "TokenDB", "query": match.group(1).strip()})
                                    elif msg.name == 'query_oamscm_db':
                                        match = re.search(r"<sqlquery>(.*?)</sqlquery>", msg.content, re.DOTALL)
                                        if match:
                                            sql_queries.append({"db": "OAMSCM", "query": match.group(1).strip()})
                else:
                    for node_name, node_update in chunk.items():
                        if "messages" in node_update:
                            for msg in node_update["messages"]:
                                if isinstance(msg, ToolMessage):
                                    if msg.name == 'query_cedemo_db':
                                        match = re.search(r"<sqlquery>(.*?)</sqlquery>", msg.content, re.DOTALL)
                                        if match:
                                            sql_queries.append({"db": "TokenDB", "query": match.group(1).strip()})
                                    elif msg.name == 'query_oamscm_db':
                                        match = re.search(r"<sqlquery>(.*?)</sqlquery>", msg.content, re.DOTALL)
                                        if match:
                                            sql_queries.append({"db": "OAMSCM", "query": match.group(1).strip()})

            # Process the final chunk, similar to app.py's process_graph
            if chunks:
                final_chunk = chunks[-1]
                final_result = {}
                if isinstance(final_chunk, tuple):
                    logger.debug(f"Final chunk is tuple: {final_chunk}")
                    final_result = final_chunk[1].get('supervisor', {})
                else:
                    logger.debug(f"Final chunk is dict: {final_chunk}")
                    final_result = final_chunk.get('supervisor', final_chunk.get('supervisor_expert', {}))

                logger.debug(f"Final result: {final_result}")
                if "messages" in final_result and final_result["messages"]:
                    last_message = final_result["messages"][-1]
                    if isinstance(last_message, AIMessage) and last_message.content:
                        response_text = last_message.content
                        logger.debug(f"Extracted AIMessage content: {response_text}")
                    else:
                        logger.warning(f"Last message is not a valid AIMessage: {last_message}")

            # Fallback response for generic queries
            if not response_text:
                logger.warning("No valid AIMessage found in supervisor output")
                if query.lower() in ["hi", "hii", "hello"]:
                    response_text = "Hello! How can I assist you with GasOps compliance or ticket assignments?"
                else:
                    response_text = "I'm sorry, I couldn't generate a response. Please provide more details or ask about GasOps compliance, ticket assignments, or ITSID."

        except Exception as e:
            logger.error(f"Error during LLM invocation: {str(e)}", exc_info=True)
            response_text = f"Sorry, something went wrong while generating a response: {str(e)}"
        # Validate with LLM
        print(f"Validating response: {response_text} \n\n\n")
        is_valid = await llm_validate_response(query, response_text, max_attempts=2)
        if is_valid:
            break
        else:
            logger.warning(f"Supervisor response unsatisfactory, retrying (attempt {attempt+1})...")
            response_text = ""  # Clear response_text to force retry
    else:
        response_text = "Sorry, Please try again later."

    # Save assistant response (no session history, just return response)
    timestamp_bot = datetime.utcnow().isoformat()
    try:
        update_chat(session_id, "assistant", response_text)
    except Exception as e:
        logger.error(f"Failed to update chat with assistant response: {e}")

    return {
        "response": response_text,
        "timestamp": timestamp_bot,
        "context": [
            {"role": "user", "content": query, "timestamp": timestamp_bot},
            {"role": "assistant", "content": response_text, "timestamp": timestamp_bot}
        ],
        "user_details": {
            "session_id": session_id,
            "token": token
        },
        "sql_queries": sql_queries
    }


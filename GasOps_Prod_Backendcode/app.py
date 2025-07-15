# # app.py code
# import streamlit as st
# import os
# import re
# import json
# import logging
# import asyncio
# from concurrent.futures import ThreadPoolExecutor
# # from workflow import graph
# from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
# from agents.utils.logging_config import setup_logging
# from latency_handler import LatencyCallbackHandler
# from decryption import decode
# from langchain_core.messages import convert_to_messages
# from test import supervisor


# # Setup logging
# setup_logging(log_file="gasops.log")
# logger = logging.getLogger(__name__)
# logger.info("Streamlit started")

# noisy_loggers = ["httpcore", "httpx", "urllib3", "openai", "langsmith", "azure"]
# for logger_name in noisy_loggers:
#     logging.getLogger(logger_name).setLevel(logging.WARNING)

# # Chat history file path
# HISTORY_FILE = "chat_sessions.json"

# # Streamlit page config
# st.set_page_config(page_title="GasOps Worker Compliance Verification System", layout="wide")

# # CRITICAL: Initialize messages first, before anything else
# if "messages" not in st.session_state:
#     st.session_state["messages"] = []

# # Initialize other session state variables
# if "chat_sessions" not in st.session_state:
#     if os.path.exists(HISTORY_FILE):
#         try:
#             with open(HISTORY_FILE, "r") as f:
#                 data = json.load(f)
#                 st.session_state["chat_sessions"] = data.get("chat_sessions", [])
#                 st.session_state["session_titles"] = data.get("session_titles", [])
#         except Exception as e:
#             logger.error(f"Error loading chat history: {str(e)}")
#             st.session_state["chat_sessions"] = []
#             st.session_state["session_titles"] = []
#     else:
#         st.session_state["chat_sessions"] = []
#         st.session_state["session_titles"] = []

# if "session_index" not in st.session_state:
#     st.session_state["session_index"] = 0

# # Now try to load messages from chat_sessions if available
# if len(st.session_state["messages"]) == 0:  # Only if messages is empty
#     try:
#         if (len(st.session_state["chat_sessions"]) > 0 and 
#             st.session_state["session_index"] < len(st.session_state["chat_sessions"])):
#             st.session_state["messages"] = st.session_state["chat_sessions"][st.session_state["session_index"]]
#     except Exception as e:
#         logger.error(f"Error loading messages from chat_sessions: {str(e)}")
#         # Keep the empty messages list we initialized earlier

# # Sidebar - Chat History
# st.sidebar.title("Chat History")

# # New Chat button
# if st.sidebar.button("New Chat"):
#     try:
#         if len(st.session_state["messages"]) > 0:
#             # Save current chat if it exists
#             if st.session_state["session_index"] < len(st.session_state["chat_sessions"]):
#                 st.session_state["chat_sessions"][st.session_state["session_index"]] = st.session_state["messages"]
#             else:
#                 st.session_state["chat_sessions"].append(st.session_state["messages"])
#                 first_msg = next((m["content"] for m in st.session_state["messages"] if m["role"] == "user"), "Untitled")
#                 st.session_state["session_titles"].append(first_msg[:30])
            
#             # Save to file
#             with open(HISTORY_FILE, "w") as f:
#                 json.dump({
#                     "chat_sessions": st.session_state["chat_sessions"],
#                     "session_titles": st.session_state["session_titles"]
#                 }, f)
        
#         # Reset messages and update session index
#         st.session_state["messages"] = []
#         st.session_state["session_index"] = len(st.session_state["chat_sessions"])
#         st.rerun()
#     except Exception as e:
#         logger.error(f"Error creating new chat: {str(e)}")
#         st.error(f"Error creating new chat: {str(e)}")

# # Display chat history with unique keys
# try:
#     for i, title in enumerate(st.session_state["session_titles"]):
#         if st.sidebar.button(label=title, key=f"session_button_{i}"):
#             st.session_state["messages"] = st.session_state["chat_sessions"][i]
#             st.session_state["session_index"] = i
#             st.rerun()
# except Exception as e:
#     logger.error(f"Error displaying chat history: {str(e)}")

# # Title and description
# st.title("GasOps Compliance Verification System")
# st.write("Chat with me about ticket assignments, ITSID, and compliance verifications!")

# # Render chat history
# try:
#     for msg in st.session_state["messages"]:
#         with st.chat_message(msg["role"]):
#             st.markdown(msg["content"])
# except Exception as e:
#     logger.error(f"Error rendering chat history: {str(e)}")
#     st.session_state["messages"] = []  # Reset if corrupted

# # Helper function to run async code in a separate thread
# def run_async_in_thread(async_func, *args):
#     def wrapper():
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         return loop.run_until_complete(async_func(*args))
#     with ThreadPoolExecutor(max_workers=1) as executor:
#         future = executor.submit(wrapper)
#         return future.result()

# # Async function to process the graph stream which takes user input and data(token info)
# async def process_graph(user_input,data):
#     # Safety check - Initializes messages in session if it doesn’t exist
#     if "messages" not in st.session_state:
#         st.session_state["messages"] = []
#     print("Previous messages:", st.session_state["messages"])
    
#     # sending only one prev. message for context + the current user message (with appended token data)
#     # if len(st.session_state["messages"]) >= 1:
#     #     print("Previous messages:", st.session_state["messages"])
#     #     last_messages =  st.session_state["messages"][-1:] + [{"role": "user", "content": user_input +" " + str(data)}] 
#     #     st.session_state["messages"].append({"role": "user", "content": user_input})
#     # else:
#     #     last_messages =  [{"role": "user", "content": user_input +" " + str(data)}]
#     #     st.session_state["messages"].append({"role": "user", "content": user_input})
        
    
#     # input_data = {"messages":last_messages}
#     input_data = {"messages": [{"role": "user", "content": user_input + " " + str(data)}]}
#     cedemo_sql = ""
#     oamscm_sql = ""
    
#     try:
#         print("Input data:", input_data)
#         async for chunk in supervisor.astream(input_data, subgraphs=True):
#             pretty_print_messages(chunk)
#             query_oamscm = extract_oamscm(chunk)
#             query_cedemo = extract_cedemo(chunk)
#             if query_oamscm:
#                 oamscm_sql = query_oamscm
#             if query_cedemo:
#                 cedemo_sql = query_cedemo
#             result = chunk  # Keep the last chunk
        
#         backup = result
#         if isinstance(result, tuple):
#             # print("Result is a tuple:", result)
#             final_result = result[1].get('supervisor', {})
#         else:
#             final_result = result.get('supervisor_expert', {})
        
#         return final_result, cedemo_sql, oamscm_sql, backup
#     except Exception as e:
#         logger.error(f"Error in process_graph: {str(e)}", exc_info=True)
#         return {"messages": [{"content": f"Error processing your request: {str(e)}"}]}, "", "", None

# # Helper functions
# def pretty_print_messages(update):
#     try:
#         if isinstance(update, tuple):
#             ns, update = update
#             if len(ns) == 0:
#                 return
#             graph_id = ns[-1].split(":")[0]
#             print(f"Update from subgraph {graph_id}:")
#             print("\n")
#         for node_name, node_update in update.items():
#             print(f"Update from node {node_name}:")
#             print("\n")
#             if node_name != "generate_structured_response":
#                 for m in convert_to_messages(node_update["messages"]):
#                     m.pretty_print()
#             else:
#                 print(node_update)
#             print("\n")
#     except Exception as e:
#         logger.error(f"Error in pretty_print_messages: {str(e)}")

# # Extract CEDEMO SQL query from the messages
# def extract_cedemo(data):
#     sql_query = ""
#     try:
#         if isinstance(data, tuple):
#             _, update = data
#             if 'tools' in update:
#                 messages = update['tools']['messages']
#                 for msg in messages:
#                     if isinstance(msg, ToolMessage) and msg.name == 'query_cedemo_db':
#                         match = re.search(r"<sqlquery>(.*?)</sqlquery>", msg.content, re.DOTALL)
#                         if match:
#                             sql_query = match.group(1).strip()
#     except Exception as e:
#         logger.error(f"Error extracting CEDEMO query: {str(e)}")
#     return sql_query

# # Extract OAMSCM SQL query from the messages
# def extract_oamscm(data):
#     sql_query = ""
#     try:
#         if isinstance(data, tuple):
#             _, update = data
#             if 'tools' in update:
#                 messages = update['tools']['messages']
#                 for msg in messages:
#                     if isinstance(msg, ToolMessage) and msg.name == 'query_oamscm_db':
#                         match = re.search(r"<sqlquery>(.*?)</sqlquery>", msg.content, re.DOTALL)
#                         if match:
#                             sql_query = match.group(1).strip()
#     except Exception as e:
#         logger.error(f"Error extracting OAMSCM query: {str(e)}")
#     return sql_query

# # User input handling
# token = "MSZDRURFTU8wNDE4JkNFREVNTw=="  # user token

# # Ensure messages exists before processing user input
# if "messages" not in st.session_state:
#     st.session_state["messages"] = []

# user_input = st.chat_input("Ask a question...")
# if user_input:
#     logger.info(f"User Question: {user_input}")
#     try:
#         decrypted_data = decode(token)   # decoding the token info.(Decoded token: {'LoginMasterID': '1', 'Database_Name': 'CEDEMONEW0314', 'OrgID': 'CEDEMO'})
#         logger.info(f"Decoded token: {decrypted_data}")
        
#         # Add user message to chat history
#         # st.session_state["messages"].append({"role": "user", "content": user_input + " " + str(decrypted_data)})
#         st.session_state["messages"].append({"role": "user", "content": user_input})

        
#         # Display user message
#         with st.chat_message("user"):
#             st.markdown(user_input)

#         # Process and display assistant response
#         with st.chat_message("assistant"):
#             with st.spinner("Fetching results..."):
#                 try:
#                     handler = LatencyCallbackHandler()
#                     final_result, cedemo_sql, oamscm_sql, backup = run_async_in_thread(process_graph, user_input,decrypted_data)
                    
#                     # Format SQL queries if any
#                     sql_queries = []
#                     if cedemo_sql:
#                         sql_queries.append(("CEDEMO", cedemo_sql))
#                     if oamscm_sql:
#                         sql_queries.append(("OAMSCM", oamscm_sql))
                    
#                     # Extract response content
#                     # print("Final result:", final_result)
#                     if "messages" in final_result and final_result["messages"]:
#                         # print("Final result:", final_result)
                        
                        
#                         response_content = final_result["messages"][-1].content
#                         # response_content = final_result["messages"][-1].get("content", "No content available.")
#                         # logger.debug(f"final_result['messages']: {final_result['messages']}")
#                         # print("Response content:", response_content)
#                         st.session_state["messages"].append({"role": "assistant", "content": response_content})
#                     else:
#                         print('final result:', final_result)
#                         response_content = "No response generated."
                    
#                     # Build complete response
#                     response_text = ""
#                     if sql_queries:
#                         response_text += "\n"
#                         for db_name, query in sql_queries:
#                             response_text += f"**Database:** `{db_name}`\n```sql\n{query}\n```\n"
#                     response_text += f"\n{response_content}"
                    
#                     # Display response
#                     st.markdown(response_text)
                    
#                     # Add assistant message to chat history
#                     st.session_state["messages"].append({"role": "assistant", "content": response_text})
                    
#                     # Update chat sessions
#                     if st.session_state["session_index"] < len(st.session_state["chat_sessions"]):
#                         st.session_state["chat_sessions"][st.session_state["session_index"]] = st.session_state["messages"]
#                     else:
#                         st.session_state["chat_sessions"].append(st.session_state["messages"])
#                         title = user_input[:30] if user_input else "Untitled"
#                         st.session_state["session_titles"].append(title)
                    
#                     # Save to file
#                     with open(HISTORY_FILE, "w") as f:
#                         json.dump({
#                             "chat_sessions": st.session_state["chat_sessions"],
#                             "session_titles": st.session_state["session_titles"]
#                         }, f)
                                                
#                 except Exception as e:
#                     error_msg = f"An error occurred: {str(e)}"
#                     st.error(error_msg)
#                     logger.error(f"Error processing input: {str(e)}", exc_info=True)
#                     st.session_state["messages"].append({"role": "assistant", "content": error_msg})
#     except Exception as e:
#         st.error(f"An error occurred: {str(e)}")
#         logger.error(f"Fatal error: {str(e)}", exc_info=True)
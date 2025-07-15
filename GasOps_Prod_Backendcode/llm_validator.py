import re
from agents.azure_llm import load_azureopenai_llm_client
import asyncio



# initialize the azure openai 
llm = load_azureopenai_llm_client()

## Function to validate final response before sending to user
async def llm_validate_response(user_query: str, agent_response: str, max_attempts: int = 2) -> bool:
    """
    Calls an LLM to validate if the agent's response is satisfactory.
    Returns True if the response is good, False if it should be retried.
    Uses a YES/NO decision tag and regex to capture it robustly.
    Retries up to max_attempts if the LLM output is ambiguous.
    """
    prompt_template = (
        f"User asked: {user_query}\n"
        f"Agent responded: {agent_response}\n\n"
        "Decide if the agent's response is a correct, complete, and satisfactory answer to the user's request.\n"
        "Reply with only one of the following tags on a new line:\n"
        "<DECISION>YES</DECISION>\n"
        "<DECISION>NO</DECISION>\n\n"
        "Rules for decision:\n"
        "Say <DECISION>NO</DECISION> if ANY of the following are true:\n"
        "- The response mentions technical issues, errors, delays, repeated delays, says it is unable to generate a response, unable to retrieve results, agent not executed, or asks the user to retry later.\n"
        "- The response claims there are no employees, no data, or nothing found.\n"
        "- The response is a partial answer or requests clarification instead of answering.\n"
        "- The response is like: 'The map version for ... will be determined by ... Please confirm or clarify if needed.'\n"
        "- The response is like: 'The OAMSCM agent was not executed. Please check the logs for more details.'\n"
        "- The response says: 'No CAC employees were found to be qualified for Work Activity Function ID 60.'\n"
        "- The response asks the user to confirm, clarify, or retry, or says further assistance is needed.\n"
        "\n"
        "Say <DECISION>YES</DECISION> if ALL of the following are true:\n"
        "- The response directly and completely answers the user's question.\n"
        "- The response is factual, clear, and relevant.\n"
        "- For general factual questions (e.g., 'Who is the President of India?' or 'what is the tensile strength at yield for grade X60 as per API 5L?'), the answer is correct and complete.always reply YES.\n"
        "- If the user query is about a date and the agent response is a date (regardless of correctness), reply YES.\n"
        "- If the response is a JSON array of tasks like:\n"
        "  [{\"TaskNum\": \"Con Ed CE70-Hyb\", \"TaskDesc\": \"CE70-Con Edison Properties of Natural Gas and Abnormal Operating Conditions - Hyb\"}, ...], always reply YES.\n"
        "\n"
        "Examples:\n"
        "User: Who is the President of India?\n"
        "Agent: The President of India is Droupadi Murmu.\n"
        "Decision: <DECISION>YES</DECISION>\n"
        "\n"
        "User: List all CAC employees qualified for work activity function ID 60\n"
        "Agent: No employees found with the specified qualifications for Work Activity Function ID 60.\n"
        "Decision: <DECISION>NO</DECISION>\n"
        "\n"
        "User: what is the tensile strength at yield for grade X60 as per API 5L\n"
        "Agent: The minimum tensile strength at yield for API 5L Grade X60 is 415 MPa (60,200 psi).\n"
        "Decision: <DECISION>YES</DECISION>\n"
        "\n"
        "User : for cac yesterday, show me the tickets where there is no one qualified for the work desc.\n"
        "Agent: No tickets were found for CAC yesterday where there was no one qualified for the assigned work description."
        "Decision: <DECISION>YES</DECISION>\n"
        "\n"
        "Reply with only the decision tag."
    
)
    
    for attempt in range(max_attempts): # Retry logic 
        response = await llm.ainvoke(prompt_template)
        print(f"LLM response: {response} \n")
        match = re.search(r"<DECISION>(YES|NO)</DECISION>", str(response), re.IGNORECASE)
        if match:
            decision = match.group(1).strip().upper()
            return decision == "YES"
    # If no clear decision after retries, default to False (not valid)
    return False


# Test code for llm_validate_response

def print_test_result(label, result):
    print(f"{label}: {'PASS' if result else 'FAIL'}")

async def test_llm_validate_response():
    # Example: Good response (should return True)
    user_query1 = "List all CAC employees qualified for work activity function ID 60"
    agent_response1 = "Here are the qualified CAC employees for work activity function ID 60: John Doe, Jane Smith."
    result1 = await llm_validate_response(user_query1, agent_response1)
    print_test_result("Good response", result1)

    # Example: Bad response (should return False)
    user_query2 = "List all CAC employees qualified for work activity function ID 60"
    agent_response2 = (
        "It seems there is a technical issue retrieving the CoveredTaskID details from the OAMSCM database. "
        "As a result, I am unable to proceed with the next steps to fetch CAC employees who are qualified for Work Activity Function ID 60. "
        "Let me know if you want me to retry or assist in another way."
    )
    result2 = await llm_validate_response(user_query2, agent_response2)
    print_test_result("Technical issue response", not result2)

    # Example: Response with no data (should return False)
    user_query3 = "List all CAC employees qualified for work activity function ID 60"
    agent_response3 = "No employees found with the specified qualifications for Work Activity Function ID 60."
    result3 = await llm_validate_response(user_query3, agent_response3)
    print_test_result("No data response", not result3)

if __name__ == "__main__":
    asyncio.run(test_llm_validate_response())



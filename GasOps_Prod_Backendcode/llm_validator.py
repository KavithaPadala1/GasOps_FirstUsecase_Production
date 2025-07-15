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
        "Is this response a correct, complete, and satisfactory answer to the user's request? "
        "Reply with only one of the following tags on a new line:\n"
        "<DECISION>YES</DECISION>\n"
        "<DECISION>NO</DECISION>\n"
        "Say <DECISION>NO</DECISION> if the response mentions technical issues, errors, delays, repeated delays, says it is unable to generate a response, unable to retrieve results, agent not executed, or asks the user to retry later, or claims there are no employees, no data, or nothing found. "
        "For example, say <DECISION>NO</DECISION> for responses like: 'It seems like there has been a repeated delay in executing the query by the OAMSCM agent. Unfortunately, I am unable to retrieve the results. You may need to directly reach out or retry later to resolve this issue.' "
        "Also say <DECISION>NO</DECISION> if the response is a partial answer, or No CAC employees were found to be qualified for Work Activity Function ID 60. If you believe there is an error or require further assistance say no "
        "Always say <DECISION>NO</DECISION> if the response is like: 'The map version for 'regulator automation' will be determined by first finding the matched work activity function and then looking up its map version. Could you please specify if you want the map version for all regions or a particular contractor/vendor? If not, I will proceed to retrieve the general map version associated with regulator automation for your organization. Please confirm or clarify if needed.' "
        "For example, say <DECISION>NO</DECISION> for responses like: 'The OAMSCM agent was not executed. Please check the logs for more details.' "
        "For all other cases, including greetings, partial answers, or if any relevant data is present, reply <DECISION>YES</DECISION>."
        "REPLY YES IF USER QUERY is DATE and AGENT RESPONSE is DATE, and the date only dont check correct or wrong "
        "If the response is like this format ["
  "{\"TaskNum\": \"Con Ed CE70-Hyb\", \"TaskDesc\": \"CE70-Con Edison Properties of Natural Gas and Abnormal Operating Conditions - Hyb\"},"
  "{\"TaskNum\": \"Con Ed CE71-Hyb\", \"TaskDesc\": \"CE71-Con Edison Operator Excavating and Backfilling in the Vicinity of a Pipeline - Hyb\"}"
"]  always say <DECISION>YES</DECISION>"    )
    
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



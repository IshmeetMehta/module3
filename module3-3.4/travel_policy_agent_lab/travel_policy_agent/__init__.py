# ruff: noqa
import os
import logging
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from google.genai import Client

logger = logging.getLogger("travel_policy_agent")

# PROBLEM 2: Using the most expensive, slowest reasoning model for standard greetings and simple queries
# We configure the root agent to use gemini-2.5-pro by default
root_agent = Agent(
    name="cymbal_travel_policy_agent",
    model=Gemini(model_name="gemini-2.5-pro"),
    instruction="You are an expert corporate travel concierge. You help employees answer questions about travel, meals, accommodations, and expense limits. Use the query_travel_policy tool for all answers.",
)

@root_agent.skill
def query_travel_policy(user_query: str) -> str:
    """Queries the corporate travel and expense policy document to answer employee questions.
    
    Args:
        user_query: The employee's question about corporate travel or expenses.
    """
    logger.info(f"Processing query: {user_query}")
    client = Client()
    
    # PROBLEM 1: Reading a huge file from disk into the prompt payload on EVERY SINGLE message
    policy_path = os.path.join(os.path.dirname(__file__), "corporate_travel_policy.txt")
    
    if not os.path.exists(policy_path):
        logger.warning("Policy file not found! Using fallback stub.")
        massive_policy_text = "Standard corporate travel rules apply. Max daily meal expense is $75."
    else:
        with open(policy_path, "r") as f:
            massive_policy_text = f.read()
            
    system_instruction = (
        "You are a helpful HR and travel concierge. Use the provided corporate travel policy "
        f"document text to answer the employee's query accurately: {massive_policy_text}"
    )
    
    # PROBLEM 2 (cont.): Generating content with the slow, expensive model, loading the raw document context every time
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=user_query,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction
        )
    )
    return response.text

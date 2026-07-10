# ruff: noqa
try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.extract_from_urllib3()
except Exception:
    pass

import os
import logging
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from google.genai import Client

logger = logging.getLogger("travel_policy_agent")

# Global lazy-initialization variables for context caching
_client = None
_policy_cache = None

def get_client_and_cache():
    """Lazily initializes the GenAI Client and the global Context Cache once."""
    global _client, _policy_cache
    if _client is None:
        _client = Client()
    if _policy_cache is None:
        logger.info("Initializing persistent context cache for corporate travel policy...")
        policy_path = os.path.join(os.path.dirname(__file__), "corporate_travel_policy.txt")
        
        if not os.path.exists(policy_path):
            logger.warning("Policy file not found! Caching fallback stub.")
            policy_text = "Standard corporate travel rules apply. Max daily meal expense is $75."
        else:
            with open(policy_path, "r") as f:
                policy_text = f.read()
        
        # Create persistent cache using gemini-2.5-flash (valid for 30 minutes)
        # Moving system_instruction here since Vertex AI forbids setting it in generate_content when caching is used
        _policy_cache = _client.caches.create(
            model="gemini-2.5-flash",
            config=types.CreateCachedContentConfig(
                contents=[policy_text],
                system_instruction=(
                    "You are an expert HR and travel concierge. Use the provided cached travel policy "
                    "context to answer the employee's query accurately."
                ),
                ttl="1800s"  # Valid for 30 minutes
            )
        )
        logger.info(f"Context Cache created successfully: {_policy_cache.name}")
        
    return _client, _policy_cache


def query_travel_policy(user_query: str) -> str:
    """Queries the corporate travel and expense policy document to answer employee questions.
    
    Args:
        user_query: The employee's question about corporate travel or expenses.
    """
    logger.info(f"Processing query: {user_query}")
    cleaned_query = user_query.strip().lower()
    
    # --- OPTIMIZATION: Tiered Model Routing for Greetings/Short Queries ---
    greetings = ["hi", "hello", "hey", "thanks", "thank you", "good morning", "good afternoon"]
    if len(cleaned_query) < 15 or any(greet == cleaned_query for greet in greetings):
        logger.info("Greeting/Short query detected. Bypassing context cache and routing to Flash.")
        client = Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Respond politely and briefly to the employee: {user_query}"
        )
        return response.text

    # --- OPTIMIZATION: Deep Reasoning Escalation to gemini-2.5-pro ---
    # Trigger escalation if we detect complex comparative language, or multiple policy topics in one query
    escalation_keywords = ["compare", "comparison", "difference", "versus", "vs", "multiple", "complex", "exception", "combination", "both"]
    topics = ["meal", "food", "dinner", "breakfast", "lunch", "flight", "airfare", "travel", "plane", "hotel", "lodging", "stay", "accommodation", "uber", "rideshare", "taxi", "car", "vehicle"]
    matched_topics = [t for t in topics if t in cleaned_query]
    
    is_complex = (
        any(word in cleaned_query for word in escalation_keywords) or
        len(matched_topics) >= 2 or
        cleaned_query.count(" and ") >= 2 or
        cleaned_query.count(" or ") >= 2
    )

    if is_complex:
        logger.info("Complex query detected. Upgrading to gemini-2.5-pro reasoning model (no cache).")
        policy_path = os.path.join(os.path.dirname(__file__), "corporate_travel_policy.txt")
        if os.path.exists(policy_path):
            with open(policy_path, "r") as f:
                policy_text = f.read()
        else:
            policy_text = "Standard corporate travel rules apply. Max daily meal expense is $75."
            
        client = Client()
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=(
                f"Here is the Cymbal Group Corporate Travel & Expense Policy:\n\n{policy_text}\n\n"
                f"Using the policy, answer the following complex query with deep reasoning: {user_query}"
            )
        )
        return response.text

    # --- OPTIMIZATION: Google GenAI Context Caching for Standard Compliance Queries ---
    client, policy_cache = get_client_and_cache()
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_query,
        config=types.GenerateContentConfig(
            cached_content=policy_cache.name
        )
    )
    return response.text


# Configure the agent to use the faster, cost-efficient gemini-2.5-flash model
root_agent = Agent(
    name="cymbal_travel_policy_agent",
    model=Gemini(model_name="gemini-2.5-flash"),
    instruction="You are an expert corporate travel concierge. You help employees answer questions about travel, meals, accommodations, and expense limits. Always use the query_travel_policy tool for compliance answers.",
    tools=[query_travel_policy],
)

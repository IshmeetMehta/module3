# Lab Guide: Cymbal Travel Policy Concierge Latency & Cost Optimization (Break-Fix)

## Scenario

Your organization deployed a lightweight, fast, and cost-efficient **Cymbal Travel Policy Concierge** agent that worked beautifully with a simple 1-page policy document. 

However, the Corporate Travel Department recently released a massive **new Global Travel Policy**. They published the official visual guide as **`Cymbal Group Global Travel and Expense Policy.pdf`** and converted its contents to a comprehensive raw text handbook **`corporate_travel_policy.txt`** containing 50+ complex department-specific regional annexes (inflating the payload size to over 104 KB).

An engineering intern was tasked with quickly deploying the new policy to the agent. Within 48 hours of rolling it out, two critical escalations have hit your desk:

1. **User Experience Escalation**: Users report that the agent takes **7 to 10 seconds** to respond to basic questions or even simple greetings (like "Hi" or "Thanks") in the corporate chat application.
2. **Billing Escalation**: The Cloud Finance team reports a massive spike in API spend—the agent appears to be consuming millions of raw tokens per minute, even during periods of light usage.

Your mission is to enter the environment, trace the intern's implementation errors, resolve the immediate startup crash, and optimize the agent to handle the massive new policy efficiently!

---

## 🛠️ The Architecture

The application is structured as a localized Python package (`travel_policy_agent`) integrated into a production-ready **FastAPI web server** (`agent.py`). 

```
module3-3.4/
└── travel_policy_agent_lab/                         # (Your active Travel Policy lab folder)
    ├── LAB_GUIDE.md                                 # This Guide!
    ├── antigravity_prompts.md                       # Antigravity copy-paste prompts
    └── travel_policy_agent/                         # The Agent Package & Server
        ├── __init__.py                              # Python Agent Definitions & Tool Implementation
        ├── agent.py                                 # FastAPI Web Server (Runs the Agent)
        ├── requirements.txt                         # Project Dependencies
        └── corporate_travel_policy.txt              # Comprehensive 104 KB Corporate Travel Policy Document
```

> [!NOTE]
> **Looking for the HR Policy Agent Lab?**
> The lightweight **HR Policy Agent** single-file sandbox lab has been moved and isolated in your home directory at `~/hr_policy_agent_lab/` to keep this active workspace 100% focused on the Cymbal Travel FastAPI web application.

---

## 🚀 Phase 1: Resolving the Startup Crash (Import Bug)

Before you can even run the server to measure performance, you must resolve an immediate startup crash left by the intern.

### Step 1: Attempt to Start the FastAPI Server
From the `module3-3.4` root directory, execute the following commands in your terminal:

```bash
# Make sure your virtual environment is active
source .venv/bin/activate
pip install -r travel_policy_agent_lab/travel_policy_agent/requirements.txt

# Start the agent server in uvicorn
python3 travel_policy_agent_lab/travel_policy_agent/agent.py
```

### Step 2: Analyze the Crash
The server will fail to start and crash immediately with the following error:
```text
  File ".../travel_policy_agent/__init__.py", line 19, in <module>
    @root_agent.skill
     ^^^^^^^^^^^^^^^^
AttributeError: 'LlmAgent' object has no attribute 'skill'
```

> [!IMPORTANT]
> **Why did this happen?**
> The intern attempted to register the `query_travel_policy` tool using an `@root_agent.skill` decorator. In the official Google Agent Development Kit (ADK), there is no `.skill` attribute or decorator. Instead, skills/tools must be registered by passing them in the `tools` list argument when instantiating the `Agent` object.

### Step 3: Resolve the Startup Bug
1. Open [travel_policy_agent/__init__.py](file:///usr/local/google/home/ishmeetm/module3-3.4/travel_policy_agent_lab/travel_policy_agent/__init__.py) in your editor.
2. Remove the `@root_agent.skill` decorator on line 19.
3. Modify the `root_agent` instantiation (lines 13-17) to define the agent *after* the `query_travel_policy` function and pass the tool inside the `tools` list:

> [!TIP]
> **Want an AI Pair Programmer to resolve this crash for you?**
> Open [antigravity_prompts.md](file:///usr/local/google/home/ishmeetm/module3-3.4/travel_policy_agent_lab/antigravity_prompts.md) and copy-paste the **Phase 1 Prompt** directly into your Antigravity chat window! It will automatically analyze the traceback and rewrite the tool registration using correct Google ADK standard interfaces for you.

```python
# 1. Define function first
def query_travel_policy(user_query: str) -> str:
    ...

# 2. Register tool during Agent instantiation
root_agent = Agent(
    name="cymbal_travel_policy_agent",
    model=Gemini(model_name="gemini-2.5-pro"),
    instruction="...",
    tools=[query_travel_policy],  # Proper Google ADK registration
)
```

Restart the server:
```bash
python3 travel_policy_agent_lab/travel_policy_agent/agent.py
```
> [!TIP]
> The server should now successfully start up and bind to `http://0.0.0.0:8000`!

---

## 🚀 Phase 2: Resolving the Runtime Event Loop Crash (Runtime Bug)

Now that the server compiles and starts up, you will notice that the very first query works perfectly, but the **second request onwards crashes** with an async error!

Prompt to Antigravity
```text

Run the server . Run this curl request two times to see if server is working correctly.

curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"message": "Hi"}'
```


OR

### Step 1: Trigger the Runtime Error
Start the server and run your first chat query:
```bash
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"message": "Hi"}'
```
* **Result**: Works perfectly and returns a response.

Now, run the exact same command a **second time**:
```bash
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"message": "Hi"}'
```
* **Result**: The server crashes with:
```text
RuntimeError: Event loop is closed
```

### 🔍 Why did this happen?
FastAPI runs on a persistent, global asynchronous event loop inside Uvicorn. However, in the intern's original `agent.py`, they invoked the synchronous blocking `runner.run(...)` method inside FastAPI's `/chat` endpoint. 

To run this without freezing the main thread, the ADK runner is forced to spawn a temporary background thread with its own short-lived event loop (`asyncio.run()`).
1. **First Request**: The ADK runner initializes the underlying Google GenAI Client. The Client creates an asynchronous `httpx` connection pool bound to that temporary background thread's loop. When the request ends, the background thread closes its event loop.
2. **Second Request**: The ADK runner spawns a new background thread with a *new* event loop. The persistent, globally instantiated GenAI Client attempts to reuse its cached `httpx` connection pool—but since it is bound to the *closed* loop of the previous thread, Python throws `RuntimeError: Event loop is closed`!

### Step 2: Fix the Runtime Bug
To resolve this, we must force the entire ADK agent runner execution to execute natively on FastAPI's persistent event loop. 

> [!TIP]
> **Want an AI Pair Programmer to resolve this runtime crash for you?**
> Open [antigravity_prompts.md](file:///usr/local/google/home/ishmeetm/module3-3.4/travel_policy_agent_lab/antigravity_prompts.md) and copy-paste the **Phase 2 Prompt** directly into your Antigravity chat window! It will automatically convert the `/chat` endpoint to run asynchronously on FastAPI's main persistent loop.

1. Open [travel_policy_agent/agent.py](file:///usr/local/google/home/ishmeetm/module3-3.4/travel_policy_agent_lab/travel_policy_agent/agent.py) in your editor.
2. In the `/chat` endpoint (around lines 110–124), replace `runner.run(...)` with its asynchronous counterpart: `await runner.run_async(...)`.
3. Since `runner.run_async` returns an async generator, replace the `for` loop with an `async for` loop:

```python
        # Change this:
        # events = runner.run(...)
        # for event in events:
        
        # To this:
        events = await runner.run_async(
            new_message=message,
            user_id="default_user",
            session_id=session_id,
            run_config=RunConfig(streaming_mode=StreamingMode.NONE),
        )
        
        response_text = ""
        async for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
```

Restart the FastAPI server. Now, you can query the `/chat` endpoint repeatedly without any event-loop or pooling issues!

---

## 🚀 Phase 3: Latency & Cost Optimization

Now that the server is successfully running, you can analyze the baseline performance and optimize the architecture.

### Step 1: Query the Server (The Greeting Baseline)
Open a separate terminal window and send a simple greeting using `curl`:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi"}'
```

* **Expected Latency**: **1 to 2 seconds**
* **Why?**: The main agent model (`gemini-2.5-pro`) is smart enough to reply to greetings directly. Since it does not need policy information, it **does not invoke the tool**, bypassing the 104 KB handbook load completely.

### Step 2: Query the Server (The Policy Baseline)
Now, ask a real compliance question that forces the agent to query the policy:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the daily meal limit in San Francisco?"}'
```

* **Expected Latency**: **8 to 12 seconds**
* **Why?**: The agent detects a policy question and is forced to invoke the `query_travel_policy` tool. Inside the tool, the script opens, reads, and uploads the entire **104 KB travel handbook** (~26,000 tokens) from disk and passes it raw to the model. This results in severe latency and a massive token bill!

---

## 🛠️ The Fix: Caching & Tiered Routing

To fix the latency and billing escalations, implement these two high-performance design patterns:

### Optimization A: Global Context Caching
Instead of uploading the 104 KB policy document on every single tool execution, write a helper function that:
1. Lazily instantiates the `genai.Client()`.
2. Creates a **Google GenAI Context Cache** containing the travel policy document.
3. Reuses this pre-compiled cache across all subsequent tool calls via `cached_content=policy_cache.name`.

### Optimization B: Tiered Model Routing (Bypassing the Cache)
Simple greetings ("Hi", "Hello", "Thanks") or very short questions do not require policy lookups or massive reasoning. 
1. Intercept simple greetings at the beginning of the tool.
2. Bypass reading the handbook or calling the cache entirely.
3. Route these queries directly to `gemini-2.5-flash` with a brief instructions prompt.

---

## ✍️ Guided Implementation

Stop your running FastAPI server (`Ctrl+C`) and replace the contents of [travel_policy_agent/__init__.py](file:///usr/local/google/home/ishmeetm/module3-3.4/travel_policy_agent_lab/travel_policy_agent/__init__.py) with the fully optimized version:

> [!TIP]
> **Want an AI Pair Programmer to implement these optimizations?**
> Open [antigravity_prompts.md](file:///usr/local/google/home/ishmeetm/module3-3.4/travel_policy_agent_lab/antigravity_prompts.md) and copy-paste the **Phase 2 Prompt** directly into your Antigravity chat window! It will automatically write the context caching helper, add the routing logic, and replace the broken agent configurations for you.

```python
# ruff: noqa
import os
import logging
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from google.genai import Client

logger = logging.getLogger("travel_policy_agent")

# Global lazy-initialization variables
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
        _policy_cache = _client.caches.create(
            model="gemini-2.5-flash",
            config=types.CreateCachedContentConfig(
                contents=[types.Content(parts=[types.Part.from_text(text=policy_text)])],
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
    
    # --- OPTIMIZATION B: Tiered Model Routing for Greetings ---
    cleaned_query = user_query.strip().lower()
    greetings = ["hi", "hello", "hey", "thanks", "thank you", "good morning", "good afternoon"]
    if len(cleaned_query) < 15 or any(greet == cleaned_query for greet in greetings):
        logger.info("Greeting/Short query detected. Bypassing context cache and routing to Flash.")
        client = Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Respond politely and briefly to the employee: {user_query}"
        )
        return response.text

    # --- OPTIMIZATION A: Google GenAI Context Caching ---
    client, policy_cache = get_client_and_cache()
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_query,
        config=types.GenerateContentConfig(
            cached_content=policy_cache.name,
            system_instruction=(
                "You are an expert HR and travel concierge. Use the provided cached travel policy "
                "context to answer the employee's query accurately."
            )
        )
    )
    return response.text

# Configure the agent to use the faster, cost-efficient gemini-2.5-flash model
# Pass the query_travel_policy tool in the tools list parameter
root_agent = Agent(
    name="cymbal_travel_policy_agent",
    model=Gemini(model_name="gemini-2.5-flash"),
    instruction="You are an expert corporate travel concierge. You help employees answer questions about travel, meals, accommodations, and expense limits. Always use the query_travel_policy tool for compliance answers.",
    tools=[query_travel_policy],
)
```

---

## 📈 Verification and Comparison

Restart your FastAPI server (`python3 travel_policy_agent_lab/agent.py`) and repeat the baseline tests.

### Test 1: Simple Greeting
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi"}'
```

* **New Latency**: **< 1.5 seconds** (down from 7-10s)
* **Token Cost**: ~10 tokens (down from ~26,000 tokens)

### Test 2: Complex Policy Query
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the daily meal limit in San Francisco?"}'
```

* **New Latency**: **< 2.5 seconds** (down from 8-12s)
* **Token Cost**: You are now billed under the **Context Caching pricing model**, which is significantly cheaper than standard model queries!

---

## 📊 Summary of Optimization Impact

| Metric / Scenario | Broken Baseline Agent | Optimized Agent (Your Fixes) | Performance Gains |
| :--- | :--- | :--- | :--- |
| **Greeting Latency** | 7 to 10 seconds | **< 1.5 seconds** | **85% faster** response times |
| **Greeting Token Footprint** | ~26,000 tokens / query | **~15 tokens / query** | **99.9% cost reduction** |
| **Policy Query Latency** | 8 to 12 seconds | **< 2.5 seconds** | **75% faster** response times |
| **Policy Query Cost** | Full Price (Pro Model, Raw Payload) | Cache-pricing (Flash Model, Cached Payload) | **90%+ savings on token ingestion** |

**Congratulations!** You have successfully resolved the startup crash, user experience latency escalation, and the cloud finance billing spike by applying Context Caching and Tiered Routing patterns.

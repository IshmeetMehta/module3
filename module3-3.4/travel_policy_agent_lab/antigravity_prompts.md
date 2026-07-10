# Prompts for Antigravity

This guide contains the exact, verified prompts you can copy-paste and send to **Antigravity** to guide you through fixing the travel policy agent step-by-step.

---

## 🚀 Phase 1 Prompt: Fix the Startup Crash (Import Bug)

Copy and paste this prompt into your Antigravity chat to resolve the immediate `AttributeError` and get the FastAPI server compiling:

```text
Please help me debug my travel policy agent. 

When I try to start the FastAPI server, it crashes on startup with the following error:
AttributeError: 'LlmAgent' object has no attribute 'skill'

Please inspect `travel_policy_agent/__init__.py` and correct the tool/skill registration code using the proper Google Agent Development Kit (ADK) standards (register the function inside the tools parameter of the Agent instantiation). 

Ensure that we don't change any of the internal business logic or parameters, and make sure that python can successfully import the `root_agent` from the package.
```

---

## 🚀 Phase 2 Prompt: Fix the Runtime Event Loop Crash (Runtime Bug)

Copy and paste this prompt into your Antigravity chat once the server starts successfully, but crashes on the second request with a runtime error:

```text
Please help me debug my FastAPI server. The first request succeeds perfectly, but on the second request and all subsequent queries, the server crashes with:
RuntimeError: Event loop is closed

Please inspect `travel_policy_agent/agent.py`. Convert the synchronous blocking `runner.run(...)` call in the `/chat` endpoint to the asynchronous `await runner.run_async(...)` method, and update the event iteration loop to use `async for event in events:`. Make sure the endpoint function `chat_endpoint` remains async.
```

---

## 🚀 Phase 3 Prompt: Refactor for Latency & Cost Optimization

Copy and paste this prompt into your Antigravity chat once both compilation and runtime event-loop issues are fully resolved to apply Context Caching and Tiered Routing:

```text
Now that the server is starting and responding successfully without any event loop issues, we need to optimize the agent in `travel_policy_agent/__init__.py` to solve our latency and billing escalations.

Please apply the following architectural improvements to the file:

1. **Google GenAI Context Caching**:
   - Write a helper function that lazily initializes the `Client()` once and creates a global context cache using the model `gemini-2.5-flash` and a TTL of `1800s` (30 minutes) loading the contents of `travel_policy_agent/corporate_travel_policy.txt`.
   - Reuse this pre-compiled cache across all subsequent compliance policy query tool executions via the config `cached_content=policy_cache.name`.

2. **Tiered Model Routing**:
   - Change the `root_agent` configuration to use the fast, cost-effective `gemini-2.5-flash` model by default (instead of the slow/expensive `gemini-2.5-pro` reasoning model).
   - In the `query_travel_policy` function, intercept simple greetings or extremely short inputs (e.g. "hi", "hello", "thanks", "thank you", "hey", or queries under 15 characters). Route these directly to a light `gemini-2.5-flash` generation without calling the cache or loading any policy context, keeping responses under 1.5 seconds.
   - For all actual policy queries, run a generation using `gemini-2.5-flash` with the cached content config to answer compliance questions instantly.

Make sure to preserve all existing imports, logging configurations, and function signatures, and verify that python can import the fixed agent cleanly!
```

---

## 🔍 The Verification Prompt

Copy and paste this prompt to verify the final result and make sure no package paths are broken:

```text
Great! Now let's verify that the code can be successfully imported by python and runs correctly. Please run a quick python validation command to ensure the agent package is clean and has no syntax or import errors.
```

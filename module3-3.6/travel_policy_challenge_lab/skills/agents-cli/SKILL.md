---
name: agents-cli-orchestrator
description: Compiles, deploys, and registers Gemini Enterprise Agent Platform (GEAP) agents using agents-cli.
---

# `agents-cli` Orchestrator Skill

This skill empowers the Antigravity agent to autonomously build, package, deploy, and register containerized travel and compliance agents on the Gemini Enterprise Agent Platform (GEAP) using the `agents-cli` developer toolset.

---

## 🛠️ CLI Reference Guidelines

### 1. Build Agent Container
To package and compile your local agent codebase into a secured container, run:
```bash
agents-cli build --repo=[REPOSITORY_NAME] --tag=[TAG_NAME]
```
- **`--repo`**: The target Artifact Registry Docker repository name (e.g., `hr-policy-repo`).
- **`--tag`**: The tag to assign to the image (usually `latest` or a specific semver version).
- **Behavior**: This command triggers Cloud Build remotely to compile the agent and pushes it to `us-central1-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/travel-concierge:[TAG_NAME]`.

### 2. Deploy Agent Container
To deploy the successfully compiled container image to the Agent Engine service layer:
```bash
agents-cli deploy --image=us-central1-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY_NAME]/travel-concierge:[TAG_NAME] --region=[REGION]
```
- **`--image`**: The full registry path of the Docker image built in the previous step.
- **`--region`**: The deployment region (defaults to `us-central1` if not specified).
- **Output**: After a successful run, the command outputs the live HTTPS service endpoint URL (e.g., `https://travel-concierge-ae-us-central1.run.app/chat`). Record this URL for the registration step.

### 3. Register Agent with Agent Registry
To enroll the live service endpoint into the central discovery registry:
```bash
agents-cli register --config=[CONFIG_JSON_PATH]
```
- **`--config`**: Path to the standard JSON registry mapping config (typically `register-agent.json`).
- **Required JSON Keys**:
  ```json
  {
    "agent_id": "cymbal-travel-policy-concierge",
    "display_name": "Cymbal Travel Policy Concierge",
    "runtime_endpoint": "[LIVE_SERVICE_ENDPOINT_URL]",
    "identity_mapping": {
      "service_account": "[SERVICE_ACCOUNT_EMAIL]"
    }
  }
  ```

---

## 🎯 Implementation Workflows for the Agent

When instructed by the user to compile, deploy, or register their agent:
1. **Identify parameters**: Scan the active workspace files (such as `register-agent.json`) or environment variables to resolve `[PROJECT_ID]`, `[REPOSITORY_NAME]`, and `[SERVICE_ACCOUNT_EMAIL]`.
2. **Execute steps sequentially**: 
   - First, run the `build` command. Wait for build completion logs.
   - Second, run the `deploy` command. Parse its console output to extract the live HTTPS runtime URL.
   - Third, dynamically update `register-agent.json` with the extracted runtime URL.
   - Fourth, run the `register` command to enroll the live endpoint.
3. **Verify registration status**: Confirm that the command exits successfully with status code `0`.

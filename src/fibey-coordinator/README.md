# Fibey Coordinator

Network operations coordinator agent — a long-running AI teammate that monitors, investigates, dispatches, and escalates.

## What It Does

Fibey is not a chatbot. Fibey is an employee:
- **Proactively monitors** network telemetry via routines
- **Investigates anomalies** and builds investigation dossiers
- **Dispatches work orders** to field contractors
- **Waits for responses** (scales to zero while waiting — $0 compute)
- **Escalates** when SLAs are at risk
- **Persists context** to $HOME filesystem across sessions

## Architecture

Uses the Microsoft Agent Framework (MAF) pattern:
- FoundryChatClient + FunctionTool for tool orchestration
- ResponseEventStream for Responses protocol streaming
- Real file persistence via $HOME/investigations/
- azure-ai-agentserver-responses SDK for hosting

### Multi-agent: coordinator → field-ops

Fibey is the **coordinator** in a two-agent system. When a task needs on-site
expertise, it delegates to the **`field-ops-agent`** (a separate hosted agent)
over that agent's Responses endpoint — the *agent-as-tool* pattern. Two paths
trigger the handoff:

- `ask_field_ops` — a read-only tool the model calls for technician questions
  (site specs, repair procedures, part numbers, work-order detail).
- `dispatch_work_order` — after creating a work order, it briefs the field-ops
  technician agent and returns the technician's acknowledgement (first step +
  parts). The same handoff runs in the durable approval path
  (`execute_destructive_action`).

The link is **opt-in**: set `FIELD_OPS_AGENT_ENDPOINT` (see *Environment
variables*) to the deployed field-ops agent's Responses URL. When unset, the
coordinator runs standalone and the tools return a graceful "not configured"
note instead of failing. See [`field_ops_tool.py`](field_ops_tool.py).

## Tools

| Tool | Description |
|------|-------------|
| check_network_telemetry | Monitor sites for anomalies and active alerts |
| request_approval | Human-in-the-loop gate before any destructive action |
| dispatch_work_order | Create a work order **and hand it to the field-ops agent** for acknowledgement |
| save_investigation | Save investigation context to persistent $HOME |
| get_active_incidents | List all active incidents across the portfolio |
| escalate_incident | Escalate to ops manager on SLA breach |
| ask_field_ops | Delegate technician questions to the `field-ops-agent` (connected agent) |

Currently using mock data with rich telemetry, alerts, and incident portfolios.

## Model

- Deployment: gpt-5 (configurable via AZURE_AI_MODEL_DEPLOYMENT_NAME)

## Example Prompts

- Check network telemetry for Quincy North - any active alerts?
- Dispatch a work order for the CRC error on Rack B-14
- Ask field ops what repair procedure to follow for a QSFP-DD transceiver replacement
- Save an investigation report for the fiber degradation incident
- What active incidents do we have across all sites?
- Escalate the Quincy North optical power issue - SLA at risk

## Running

```bash
# Deploy to Foundry (from repo root)
$env:AZURE_TENANT_ID = (az account show --query tenantId -o tsv)  # PowerShell
azd deploy fibey-coordinator

# Invoke via azd (after deploy)
azd ai agent run --service fibey-coordinator
```

The playground URL is printed by `azd deploy`. Open it to chat immediately.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FOUNDRY_PROJECT_ENDPOINT` | yes | Auto-injected in hosted containers |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | yes | Model deployment name (default: `gpt-5`) |
| `FIELD_OPS_AGENT_ENDPOINT` | no | Deployed `field-ops-agent` Responses base URL. Enables the connected-agent handoff (`ask_field_ops` / `dispatch_work_order`). Unset → coordinator runs standalone. Get it from `azd show`. |
| `FIELD_OPS_AGENT_MODEL` | no | Model name sent in the Responses request body (default: coordinator model). The hosted field-ops agent uses its own worker model regardless. |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | no | Auto-injected; enables tracing |

## Connecting to the field-ops agent (multi-agent)

To turn on the coordinator → field-ops handoff, point the coordinator at the
deployed `field-ops-agent` and redeploy:

```bash
# 1. Deploy the field-ops agent (if not already) and grab its endpoint
azd deploy field-ops-agent
azd show          # copy the field-ops-agent endpoint / playground URL

# 2. Point the coordinator at it and grant access
azd env set FIELD_OPS_AGENT_ENDPOINT "<field-ops-agent responses base URL>"
#    Grant this coordinator's managed identity permission to invoke the
#    field-ops hosted agent (Foundry User on the project / agent).

# 3. Redeploy the coordinator
azd deploy fibey-coordinator
```

With the endpoint set, `ask_field_ops` and `dispatch_work_order` call the live
field-ops agent. Without it, the coordinator runs standalone and those tools
return a graceful "not configured" note. See [`field_ops_tool.py`](field_ops_tool.py).

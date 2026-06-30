"""Connected-agent tool — call the field-ops-agent over its Responses endpoint.

═══════════════════════════════════════════════════════════════════════════════
DEMO POINT — "Agent-as-tool" (coordinator → field-ops)

Fibey delegates technician-facing questions (site fiber/panel specs, repair
procedures, transceiver part numbers, active work-order detail) to the deployed
``field-ops-agent`` instead of answering from its own mock data. The remote
hosted agent is exposed to the model as a single function tool — same shape as
any local tool.
═══════════════════════════════════════════════════════════════════════════════

Wiring (opt-in — unset ⇒ graceful fallback message, never a crash):
  FIELD_OPS_AGENT_ENDPOINT
      Base URL of the deployed field-ops-agent (its Responses protocol root).
      The tool POSTs to ``{FIELD_OPS_AGENT_ENDPOINT}/responses``. Find it with
      ``azd show`` (the agent's playground/endpoint URL) or in the Foundry
      portal under the field-ops-agent.
  FIELD_OPS_AGENT_MODEL (optional)
      Model/deployment name sent in the request body to satisfy the Responses
      request schema. Defaults to the coordinator's model. The hosted field-ops
      agent runs its own worker model regardless of this value.

Auth: an AAD bearer token (scope ``https://ai.azure.com/.default``) is injected
on every request via ``DefaultAzureCredential`` — no keys in the repo.
"""

from __future__ import annotations

import logging
import os

import httpx
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

logger = logging.getLogger(__name__)

_FIELD_OPS_SCOPE = "https://ai.azure.com/.default"


def _extract_text(data: dict) -> str:
    """Pull assistant text out of an OpenAI Responses payload, defensively."""
    # Preferred convenience field.
    text = data.get("output_text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    # Otherwise walk output[].content[].text (text may be a str or {"value": ...}).
    parts: list[str] = []
    for item in data.get("output", []) or []:
        for block in item.get("content", []) or []:
            t = block.get("text")
            if isinstance(t, dict):
                t = t.get("value")
            if isinstance(t, str) and t.strip():
                parts.append(t.strip())
    return "\n".join(parts)


def _prepare(question: str):
    """Build the (url, payload, headers) for a field-ops Responses call.

    Returns ``None`` when ``FIELD_OPS_AGENT_ENDPOINT`` is unset so callers can
    degrade gracefully instead of failing.
    """
    endpoint = os.getenv("FIELD_OPS_AGENT_ENDPOINT", "").strip().rstrip("/")
    if not endpoint:
        logger.info("FIELD_OPS_AGENT_ENDPOINT not set — field-ops delegation disabled.")
        return None

    model = (
        os.getenv("FIELD_OPS_AGENT_MODEL", "").strip()
        or os.getenv("MODEL_DEPLOYMENT_NAME", "").strip()
        or os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "").strip()
        or "gpt-5"
    )

    get_token = get_bearer_token_provider(DefaultAzureCredential(), _FIELD_OPS_SCOPE)
    url = f"{endpoint}/responses"
    payload = {"model": model, "input": question, "stream": False}
    headers = {"Authorization": f"Bearer {get_token()}"}
    return url, payload, headers


_NOT_CONFIGURED = (
    "The field-ops agent is not configured (FIELD_OPS_AGENT_ENDPOINT is unset), "
    "so I can't reach it right now."
)


async def ask_field_ops(question: str) -> str:
    """Ask the on-site field-ops technician agent and return its answer.

    Use this to delegate field/technician questions that the field-ops-agent
    specializes in: site fiber/panel specs, step-by-step repair procedures,
    transceiver part numbers, and active work-order detail for a technician.
    Pass the question in natural language.

    Args:
        question: The natural-language question to send to the field-ops agent.
    """
    prepared = _prepare(question)
    if prepared is None:
        return _NOT_CONFIGURED
    url, payload, headers = prepared

    logger.info("Delegating to field-ops agent: %s", url)
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:  # noqa: BLE001
        logger.warning("field-ops call failed (%s): %s", type(e).__name__, e)
        return f"Couldn't reach the field-ops agent ({type(e).__name__}: {e})."

    answer = _extract_text(data)
    return answer or "The field-ops agent returned no answer."


def ask_field_ops_sync(question: str) -> str | None:
    """Synchronous variant of :func:`ask_field_ops` for non-async contexts.

    Used by the durable orchestration activity (which runs in a sync worker
    thread). Returns ``None`` when the field-ops endpoint isn't configured so
    the caller can fall back to mock behavior.

    Args:
        question: The natural-language question to send to the field-ops agent.
    """
    prepared = _prepare(question)
    if prepared is None:
        return None
    url, payload, headers = prepared

    logger.info("Delegating to field-ops agent (sync): %s", url)
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:  # noqa: BLE001
        logger.warning("field-ops call failed (%s): %s", type(e).__name__, e)
        return f"Couldn't reach the field-ops agent ({type(e).__name__}: {e})."

    answer = _extract_text(data)
    return answer or "The field-ops agent returned no answer."


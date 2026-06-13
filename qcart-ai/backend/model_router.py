"""Multi-Region Bedrock Model Router.

Routes inference requests to the correct AWS region based on model availability.
Uses 3 active models: Nova Pro (primary), Nova Lite (fast), Llama (fallback).

Usage:
    from model_router import invoke, invoke_json, Task

    result = invoke_json(Task.CART_GENERATION, messages=[...])
    print(result["parsed"])
"""

import json
import logging
import os
import re
import time
from enum import Enum
from typing import Any

import boto3
from dotenv import load_dotenv

load_dotenv()

# ─── Logging ───────────────────────────────────────────────────────────────────

logger = logging.getLogger("model_router")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"
    ))
    logger.addHandler(handler)

# ─── Configuration (only models you have access to) ────────────────────────────

MODEL_CONFIG = {
    "nova_pro": {
        "region": os.getenv("NOVA_PRO_REGION", "us-east-1"),
        "model_id": os.getenv("NOVA_PRO_MODEL_ID", "amazon.nova-pro-v1:0"),
        "max_tokens": 5000,
    },
    "nova_lite": {
        "region": os.getenv("NOVA_LITE_REGION", "us-east-1"),
        "model_id": os.getenv("NOVA_LITE_MODEL_ID", "amazon.nova-lite-v1:0"),
        "max_tokens": 5000,
    },
    "llama": {
        "region": os.getenv("LLAMA_REGION", "us-east-1"),
        "model_id": os.getenv("LLAMA_MODEL_ID", "meta.llama3-70b-instruct-v1:0"),
        "max_tokens": 4096,
    },
    # Reserved — not in active routing
    "nova_sonic": {
        "region": os.getenv("NOVA_SONIC_REGION", "us-east-1"),
        "model_id": os.getenv("NOVA_SONIC_MODEL_ID", "amazon.nova-sonic-v1:0"),
        "max_tokens": 4096,
    },
    "nemotron_super": {
        "region": os.getenv("NEMOTRON_REGION", "us-east-1"),
        "model_id": os.getenv("NEMOTRON_MODEL_ID", "nvidia.nemotron-super-v1:0"),
        "max_tokens": 4096,
    },
}

# ─── Tasks ─────────────────────────────────────────────────────────────────────


class Task(str, Enum):
    """Routable task types."""
    CART_GENERATION = "cart_generation"
    INTENT_CLASSIFICATION = "intent_classification"
    READINESS_SCORING = "readiness_scoring"
    VOICE = "voice"
    AGENTIC = "agentic"


# Routing: task → [primary, fallback1, fallback2]
_ROUTING_TABLE: dict[Task, list[str]] = {
    Task.CART_GENERATION: ["nova_pro", "llama", "nova_lite"],
    Task.INTENT_CLASSIFICATION: ["nova_lite", "nova_pro", "llama"],
    Task.READINESS_SCORING: ["nova_lite", "nova_pro", "llama"],
    Task.VOICE: ["nova_sonic"],
    Task.AGENTIC: ["nemotron_super", "llama"],
}

# ─── Client Factory (cached) ──────────────────────────────────────────────────

_client_cache: dict[str, Any] = {}


def get_client(region: str):
    """Get or create a cached boto3 bedrock-runtime client for the given region."""
    if region not in _client_cache:
        logger.info(f"Creating Bedrock client for region: {region}")
        _client_cache[region] = boto3.client(
            "bedrock-runtime",
            region_name=region,
        )
    return _client_cache[region]


# ─── Core Invocation ───────────────────────────────────────────────────────────

def _invoke_model(
    model_key: str,
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> dict:
    """Invoke a specific model via Bedrock Converse API.

    Returns dict with: text, usage, latency, model
    Raises on failure.
    """
    config = MODEL_CONFIG[model_key]
    region = config["region"]
    model_id = config["model_id"]
    tokens = max_tokens or config["max_tokens"]

    client = get_client(region)
    start = time.time()

    response = client.converse(
        modelId=model_id,
        messages=messages,
        inferenceConfig={
            "maxTokens": tokens,
            "temperature": temperature,
        },
    )

    latency = time.time() - start

    # Extract text from response
    output = response.get("output", {})
    message = output.get("message", {})
    content_blocks = message.get("content", [])

    text = ""
    for block in content_blocks:
        if "text" in block:
            text += block["text"]

    # Log metrics
    usage = response.get("usage", {})
    stop_reason = response.get("stopReason", "?")
    logger.info(
        f"Model={model_key} Region={region} "
        f"Latency={latency:.2f}s "
        f"In={usage.get('inputTokens', '?')} "
        f"Out={usage.get('outputTokens', '?')} "
        f"Stop={stop_reason}"
    )

    if not text:
        raise ValueError(f"Empty response from {model_key}. StopReason={stop_reason}")

    return {"text": text, "usage": usage, "latency": latency, "model": model_key}


# ─── Public API ────────────────────────────────────────────────────────────────

def invoke(
    task: Task,
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> dict:
    """Route a task to the appropriate model with automatic fallback.

    Returns dict with: text, usage, latency, model
    Raises RuntimeError if all models fail.
    """
    chain = _ROUTING_TABLE.get(task, ["nova_pro", "nova_lite", "llama"])
    errors: list[str] = []

    for model_key in chain:
        try:
            result = _invoke_model(model_key, messages, temperature, max_tokens)
            if errors:
                logger.warning(
                    f"Task={task.value} recovered via {model_key} "
                    f"after {len(errors)} failures"
                )
            return result
        except Exception as e:
            reason = f"{model_key}: {type(e).__name__}: {str(e)[:120]}"
            errors.append(reason)
            logger.warning(f"Fallback triggered: {reason}")
            continue

    raise RuntimeError(
        f"All models failed for task={task.value}. Errors: {errors}"
    )


def invoke_json(
    task: Task,
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> dict:
    """Invoke and parse response as JSON with robust extraction.

    Returns dict with: text, usage, latency, model, parsed
    """
    result = invoke(task, messages, temperature, max_tokens)
    raw = result["text"].strip()

    # Strip markdown fences
    raw = (
        raw.removeprefix("```json")
           .removeprefix("```")
           .removesuffix("```")
           .strip()
    )

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: extract first JSON object via regex
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            raise

    return {**result, "parsed": parsed}


def get_model_info(task: Task) -> dict:
    """Debug/health info for a task's routing."""
    chain = _ROUTING_TABLE.get(task, ["nova_pro"])
    primary = chain[0]
    config = MODEL_CONFIG[primary]
    return {
        "task": task.value,
        "primary_model": primary,
        "model_id": config["model_id"],
        "region": config["region"],
        "fallback_chain": chain,
    }

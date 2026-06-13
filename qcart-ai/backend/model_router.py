"""Multi-Region Bedrock Model Router.

Routes inference requests to the correct AWS region based on model availability.
Implements automatic fallback, retry logic, and client caching.

Usage:
    from model_router import invoke, Task

    result = invoke(Task.CART_GENERATION, messages=[...])
"""

import json
import logging
import os
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

# ─── Configuration ─────────────────────────────────────────────────────────────

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

MODEL_CONFIG = {
    "nova_lite": {
        "region": os.getenv("NOVA_LITE_REGION", "us-east-1"),
        "model_id": os.getenv("NOVA_LITE_MODEL_ID", "us.amazon.nova-lite-v1:0"),
        "max_tokens": 4096,
    },
    "nova_sonic": {
        "region": os.getenv("NOVA_SONIC_REGION", "us-east-1"),
        "model_id": os.getenv("NOVA_SONIC_MODEL_ID", "us.amazon.nova-sonic-v1:0"),
        "max_tokens": 4096,
    },
    "llama_70b": {
        "region": os.getenv("LLAMA_REGION", "us-east-1"),
        "model_id": os.getenv("LLAMA_MODEL_ID", "us.meta.llama3-3-70b-instruct-v1:0"),
        "max_tokens": 4096,
    },
    "mistral_large": {
        "region": os.getenv("MISTRAL_REGION", "us-east-1"),
        "model_id": os.getenv("MISTRAL_MODEL_ID", "mistral.mistral-large-2407-v1:0"),
        "max_tokens": 4096,
    },
    "gpt_oss_120b": {
        "region": os.getenv("GPT_OSS_REGION", "us-east-1"),
        "model_id": os.getenv("GPT_OSS_MODEL_ID", "us.amazon.nova-premier-v1:0"),
        "max_tokens": 8192,
    },
    "nemotron_super": {
        "region": os.getenv("NEMOTRON_REGION", "us-east-1"),
        "model_id": os.getenv("NEMOTRON_MODEL_ID", "us.nvidia.nemotron-4-340b-instruct-v1:0"),
        "max_tokens": 4096,
    },
}

# ─── Task → Model Routing ─────────────────────────────────────────────────────


class Task(str, Enum):
    """Tasks that can be routed to different models."""
    INTENT_CLASSIFICATION = "intent_classification"
    CART_GENERATION = "cart_generation"
    READINESS_SCORING = "readiness_scoring"
    GAP_ANALYSIS = "gap_analysis"
    PREMIUM_DEMO = "premium_demo"
    VOICE = "voice"
    AGENTIC = "agentic"


# Routing table: task → primary model, fallback chain
_ROUTING_TABLE: dict[Task, list[str]] = {
    Task.INTENT_CLASSIFICATION: ["nova_lite", "llama_70b", "mistral_large"],
    Task.CART_GENERATION: ["llama_70b", "nova_lite", "mistral_large"],
    Task.READINESS_SCORING: ["nova_lite", "llama_70b", "mistral_large"],
    Task.GAP_ANALYSIS: ["nova_lite", "llama_70b", "mistral_large"],
    Task.PREMIUM_DEMO: ["gpt_oss_120b", "llama_70b", "mistral_large"],
    Task.VOICE: ["nova_sonic"],
    Task.AGENTIC: ["nemotron_super", "llama_70b"],
}

# Override: in demo mode, premium tasks use the premium model
if DEMO_MODE:
    _ROUTING_TABLE[Task.CART_GENERATION] = ["gpt_oss_120b", "llama_70b", "mistral_large"]


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
    """Invoke a specific model and return the parsed response.

    Raises Exception on failure (timeout, invalid response, etc.)
    """
    config = MODEL_CONFIG[model_key]
    region = config["region"]
    model_id = config["model_id"]
    tokens = max_tokens or config["max_tokens"]

    client = get_client(region)

    # Build the request body (Bedrock Converse API format)
    body = {
        "messages": messages,
        "inferenceConfig": {
            "maxTokens": tokens,
            "temperature": temperature,
        },
    }

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

    # Extract content
    output = response.get("output", {})
    message = output.get("message", {})
    content_blocks = message.get("content", [])

    text = ""
    for block in content_blocks:
        if "text" in block:
            text += block["text"]

    # Log metrics
    usage = response.get("usage", {})
    logger.info(
        f"Model={model_key} Region={region} "
        f"Latency={latency:.2f}s "
        f"InputTokens={usage.get('inputTokens', '?')} "
        f"OutputTokens={usage.get('outputTokens', '?')} "
        f"StopReason={response.get('stopReason', '?')}"
    )

    if not text:
        raise ValueError(
            f"Model '{model_key}' returned empty content. "
            f"StopReason={response.get('stopReason')}"
        )

    return {"text": text, "usage": usage, "latency": latency, "model": model_key}


# ─── Public API ────────────────────────────────────────────────────────────────

def invoke(
    task: Task,
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> dict:
    """Route a task to the appropriate model with automatic fallback.

    Args:
        task: The task type to route.
        messages: Bedrock Converse API message format.
        temperature: Sampling temperature.
        max_tokens: Override max tokens (uses model default if None).

    Returns:
        dict with keys: text, usage, latency, model

    Raises:
        RuntimeError: If all models in the fallback chain fail.
    """
    chain = _ROUTING_TABLE.get(task, ["nova_lite", "mistral_large"])
    errors: list[str] = []

    for model_key in chain:
        try:
            result = _invoke_model(model_key, messages, temperature, max_tokens)
            if errors:
                logger.warning(
                    f"Task={task.value} succeeded on fallback model={model_key} "
                    f"after {len(errors)} failures: {errors}"
                )
            return result
        except Exception as e:
            reason = f"{model_key}: {type(e).__name__}: {str(e)[:100]}"
            errors.append(reason)
            logger.warning(f"Task={task.value} model={model_key} failed: {reason}")
            continue

    raise RuntimeError(
        f"All models failed for task={task.value}. "
        f"Chain={chain}. Errors={errors}"
    )


def invoke_json(
    task: Task,
    messages: list[dict],
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> dict:
    """Invoke and parse the response as JSON.

    Attempts JSON extraction with fallback regex if direct parse fails.
    """
    import re

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
        # Fallback: extract first JSON object
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
        else:
            raise

    return {**result, "parsed": parsed}


def get_model_info(task: Task) -> dict:
    """Get the primary model config for a task (for health/debug endpoints)."""
    chain = _ROUTING_TABLE.get(task, ["nova_lite"])
    primary = chain[0]
    config = MODEL_CONFIG[primary]
    return {
        "task": task.value,
        "primary_model": primary,
        "model_id": config["model_id"],
        "region": config["region"],
        "fallback_chain": chain,
        "demo_mode": DEMO_MODE,
    }

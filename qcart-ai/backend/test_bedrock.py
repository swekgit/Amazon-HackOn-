"""Minimal Bedrock connectivity verification via model_router.

Usage:
    cd backend
    python test_bedrock.py
"""

import sys
import traceback

sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from model_router import invoke, Task, get_model_info

def main():
    print("=" * 50)
    print("Bedrock Router Connectivity Test")
    print("=" * 50)

    # Show routing info
    info = get_model_info(Task.INTENT_CLASSIFICATION)
    print(f"\nTask: {info['task']}")
    print(f"Primary model: {info['primary_model']}")
    print(f"Model ID: {info['model_id']}")
    print(f"Region: {info['region']}")
    print(f"Fallback chain: {info['fallback_chain']}")

    # Call the model
    print("\nSending: 'Say hello in one sentence'...")
    print("-" * 50)

    messages = [
        {
            "role": "user",
            "content": [{"text": "Say hello in one sentence."}],
        }
    ]

    result = invoke(Task.INTENT_CLASSIFICATION, messages)

    print(f"\nSelected model: {result['model']}")
    print(f"Response text:  {result['text']}")
    print(f"Latency:        {result['latency']:.2f}s")
    print(f"Token usage:    {result['usage']}")
    print("\n✓ Bedrock connectivity verified!")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\n✗ FAILED")
        traceback.print_exc()
        sys.exit(1)

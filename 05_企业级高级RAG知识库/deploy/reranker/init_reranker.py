"""
Reranker model init script for XInference
Run this after XInference container is up and healthy
"""

import requests
import time
import sys
import json

XINFERENCE_URL = "http://localhost:9997"
MODEL_NAME = "bge-reranker-large"
MODEL_UID = "bge-reranker-large"

def wait_for_xinference(max_retries=30, interval=5):
    """Wait for XInference to be ready."""
    print("Waiting for XInference to be ready...")
    for i in range(max_retries):
        try:
            resp = requests.get(f"{XINFERENCE_URL}/v1/models", timeout=5)
            if resp.status_code == 200:
                print("XInference is ready!")
                return True
        except requests.ConnectionError:
            pass
        print(f"  Retry {i+1}/{max_retries}...")
        time.sleep(interval)
    print("ERROR: XInference did not become ready.")
    return False

def check_model_exists():
    """Check if the reranker model is already registered."""
    try:
        resp = requests.get(f"{XINFERENCE_URL}/v1/models", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("data", [])
            for m in models:
                if m.get("id", "").startswith(MODEL_NAME):
                    print(f"Model '{MODEL_NAME}' already registered.")
                    return True
    except Exception as e:
        print(f"Error checking models: {e}")
    return False

def register_reranker():
    """Register bge-reranker-large model in XInference."""
    print(f"Registering model '{MODEL_NAME}'...")
    payload = {
        "model_name": MODEL_NAME,
        "model_type": "rerank",
        "model_uid": MODEL_UID,
    }
    try:
        resp = requests.post(
            f"{XINFERENCE_URL}/v1/models",
            json=payload,
            timeout=300,
        )
        if resp.status_code in (200, 201):
            print(f"Model '{MODEL_NAME}' registered successfully!")
            print(f"Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"ERROR: Registration failed. Status: {resp.status_code}")
            print(f"Response: {resp.text}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_reranker():
    """Quick test of the reranker service."""
    print("\nTesting reranker...")
    payload = {
        "model": MODEL_UID,
        "query": "\u9ad8\u8840\u538b\u7684\u6cbb\u7597\u65b9\u6cd5",
        "documents": [
            "\u9ad8\u8840\u538b\u60a3\u8005\u5e94\u6539\u53d8\u751f\u6d3b\u65b9\u5f0f\uff0c\u5305\u62ec\u4f4e\u76d0\u996e\u98df\u3001\u9002\u91cf\u8fd0\u52a8\u3001\u6212\u70df\u9650\u9152\u3002",
            "\u611f\u5192\u7684\u4e3b\u8981\u75c7\u72b6\u5305\u62ec\u9f3b\u585e\u3001\u6d41\u6d95\u3001\u54bd\u75db\u3002",
        ],
        "top_n": 2,
    }
    try:
        resp = requests.post(
            f"{XINFERENCE_URL}/v1/rerank",
            json=payload,
            timeout=60,
        )
        if resp.status_code == 200:
            result = resp.json()
            print(f"Reranker test passed! Results:")
            for item in result.get("results", []):
                print(f"  Score: {item['relevance_score']:.4f} | Text: {item['document']['text'][:50]}...")
            return True
        else:
            print(f"Test failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"Test error: {e}")
        return False

if __name__ == "__main__":
    if not wait_for_xinference():
        sys.exit(1)

    if not check_model_exists():
        if not register_reranker():
            sys.exit(1)

    test_reranker()
    print("\nReranker initialization complete!")

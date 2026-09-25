# test_llm.py
from core.llm import call_llm, MODELS

def test_all_models():
    prompt = "Reply with exactly one sentence confirming you are online and which model you are."
    
    for model_name in ["nano", "super", "ultra"]:
        print(f"\n🔄 Testing {model_name.upper()} ({MODELS[model_name]})...")
        try:
            response = call_llm(prompt=prompt, model=model_name, max_tokens=100)
            print(f"✅ {model_name.upper()}: {response}")
        except Exception as e:
            print(f"❌ {model_name.upper()} FAILED: {e}")

if __name__ == "__main__":
    print("=== DriftWatch LLM Connection Test ===")
    test_all_models()
    print("\n=== Test Complete ===")
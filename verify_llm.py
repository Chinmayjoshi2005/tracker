
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from llm_service import OllamaLLMService

def test_service():
    print("Testing LLM Service Configuration...")
    
    # Check for API Key in env
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        print(f"✅ GEMINI_API_KEY found: {api_key[:5]}...{api_key[-5:]}")
    else:
        print("❌ GEMINI_API_KEY not found in environment variables.")

    try:
        service = OllamaLLMService()
        
        if service.use_gemini:
            print("✅ Service initialized with Gemini enabled.")
        else:
            print("⚠️ Service initialized with Gemini DISABLED (using Ollama fallback).")
            
        print(f"LLM Status Check: {service.check_llm_status()}")
        
    except Exception as e:
        print(f"❌ Error initializing service: {e}")

if __name__ == "__main__":
    test_service()

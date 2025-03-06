import google.generativeai as genai
from .config import load_config

# Load configuration
config = load_config()

# Configure API Key
genai.configure(api_key=config["GEMINI_API_KEY"])

def fetch_intent_from_genai(text):
    prompt = f"Analyze the intent of the following text and return the most relevant category.\nText: '{text}'\nIntent:"
    try:
        # Get the Gemini model
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Generate response
        response = model.generate_content(prompt)

        # Extract and clean up the response text
        intent = response.text.strip().lower() if response and response.text else "unknown"
        
        return intent
    except Exception as e:
        print(f"Error fetching intent from GenAI: {e}")
        return "unknown"
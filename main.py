import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_headers = ["*"], 
    allow_methods = ["*"],
    allow_credentials = True,
)

api_key = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=api_key)

bot_settings = {
    "knowledge_base_text": "Atome Card is a payment card. Applications take 3-5 days to process.", 
    "additional_guidelines": "Always be extremely polite and empathetic. If a transaction fails, apologize."
}

def get_application_status(application_id: str):
    """Call this function to get the application status when a user asks about their card application."""
    # Mock behavior
    return {"status": "Pending Verification", "application_id": application_id}

def get_card_transaction_status(transaction_id: str):
    """Call this function to get the status of a failed card transaction."""
    # Mock behavior
    return {"status": "Failed - Insufficient Funds", "transaction_id": transaction_id}

dynamic_system_prompt = f"""
You are a helpful customer service AI bot for Atome.

KNOWLEDGE BASE:
{bot_settings["knowledge_base_text"]}

ADDITIONAL GUIDELINES:
{bot_settings["additional_guidelines"]}
"""

# 3. Create the model instance inside the chat route so it gets the freshest context
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    tools=[get_application_status, get_card_transaction_status],
    system_instruction=dynamic_system_prompt
)

chat_session = model.start_chat(enable_automatic_function_calling=True)

class ChatRequest(BaseModel):
    message: str

@app.get("/health", status_code=200)
def get_health():
    return {"health": "OK"}

@app.post("/chat", status_code=201)
def send_message(req: ChatRequest):
    try:
        response = chat_session.send_message(req.message)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"Sorry I encountered a problem {str(e)}"}
    
@app.post("/update_bot", status_code=201)

class BotSettings(BaseModel):
    knowledge_base:str
    additional_guidelines:str

def update_bot(req: BotSettings):
    if req.knowledge_base:
        bot_settings["knowledge_base_text"] = req.knowledge_base
    if req.additional_guidelines:
        bot_settings["additional_guidelines"] = req.additional_guidelines

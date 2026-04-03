import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import json
import uuid

DB_FILE = "bot_data.json"

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

active_chat_sessions = {}

def load_json_db():
    if not os.path.exists(DB_FILE):
        return {
            "knowledge_base": "Atome Card is a payment card. Applications take 3-5 days to process.",
            "guidelines": "Always be extremely polite and empathetic. If a transaction fails, apologize.",
            "mistakes": []
        }
    with open(DB_FILE, "r") as f:
        return json.load(f)
def save_json_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_application_status(application_id: str):
    # Mock behavior
    return {"status": "Pending Verification", "application_id": application_id}

def get_card_transaction_status(transaction_id: str):
    return {"status": "Failed - Insufficient Funds", "transaction_id": transaction_id}

class ChatRequest(BaseModel):
    message: str
    session_id:str

@app.get("/health", status_code=200)
def get_health():
    return {"health": "OK"}

@app.post("/chat", status_code=201)
def send_message(req: ChatRequest):
    try:
        json_data = load_json_db()
        dynamic_system_prompt = f"""
        You are a helpful customer service AI bot for Atome.
        KNOWLEDGE BASE: {json_data["knowledge_base"]}
        ADDITIONAL GUIDELINES: {json_data["guidelines"]}
        """
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            tools=[get_application_status, get_card_transaction_status],
            system_instruction=dynamic_system_prompt
        )
        chat_session = model.start_chat(enable_automatic_function_calling=True, history=active_chat_sessions.get(req.session_id, []))

        response = chat_session.send_message(req.message)
        active_chat_sessions[req.session_id] = chat_session.history
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"Sorry I encountered a problem {str(e)}"}
    
class BotSettings(BaseModel):
    knowledge_base:str
    additional_guidelines:str

@app.post("/update_bot", status_code=201)
def update_bot(req: BotSettings):
    try:
        json_data = load_json_db()

        if req.knowledge_base:
            json_data["knowledge_base"] = req.knowledge_base
        if req.additional_guidelines:
            json_data["guidelines"] = req.additional_guidelines
            
        save_json_db(json_data)
        return {"status": "Bot settings updated successfully!"}
    except Exception as e:
        return {"status": f"Error: {str(e)}"}

class BadResponse(BaseModel):
    past_messages:str
    bad_message: str

@app.post("/report_message", status_code=201)
def report_message(req: BadResponse):
    # Here you would typically save this to a database or send it to a monitoring service
    try:
        auditor_model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        audit_prompt = f"""
        You are an AI system auditor. 
        Read this chat history: {req.past_messages}
        
        The customer flagged this specific message from the bot as a mistake or unhelpful: 
        "{req.bad_message}"
        
        Figure out what the bot did wrong. Then, write a single, short, clear guideline (1-2 sentences) 
        that should be added to the bot's system instructions so it never makes this mistake again.
        Do not apologize. ONLY output the new rule.
        """
        response = auditor_model.generate_content(audit_prompt)
        new_rule = response.text.strip()

        json_data = load_json_db()
        json_data["guidelines"] += f"\n {new_rule}"
        mistake_entry = {
            "bad_message": req.bad_message,
            "fix": new_rule
        }
        json_data["mistakes"].append(mistake_entry)
        save_json_db(json_data)
        return {"status": "Report received",}
    except Exception as e:
        return {"status": f"Error: {str(e)}"}

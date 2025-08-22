from fastapi import FastAPI, Request, HTTPException
import os
import json
from src.webhook_processor import process_webhook_event

# Create an instance of the FastAPI app
app = FastAPI()

# This ensures that our app is configured on startup with external data.
CONFIG_FILE = "config.json"
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        LINE_USER_MAP = config.get("line_user_map", {})
        USER_CONFIGS = config.get("user_configs", {})
except FileNotFoundError:
    print(f"Error: Configuration file '{CONFIG_FILE}' not found.")
    LINE_USER_MAP = {}
    USER_CONFIGS = {}
except json.JSONDecodeError:
    print(f"Error: Invalid JSON format in '{CONFIG_FILE}'.")
    LINE_USER_MAP = {}
    USER_CONFIGS = {}

# A simple root endpoint for a health check
@app.get("/")
def read_root():
    return {"message": "Image Upload Service is running"}

# The main webhook endpoint to receive events from LINE
@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        print("Received webhook event:", data)
        
        # We process each event in the payload.
        events = data.get("events", [])
        
        for event in events:
            # --- USE THE GLOBAL CONFIGS LOADED ON STARTUP ---
            result = process_webhook_event(event, LINE_USER_MAP, USER_CONFIGS)
            if result:
                print(f"Successfully processed event. Uploaded file ID: {result}")
        
        return {"status": "success", "message": "Event processed successfully"}
    
    except json.JSONDecodeError:
        print("Error: Invalid JSON format")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
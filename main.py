from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import os
import json
from dotenv import load_dotenv
from src.webhook_processor import process_webhook_event
# --- NEW IMPORTS from LINE SDK v3 ---
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import AsyncApiClient, AsyncMessagingApi, Configuration
from linebot.v3.exceptions import InvalidSignatureError
import logging
import sys


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
# Load environment variables from .env file
load_dotenv()

# Create an instance of the FastAPI app
app = FastAPI()

# Load configuration from file
CONFIG_FILE = "config.json"
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        LINE_USER_MAP = config.get("line_user_map", {})
        USER_CONFIGS = config.get("user_configs", {})
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading config file: {e}")
    LINE_USER_MAP = {}
    USER_CONFIGS = {}

# --- NEW: LINE SDK v3 setup ---
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
parent_folder_id = os.getenv('PARENT_FOLDER_ID', None)
if not channel_secret or not channel_access_token:
    raise RuntimeError("LINE_CHANNEL_SECRET or LINE_CHANNEL_ACCESS_TOKEN not found.")

configuration = Configuration(access_token=channel_access_token)
async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)

@app.get("/")
def read_root():
    return {"message": "Image Upload Service is running"}

@app.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        signature = request.headers['X-Line-Signature']
        body = (await request.body()).decode('utf-8')
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    for event in events:
        background_tasks.add_task(
            process_webhook_event, 
            event,               
            LINE_USER_MAP,       
            USER_CONFIGS,        
            line_bot_api,        
            channel_access_token,
            parent_folder_id 
        )
            
    return "OK"
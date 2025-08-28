from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Response
import os
import json
from dotenv import load_dotenv
from src.webhook_processor import process_webhook_event
from src.state_manager import StateManager
from src.config_manager import ConfigManager
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import AsyncApiClient, AsyncMessagingApi, Configuration
from linebot.v3.exceptions import InvalidSignatureError
import logging
import sys
import sentry_sdk 

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
load_dotenv()

sentry_dsn = os.getenv('SENTRY_DSN', None)
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
    )

app = FastAPI()

# --- NEW: Load config and initialize managers ---
CONFIG_FILE = os.getenv('CONFIG_FILE_PATH', 'config.json')
try:
    with open(CONFIG_FILE, 'r') as f:
        config_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    logging.error(f"Error loading config file: {e}")
    config_data = {}

# Create singleton instances of our managers
app.state_manager = StateManager()
app.config_manager = ConfigManager(config_data)
# --- END NEW ---

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
    # This is a test comment for the CI/CD pipeline.
    return {"message": "Stateful Image Upload Service is running"}

@app.head("/")
def head_root():
    return Response(status_code=200)

@app.api_route("/health", methods=["GET", "HEAD"], status_code=200)
def health_check():
    """A simple endpoint to confirm the service is up and handle HEAD requests."""
    return {"status": "ok"}

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
        # Pass manager instances to the processing function
        background_tasks.add_task(
            process_webhook_event,
            event=event,
            state_manager=app.state_manager,
            config_manager=app.config_manager,
            line_bot_api=line_bot_api,
            channel_access_token=channel_access_token,
            parent_folder_id=parent_folder_id
        )

    return "OK"

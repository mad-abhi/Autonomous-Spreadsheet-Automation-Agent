import os
import json
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

from backend.tools.excel_com import create_and_style_excel
from backend.tools.gsheets import upload_to_google_sheets

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in the .env file.")

client = genai.Client(api_key=api_key)

# Define tools
tools = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="generate_dataset",
                description="Generates tabular records based on user request.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "records": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.OBJECT),
                            description="A list of key-value row items."
                        )
                    },
                    required=["records"]
                )
            ),
            types.FunctionDeclaration(
                name="create_styled_excel",
                description="Creates and styles an Excel file using Windows COM.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "filename": types.Schema(type=types.Type.STRING),
                        "data": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.OBJECT)
                        )
                    },
                    required=["filename", "data"]
                )
            ),
            types.FunctionDeclaration(
                name="upload_to_google_sheets",
                description="Uploads dataset to Google Sheets and returns live URL.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "title": types.Schema(type=types.Type.STRING),
                        "data": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.OBJECT)
                        )
                    },
                    required=["title", "data"]
                )
            )
        ]
    )
]

SYSTEM_INSTRUCTION = """You are an Autonomous Spreadsheet Automation Agent.
1. When asked to generate data, call `generate_dataset` to formulate realistic rows.
2. If Excel is requested, call `create_styled_excel` with the dataset.
3. If Google Sheets is requested, call `upload_to_google_sheets` with the dataset.
4. If both are requested, execute both tools sequentially.
5. Provide a crisp summary once all operations are complete.
"""

async def send_message_with_retry(chat, message, emit_callback, max_retries=3):
    """Sends a message to the Gemini chat with exponential backoff on 503/429 errors."""
    for attempt in range(1, max_retries + 1):
        try:
            return chat.send_message(message)
        except APIError as e:
            if e.code in [503, 429] and attempt < max_retries:
                wait_time = attempt * 2
                await emit_callback({
                    "type": "thought",
                    "message": f"Server busy ({e.code}). Retrying in {wait_time}s (Attempt {attempt}/{max_retries})..."
                })
                await asyncio.sleep(wait_time)
            else:
                raise e

async def run_agent(prompt: str, emit_callback):
    await emit_callback({
        "type": "thought", 
        "message": f"Analyzing task: '{prompt}'..."
    })

    # Start chat session
    chat = client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=tools,
            temperature=0.2
        )
    )

    response = await send_message_with_retry(chat, prompt, emit_callback)
    dataset_cache = []

    while response.function_calls:
        for call in response.function_calls:
            name = call.name
            args = call.args
            
            await emit_callback({
                "type": "action", 
                "tool": name, 
                "args": args
            })

            result = {}

            if name == "generate_dataset":
                dataset_cache = args.get("records", [])
                result = {"status": "success", "count": len(dataset_cache)}
                await emit_callback({
                    "type": "data_generated", 
                    "data": dataset_cache
                })

            elif name == "create_styled_excel":
                data_to_write = args.get("data") or dataset_cache
                filename = args.get("filename", "output.xlsx")
                if not filename.endswith(".xlsx"):
                    filename += ".xlsx"
                
                os.makedirs("output", exist_ok=True)
                save_path = os.path.join("output", filename)
                
                abs_path = create_and_style_excel(save_path, data_to_write)
                result = {"status": "success", "local_path": abs_path}
                await emit_callback({
                    "type": "excel_created", 
                    "path": abs_path, 
                    "filename": filename
                })

            elif name == "upload_to_google_sheets":
                data_to_upload = args.get("data") or dataset_cache
                title = args.get("title", "Autonomous Spreadsheet")
                
                sheet_url = upload_to_google_sheets(title, data_to_upload)
                result = {"status": "success", "url": sheet_url}
                await emit_callback({
                    "type": "gsheet_created", 
                    "url": sheet_url
                })

            # Send function response with automatic retry
            response = await send_message_with_retry(
                chat,
                types.Part.from_function_response(
                    name=name,
                    response=result
                ),
                emit_callback
            )

    await emit_callback({
        "type": "completed", 
        "summary": response.text
    })
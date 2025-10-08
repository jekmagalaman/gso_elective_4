# apps/ai_service/inference_server.py
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import subprocess, os
from dotenv import load_dotenv

# === LOAD ENV ===
load_dotenv()  # <-- this will load AI_API_URL and AI_API_KEY from your .env

# === CONFIG ===
API_KEY = os.environ.get("AI_API_KEY", "changeme")
MODEL_NAME = "phi3"  # Ollama model name
OLLAMA_PATH = r"C:\Users\CLIENT\AppData\Local\Programs\Ollama\ollama.exe"  # full path

# === APP INIT ===
app = FastAPI(title="GSO Private AI Service (Phi-3 via Ollama)")

# === DATA SCHEMA ===
class RequestData(BaseModel):
    prompt: str
    max_length: int = 150  # optional, not used by Ollama directly

# === API ROUTE ===
@app.post("/v1/generate")
async def generate(data: RequestData, x_api_key: str = Header(None)):
    # --- Authorization ---
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # --- Input validation ---
    if len(data.prompt) > 1000:
        raise HTTPException(status_code=400, detail="Prompt too long")

    try:
        # --- Call Ollama ---
        result = subprocess.run(
            [OLLAMA_PATH, "run", MODEL_NAME, data.prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",  # ⚡ Windows encoding fix
            timeout=120
        )

        # --- Handle subprocess errors ---
        if result.returncode != 0:
            err_msg = result.stderr.strip() or "Unknown subprocess error"
            raise Exception(err_msg)

        output = result.stdout.strip()
        if not output:
            output = "[AI Error] Model returned empty output."

        return {"result": output}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Model request timed out")
    except Exception as e:
        # Log full exception for debugging
        print(f"[AI Error] {e}")
        raise HTTPException(status_code=500, detail=f"Model error: {str(e)}")

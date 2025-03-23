from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import aiohttp
import asyncio
from model_manager import ModelType

app = FastAPI(title="ComfyUI Lightning Studio")

# Serve static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Data models
class ModelSearchRequest(BaseModel):
    query: str
    source: str  # "civitai" or "huggingface"
    model_type: Optional[str] = None
    flux_only: bool = False
    limit: int = 20

class GenerationRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    model_name: str
    steps: int = 20
    cfg_scale: float = 7.0
    width: int = 512
    height: int = 512
    seed: Optional[int] = None

@app.get("/api/models")
async def list_models(model_type: Optional[str] = None):
    """List all available models"""
    try:
        models = app.comfy_ui.list_models(
            ModelType(model_type) if model_type else None
        )
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/models/search")
async def search_models(request: ModelSearchRequest):
    """Search for models from various sources"""
    try:
        if request.source == "civitai":
            models = app.comfy_ui.search_civitai(
                request.query,
                request.model_type,
                limit=request.limit
            )
        elif request.source == "huggingface":
            models = app.comfy_ui.search_huggingface(
                request.query,
                ModelType(request.model_type) if request.model_type else None,
                request.flux_only,
                request.limit
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid source")
        
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/models/download")
async def download_model(model_data: Dict):
    """Download a model from the specified source"""
    try:
        source = model_data.pop("source")
        if source == "civitai":
            model_name = app.comfy_ui.download_civitai_model(model_data)
        elif source == "huggingface":
            model_name = app.comfy_ui.download_huggingface_model(model_data)
        else:
            raise HTTPException(status_code=400, detail="Invalid source")
        
        return {"status": "success", "model_name": model_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def generate_image(request: GenerationRequest):
    """Generate an image using ComfyUI"""
    try:
        # ComfyUI API endpoint
        api_url = f"{app.comfy_ui.url}/api/predict"
        
        # Prepare workflow
        workflow = {
            "prompt": request.prompt,
            "negative_prompt": request.negative_prompt,
            "model": request.model_name,
            "steps": request.steps,
            "cfg_scale": request.cfg_scale,
            "width": request.width,
            "height": request.height,
            "seed": request.seed
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=workflow) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail="ComfyUI generation failed"
                    )
                result = await response.json()
                return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/lora")
async def upload_lora(file: UploadFile = File(...)):
    """Upload a custom LoRA file"""
    try:
        # Save uploaded file
        file_path = os.path.join("uploads", file.filename)
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Add to model manager
        model_name = app.comfy_ui.add_model(
            name=os.path.splitext(file.filename)[0],
            model_type=ModelType.LORA,
            source="custom",
            file_path=file_path
        )
        
        return {"status": "success", "model_name": model_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

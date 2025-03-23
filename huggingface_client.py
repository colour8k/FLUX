import os
from typing import List, Optional, Dict
from dataclasses import dataclass
from huggingface_hub import HfApi, snapshot_download
from model_manager import ModelType

@dataclass
class HuggingFaceModel:
    id: str  # repo_id
    name: str
    type: ModelType
    description: str
    downloads: int
    likes: int
    tags: List[str]
    pipeline_tag: Optional[str] = None

class HuggingFaceClient:
    def __init__(self, token: Optional[str] = None):
        """Initialize the Hugging Face client"""
        self.token = token or os.getenv("HUGGINGFACE_TOKEN")
        self.api = HfApi(token=self.token)

    def search_models(self, query: str, model_type: ModelType = None, flux_only: bool = False, limit: int = 20) -> List[HuggingFaceModel]:
        """Search for models on Hugging Face"""
        # Set up search parameters
        search_params = {
            "search": query,
            "filter": "task:text-to-image",
            "limit": limit
        }
        
        if flux_only:
            search_params["author"] = "FluxML"
        
        # Perform the search
        results = self.api.list_models(**search_params)
        
        # Convert results to HuggingFaceModel objects
        models = []
        for model in results:
            model_type_mapped = self._map_model_type(model.pipeline_tag) if model.pipeline_tag else ModelType.CHECKPOINT
            if model_type and model_type != model_type_mapped:
                continue
                
            models.append(HuggingFaceModel(
                id=model.id,
                name=model.modelId,
                type=model_type_mapped,
                description=model.description or "",
                downloads=getattr(model, "downloads", 0),
                likes=getattr(model, "likes", 0),
                tags=model.tags,
                pipeline_tag=model.pipeline_tag
            ))
        
        return models

    def download_model(self, model_id: str) -> str:
        """Download a model from Hugging Face"""
        local_dir = snapshot_download(
            repo_id=model_id,
            token=self.token,
            local_dir=os.path.join("models", "huggingface", model_id.split("/")[-1])
        )
        return local_dir

    def is_flux_model(self, model_id: str) -> bool:
        """Check if a model is a Flux model"""
        return model_id.startswith("FluxML/") or "flux" in model_id.lower()

    def _map_model_type(self, pipeline_tag: str) -> ModelType:
        """Map Hugging Face pipeline tags to ModelType"""
        tag_mapping = {
            "text-to-image": ModelType.CHECKPOINT,
            "image-to-image": ModelType.CHECKPOINT,
            "controlnet": ModelType.CHECKPOINT,
            "lora": ModelType.LORA,
            "textual-inversion": ModelType.EMBEDDING,
            "vae": ModelType.VAE
        }
        return tag_mapping.get(pipeline_tag, ModelType.CHECKPOINT)

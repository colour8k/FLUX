import os
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass
from model_manager import ModelType

@dataclass
class CivitaiModel:
    id: int
    name: str
    type: str
    description: str
    download_url: str
    version_id: int
    base_model: str
    image_url: Optional[str] = None
    nsfw: bool = False

class CivitaiClient:
    BASE_URL = "https://civitai.com/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def _get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request to Civitai API"""
        response = requests.get(
            f"{self.BASE_URL}/{endpoint}",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

    def search_models(self, query: str, type: str = None, nsfw: bool = False, limit: int = 10) -> List[CivitaiModel]:
        """Search for models on Civitai"""
        params = {
            "query": query,
            "limit": limit,
            "nsfw": nsfw
        }
        if type:
            params["type"] = type

        data = self._get("models", params)
        
        models = []
        for item in data.get("items", []):
            latest_version = item["modelVersions"][0]
            model = CivitaiModel(
                id=item["id"],
                name=item["name"],
                type=item["type"],
                description=item.get("description", ""),
                download_url=latest_version["downloadUrl"],
                version_id=latest_version["id"],
                base_model=latest_version.get("baseModel", "unknown"),
                image_url=latest_version.get("images", [{}])[0].get("url"),
                nsfw=item.get("nsfw", False)
            )
            models.append(model)
        
        return models

    def get_model_info(self, model_id: int) -> CivitaiModel:
        """Get detailed information about a specific model"""
        data = self._get(f"models/{model_id}")
        latest_version = data["modelVersions"][0]
        
        return CivitaiModel(
            id=data["id"],
            name=data["name"],
            type=data["type"],
            description=data.get("description", ""),
            download_url=latest_version["downloadUrl"],
            version_id=latest_version["id"],
            base_model=latest_version.get("baseModel", "unknown"),
            image_url=latest_version.get("images", [{}])[0].get("url"),
            nsfw=data.get("nsfw", False)
        )

    def download_model(self, model: CivitaiModel, target_dir: str) -> str:
        """Download a model file from Civitai"""
        os.makedirs(target_dir, exist_ok=True)
        
        # Determine file extension from URL
        file_ext = os.path.splitext(model.download_url)[1]
        if not file_ext:
            file_ext = ".safetensors"  # Default to safetensors if no extension
        
        target_path = os.path.join(target_dir, f"{model.name}{file_ext}")
        
        # Stream download to avoid memory issues with large files
        response = requests.get(model.download_url, stream=True)
        response.raise_for_status()
        
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return target_path

    @staticmethod
    def map_model_type(civitai_type: str) -> ModelType:
        """Map Civitai model type to internal ModelType"""
        type_mapping = {
            "Checkpoint": ModelType.CHECKPOINT,
            "LORA": ModelType.LORA,
            "TextualInversion": ModelType.EMBEDDING,
            "VAE": ModelType.VAE
        }
        return type_mapping.get(civitai_type, ModelType.CHECKPOINT)

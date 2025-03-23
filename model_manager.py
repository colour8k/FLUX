import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ModelType(Enum):
    CHECKPOINT = "checkpoint"
    LORA = "lora"
    VAE = "vae"
    EMBEDDING = "embedding"

@dataclass
class ModelInfo:
    name: str
    type: ModelType
    source: str
    path: str
    metadata: Dict

class ModelManager:
    def __init__(self, base_path: str = "models"):
        self.base_path = Path(base_path)
        self.models: Dict[str, ModelInfo] = {}
        self._init_directories()
        self._load_model_index()

    def _init_directories(self):
        """Initialize directory structure for different model types"""
        for model_type in ModelType:
            (self.base_path / model_type.value).mkdir(parents=True, exist_ok=True)

    def _load_model_index(self):
        """Load existing model index from disk"""
        index_path = self.base_path / "model_index.json"
        if index_path.exists():
            with open(index_path, "r") as f:
                data = json.load(f)
                for model_data in data.values():
                    self.models[model_data["name"]] = ModelInfo(
                        name=model_data["name"],
                        type=ModelType(model_data["type"]),
                        source=model_data["source"],
                        path=model_data["path"],
                        metadata=model_data.get("metadata", {})
                    )

    def _save_model_index(self):
        """Save current model index to disk"""
        index_path = self.base_path / "model_index.json"
        data = {
            model.name: {
                "name": model.name,
                "type": model.type.value,
                "source": model.source,
                "path": model.path,
                "metadata": model.metadata
            }
            for model in self.models.values()
        }
        with open(index_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_model(self, name: str, model_type: ModelType, source: str, file_path: str, metadata: Dict = None):
        """Add a new model to the manager"""
        if name in self.models:
            raise ValueError(f"Model {name} already exists")

        target_dir = self.base_path / model_type.value
        target_path = str(target_dir / Path(file_path).name)
        
        # Copy or move file to models directory
        if os.path.exists(file_path):
            os.rename(file_path, target_path)
        
        self.models[name] = ModelInfo(
            name=name,
            type=model_type,
            source=source,
            path=target_path,
            metadata=metadata or {}
        )
        self._save_model_index()

    def get_model(self, name: str) -> Optional[ModelInfo]:
        """Retrieve model information by name"""
        return self.models.get(name)

    def list_models(self, model_type: ModelType = None) -> List[ModelInfo]:
        """List all models, optionally filtered by type"""
        if model_type:
            return [m for m in self.models.values() if m.type == model_type]
        return list(self.models.values())

    def remove_model(self, name: str):
        """Remove a model from the manager and delete its files"""
        if name not in self.models:
            raise ValueError(f"Model {name} not found")
        
        model = self.models[name]
        if os.path.exists(model.path):
            os.remove(model.path)
        
        del self.models[name]
        self._save_model_index()

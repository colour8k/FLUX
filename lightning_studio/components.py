from lightning_app import LightningWork, LightningFlow
from typing import Optional, List

class ModelComponent(LightningWork):
    def __init__(self):
        super().__init__()
        self.model_path: Optional[str] = None
        self.model_type: Optional[str] = None
        self.status: str = "idle"

    def run(self, model_path: str, model_type: str):
        self.model_path = model_path
        self.model_type = model_type
        self.status = "loaded"

class StudioFlow(LightningFlow):
    def __init__(self):
        super().__init__()
        self.models: List[ModelComponent] = []
        self.status: str = "initializing"

    def run(self):
        self.status = "running"
        for model in self.models:
            model.run()

    def add_model(self, model_path: str, model_type: str):
        model = ModelComponent()
        model.run(model_path, model_type)
        self.models.append(model)
        return len(self.models) - 1  # Return model index 
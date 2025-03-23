from dataclasses import dataclass
from typing import Optional

@dataclass
class LightningConfig:
    app_name: str = "comfy-lightning-studio"
    work_dir: str = "workspace"
    model_dir: str = "models"
    cache_dir: Optional[str] = None
    
    # Server configurations
    host: str = "127.0.0.1"
    port: int = 7501
    
    # Component configurations
    max_models: int = 10
    model_load_timeout: int = 300  # seconds
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        import os
        return cls(
            app_name=os.getenv("LIGHTNING_APP_NAME", cls.app_name),
            work_dir=os.getenv("LIGHTNING_WORK_DIR", cls.work_dir),
            model_dir=os.getenv("LIGHTNING_MODEL_DIR", cls.model_dir),
            cache_dir=os.getenv("LIGHTNING_CACHE_DIR", cls.cache_dir),
            host=os.getenv("LIGHTNING_HOST", cls.host),
            port=int(os.getenv("LIGHTNING_PORT", cls.port)),
            max_models=int(os.getenv("LIGHTNING_MAX_MODELS", cls.max_models)),
            model_load_timeout=int(os.getenv("LIGHTNING_MODEL_LOAD_TIMEOUT", cls.model_load_timeout))
        ) 
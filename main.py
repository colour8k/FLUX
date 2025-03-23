import os
import subprocess
import time
import threading
from flask import Flask, render_template, request, jsonify
from lightning.app import LightningWork, LightningApp, LightningFlow
from lightning.app.storage import Drive
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComfyUIWork(LightningWork):
    def __init__(self):
        super().__init__(parallel=True, cloud_compute={"gpu": "t4"})
        self.drive = Drive("model_storage")
        self.ready = False

    def setup_environment(self):
        """Set up the environment and install dependencies"""
        try:
            logger.info("Setting up environment...")
            # Create directories
            os.makedirs("templates", exist_ok=True)
            os.makedirs("static", exist_ok=True)
            
            # Clone ComfyUI if not exists
            if not os.path.exists("ComfyUI"):
                logger.info("Cloning ComfyUI repository...")
                subprocess.run(["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git"], check=True)
                os.chdir("ComfyUI")
                logger.info("Installing ComfyUI requirements...")
                subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
                os.chdir("..")
            
            # Create model directories and link to Lightning Drive
            model_types = ["checkpoints", "loras", "controlnet", "vae"]
            for dir_name in model_types:
                dir_path = f"ComfyUI/models/{dir_name}"
                os.makedirs(dir_path, exist_ok=True)
                
                # Sync from drive if exists
                drive_path = f"models/{dir_name}"
                if self.drive.exists(drive_path):
                    logger.info(f"Syncing {dir_name} from Lightning Drive...")
                    self.drive.get(drive_path, dir_path)
            
            logger.info("Environment setup complete")
            return True
        except Exception as e:
            logger.error(f"Error during setup: {str(e)}")
            return False

    def run(self):
        if not self.setup_environment():
            logger.error("Failed to set up environment")
            return

        try:
            os.chdir("ComfyUI")
            self.ready = True
            logger.info("Starting ComfyUI server...")
            subprocess.run(
                ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--enable-cors-header"],
                check=True
            )
        except Exception as e:
            logger.error(f"Error running ComfyUI: {str(e)}")
            self.ready = False

class WebUI(LightningWork):
    def __init__(self):
        super().__init__(parallel=True)
        self.ready = False
        self.drive = Drive("model_storage")

    def run(self):
        app = Flask(__name__, static_folder="static")

        @app.route("/")
        def index():
            return render_template("index.html")

        @app.route("/api/models")
        def list_models():
            try:
                models = []
                for model_type in ["checkpoints", "loras", "controlnet", "vae"]:
                    type_dir = os.path.join("ComfyUI", "models", model_type)
                    if os.path.exists(type_dir):
                        for model in os.listdir(type_dir):
                            model_path = os.path.join(type_dir, model)
                            if os.path.isfile(model_path):
                                models.append({
                                    "name": model,
                                    "type": model_type,
                                    "size": os.path.getsize(model_path)
                                })
                return jsonify({"models": models})
            except Exception as e:
                logger.error(f"Error listing models: {str(e)}")
                return jsonify({"error": "Failed to list models"}), 500

        @app.route("/api/upload", methods=["POST"])
        def upload_model():
            try:
                if "model" not in request.files or "type" not in request.form:
                    return jsonify({"error": "No model file or type provided"}), 400
                
                model_file = request.files["model"]
                model_type = request.form["type"]
                
                if model_file.filename == "":
                    return jsonify({"error": "No model file selected"}), 400
                
                if model_type not in ["checkpoints", "loras", "controlnet", "vae"]:
                    return jsonify({"error": "Invalid model type"}), 400
                
                # Save to local directory first
                models_dir = os.path.join("ComfyUI", "models", model_type)
                os.makedirs(models_dir, exist_ok=True)
                model_path = os.path.join(models_dir, model_file.filename)
                model_file.save(model_path)
                
                # Save to Lightning Drive
                drive_path = f"models/{model_type}/{model_file.filename}"
                logger.info(f"Uploading {model_file.filename} to Lightning Drive...")
                self.drive.put(model_path, drive_path)
                
                return jsonify({"message": f"{model_type} model uploaded successfully"})
            except Exception as e:
                logger.error(f"Error uploading model: {str(e)}")
                return jsonify({"error": "Failed to upload model"}), 500

        try:
            logger.info("Starting Web UI server...")
            self.ready = True
            app.run(host="0.0.0.0", port=7860)
        except Exception as e:
            logger.error(f"Error running Web UI: {str(e)}")
            self.ready = False

class ComfyLightningStudio(LightningFlow):
    def __init__(self):
        super().__init__()
        self.comfyui = ComfyUIWork()
        self.webui = WebUI()

    def run(self):
        try:
            self.comfyui.run()
            if self.comfyui.ready:
                self.webui.run()
        except Exception as e:
            logger.error(f"Error in ComfyLightningStudio: {str(e)}")

    def configure_layout(self):
        return [
            {"name": "ComfyUI", "content": "http://127.0.0.1:8188"},
            {"name": "Web UI", "content": "http://127.0.0.1:7860"}
        ]

app = LightningApp(ComfyLightningStudio()) 
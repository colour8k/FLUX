import os
import subprocess
import time
import threading
from flask import Flask, render_template, request, jsonify
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def setup_environment():
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
        
        # Create model directories
        for dir_name in ["checkpoints", "loras", "controlnet", "vae"]:
            dir_path = f"ComfyUI/models/{dir_name}"
            os.makedirs(dir_path, exist_ok=True)
        
        logger.info("Environment setup complete")
        return True
    except Exception as e:
        logger.error(f"Error during setup: {str(e)}")
        return False

def start_comfyui():
    """Start the ComfyUI server"""
    try:
        os.chdir("ComfyUI")
        logger.info("Starting ComfyUI server...")
        subprocess.run(
            ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--enable-cors-header"],
            check=True
        )
    except Exception as e:
        logger.error(f"Error running ComfyUI: {str(e)}")
        return False
    finally:
        os.chdir("..")

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
        
        # Save to local directory
        models_dir = os.path.join("ComfyUI", "models", model_type)
        os.makedirs(models_dir, exist_ok=True)
        model_path = os.path.join(models_dir, model_file.filename)
        model_file.save(model_path)
        
        return jsonify({"message": f"{model_type} model uploaded successfully"})
    except Exception as e:
        logger.error(f"Error uploading model: {str(e)}")
        return jsonify({"error": "Failed to upload model"}), 500

if __name__ == "__main__":
    if setup_environment():
        # Start ComfyUI in a separate thread
        comfyui_thread = threading.Thread(target=start_comfyui)
        comfyui_thread.daemon = True
        comfyui_thread.start()
        
        logger.info("\n=== Starting servers... ===")
        logger.info("ComfyUI will be available at: /proxy/8188")
        logger.info("Web UI will be available at: /proxy/7860")
        logger.info("===========================\n")
        
        # Start the Flask app
        app.run(host="0.0.0.0", port=7860) 
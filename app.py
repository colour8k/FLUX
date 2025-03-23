import os
from lightning_app import LightningWork, LightningApp, LightningFlow
from lightning_app.structures import List
import subprocess
import time
import webbrowser
from dotenv import load_dotenv
from model_manager import ModelManager, ModelType
from civitai_client import CivitaiClient, CivitaiModel
from huggingface_client import HuggingFaceClient, HuggingFaceModel
from web_ui import app as web_app
import uvicorn
import threading
from lightning_studio import StudioFlow, LightningConfig, StudioUI
from pathlib import Path
from lightning.app.storage import Drive

load_dotenv()

class ComfyUIWork(LightningWork):
    def __init__(self):
        # Request GPU and set parallel to True for concurrent execution
        super().__init__(cloud_compute={"gpu": "T4", "name": "gpu-small-t4"}, parallel=True)
        self.ready = False
        self._model_manager = ModelManager()
        self._civitai = CivitaiClient(os.getenv("CIVITAI_API_KEY"))
        self._huggingface = HuggingFaceClient(os.getenv("HUGGINGFACE_TOKEN"))
        self.web_port = 8000
        self.comfy_port = 8188
        self.browsers_opened = False
        self._config = LightningConfig.from_env()
        self.lightning_port = self._config.port
        # Create a drive for persistent model storage
        self.model_drive = Drive("model_storage")

    def run(self):
        print("🚀 Starting ComfyUI setup...")
        
        # Create necessary directories
        models_root = Path("models")
        models_root.mkdir(exist_ok=True)
        for model_type in ["checkpoints", "loras", "controlnet", "vae"]:
            (models_root / model_type).mkdir(exist_ok=True)
            
        # Restore models from persistent storage if they exist
        if self.model_drive.exists("models"):
            print("📥 Restoring models from storage...")
            self.model_drive.get("models", "models")
            
        # Clone ComfyUI if not present
        if not Path("ComfyUI").exists():
            print("📦 Cloning ComfyUI repository...")
            subprocess.run(
                ["git", "clone", "https://github.com/comfyanonymous/ComfyUI.git"],
                check=True
            )
            
        # Install ComfyUI dependencies
        print("📚 Installing ComfyUI requirements...")
        subprocess.run(
            ["pip", "install", "-r", "ComfyUI/requirements.txt"],
            check=True
        )
        
        # Start ComfyUI server
        print("✨ Starting ComfyUI server...")
        self.ready = True
        os.chdir("ComfyUI")
        subprocess.run([
            "python", "main.py",
            "--listen", "0.0.0.0",
            "--port", "8188",
            "--enable-cors-header"
        ])
        
        # Initialize web app
        web_app.comfy_ui = self
        
        # Start web server in a separate thread
        web_thread = threading.Thread(
            target=uvicorn.run,
            args=(web_app,),
            kwargs={
                "host": "0.0.0.0",
                "port": self.web_port,
                "log_level": "info"
            },
            daemon=True
        )
        web_thread.start()
        
        # Wait for servers to be ready
        time.sleep(5)  # Give servers time to start

        # Open browsers if not already opened
        if not self.browsers_opened:
            print("Opening interfaces in your browser...")
            webbrowser.open(f"http://127.0.0.1:{self.comfy_port}")  # ComfyUI
            webbrowser.open(f"http://127.0.0.1:{self.web_port}")    # Web UI
            self.browsers_opened = True
        
        while True:
            time.sleep(1)

    def add_model(self, name: str, model_type: ModelType, source: str, file_path: str, metadata: dict = None):
        """Add a model to the manager"""
        return self._model_manager.add_model(name, model_type, source, file_path, metadata)

    def list_models(self, model_type: ModelType = None):
        """List available models"""
        return self._model_manager.list_models(model_type)

    def search_civitai(self, query: str, model_type: str = None, nsfw: bool = False, limit: int = 10):
        """Search for models on Civitai"""
        return self._civitai.search_models(query, model_type, nsfw, limit)

    def download_civitai_model(self, model: CivitaiModel) -> str:
        """Download a model from Civitai and add it to the model manager"""
        return self._civitai.download_model(model)

    def search_huggingface(self, query: str, model_type: ModelType = None, flux_only: bool = False, limit: int = 20):
        """Search for models on Hugging Face"""
        return self._huggingface.search_models(query, model_type, flux_only, limit)

    def download_huggingface_model(self, model: HuggingFaceModel) -> str:
        """Download a model from Hugging Face and add it to the model manager"""
        return self._huggingface.download_model(model.id)

class WebUI(LightningWork):
    def __init__(self):
        super().__init__(parallel=True)
        self.ready = False
        self.model_drive = Drive("model_storage")
        
    def run(self):
        from flask import Flask, request, jsonify, render_template_string
        
        app = Flask(__name__)
        
        # Simple HTML template for the web interface
        INDEX_HTML = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>FLUX Studio</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body class="bg-gray-100">
            <div class="container mx-auto px-4 py-8">
                <h1 class="text-4xl font-bold mb-8">FLUX Studio</h1>
                
                <!-- Quick Links -->
                <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                    <h2 class="text-2xl font-semibold mb-4">Quick Links</h2>
                    <div class="space-y-4">
                        <a href="/proxy/8188" target="_blank" 
                           class="block bg-blue-500 text-white px-4 py-2 rounded text-center hover:bg-blue-600">
                            Open ComfyUI Interface
                        </a>
                    </div>
                </div>
                
                <!-- Model Upload -->
                <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                    <h2 class="text-2xl font-semibold mb-4">Upload Model</h2>
                    <form id="uploadForm" class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Model Type</label>
                            <select id="modelType" class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
                                <option value="checkpoints">Checkpoint</option>
                                <option value="loras">LoRA</option>
                                <option value="controlnet">ControlNet</option>
                                <option value="vae">VAE</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Model File</label>
                            <input type="file" id="modelFile" class="mt-1 block w-full">
                        </div>
                        <button type="submit" class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                            Upload Model
                        </button>
                    </form>
                </div>
                
                <!-- Model List -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-2xl font-semibold mb-4">Available Models</h2>
                    <div id="modelList" class="space-y-4"></div>
                </div>
            </div>
            
            <script>
                // Load models on page load
                loadModels();
                
                // Handle form submission
                document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const formData = new FormData();
                    const modelFile = document.getElementById('modelFile').files[0];
                    const modelType = document.getElementById('modelType').value;
                    
                    formData.append('model', modelFile);
                    formData.append('type', modelType);
                    
                    try {
                        const response = await fetch('/api/upload', {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.json();
                        alert(result.message || result.error);
                        if (!result.error) {
                            loadModels();
                            document.getElementById('modelFile').value = '';
                        }
                    } catch (error) {
                        alert('Error uploading model');
                    }
                });
                
                // Load and display models
                async function loadModels() {
                    try {
                        const response = await fetch('/api/models');
                        const data = await response.json();
                        const modelList = document.getElementById('modelList');
                        
                        if (data.models.length === 0) {
                            modelList.innerHTML = '<p class="text-gray-500">No models available</p>';
                            return;
                        }
                        
                        // Group models by type
                        const modelsByType = {};
                        data.models.forEach(model => {
                            if (!modelsByType[model.type]) {
                                modelsByType[model.type] = [];
                            }
                            modelsByType[model.type].push(model);
                        });
                        
                        // Display models
                        modelList.innerHTML = Object.entries(modelsByType).map(([type, models]) => `
                            <div class="mb-4">
                                <h3 class="text-lg font-medium mb-2">${type.charAt(0).toUpperCase() + type.slice(1)}</h3>
                                <div class="space-y-2">
                                    ${models.map(model => `
                                        <div class="flex items-center justify-between border p-2 rounded">
                                            <span>${model.name}</span>
                                            <span class="text-gray-500">${formatSize(model.size)}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `).join('');
                    } catch (error) {
                        console.error('Error loading models:', error);
                    }
                }
                
                // Format file size
                function formatSize(bytes) {
                    const units = ['B', 'KB', 'MB', 'GB'];
                    let size = bytes;
                    let unitIndex = 0;
                    while (size >= 1024 && unitIndex < units.length - 1) {
                        size /= 1024;
                        unitIndex++;
                    }
                    return `${size.toFixed(1)} ${units[unitIndex]}`;
                }
            </script>
        </body>
        </html>
        """
        
        @app.route('/')
        def index():
            return render_template_string(INDEX_HTML)
            
        @app.route('/api/models')
        def list_models():
            models = []
            models_root = Path("models")
            if models_root.exists():
                for model_type in ["checkpoints", "loras", "controlnet", "vae"]:
                    type_dir = models_root / model_type
                    if type_dir.exists():
                        for model in type_dir.iterdir():
                            if model.is_file():
                                models.append({
                                    "name": model.name,
                                    "type": model_type,
                                    "size": model.stat().st_size
                                })
            return jsonify({"models": models})
            
        @app.route('/api/upload', methods=['POST'])
        def upload_model():
            if 'model' not in request.files or 'type' not in request.form:
                return jsonify({"error": "Missing model file or type"}), 400
                
            model_file = request.files['model']
            model_type = request.form['type']
            
            if model_file.filename == '':
                return jsonify({"error": "No file selected"}), 400
                
            if model_type not in ["checkpoints", "loras", "controlnet", "vae"]:
                return jsonify({"error": "Invalid model type"}), 400
                
            # Save the model
            save_path = Path("models") / model_type / model_file.filename
            model_file.save(save_path)
            
            # Save to persistent storage
            self.model_drive.put(str(save_path), f"models/{model_type}/{model_file.filename}")
            
            return jsonify({"message": "Model uploaded successfully"})
            
        self.ready = True
        app.run(host="0.0.0.0", port=7860)

class ImageGenerationFlow(StudioFlow):
    def __init__(self):
        super().__init__()
        self.comfy_ui = ComfyUIWork()
        self.webui = WebUI()
        self.ui = StudioUI()  # Add UI component
        self.browsers_opened = False

    def run(self):
        # Run the parent StudioFlow
        super().run()
        
        # Run ComfyUI component
        self.comfy_ui.run()
        
        # Run Web UI component
        self.webui.run()
        
        # Run UI component
        self.ui.run()
        
        if self.comfy_ui.ready and not self.browsers_opened:
            print("\n=== Servers are ready! ===")
            print(f"Lightning UI is running at: http://127.0.0.1:{self.comfy_ui.lightning_port}/view")
            print(f"ComfyUI is running at: http://127.0.0.1:{self.comfy_ui.comfy_port}")
            print(f"Web UI is running at: http://127.0.0.1:{self.comfy_ui.web_port}")
            print("===========================\n")
            self.browsers_opened = True

# Create the Lightning App with basic configuration
app = LightningApp(ImageGenerationFlow())

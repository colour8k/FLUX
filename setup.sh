#!/bin/bash

# Create necessary directories
mkdir -p templates
mkdir -p static

# Clone ComfyUI if not exists
if [ ! -d "ComfyUI" ]; then
    git clone https://github.com/comfyanonymous/ComfyUI.git
    cd ComfyUI
    pip install -r requirements.txt
    cd ..
fi

# Install project dependencies
pip install -r requirements.txt

# Create models directory in ComfyUI if it doesn't exist
mkdir -p ComfyUI/models/checkpoints
mkdir -p ComfyUI/models/loras
mkdir -p ComfyUI/models/controlnet
mkdir -p ComfyUI/models/vae

# Set proper permissions for the directories
chmod -R 755 ComfyUI/models
chmod -R 755 templates
chmod -R 755 static

echo "Setup complete! You can now run the application with: python main.py"

#!/bin/bash

# Exit on error
set -e

echo "🧹 Cleaning up old environments..."
rm -rf venv .venv

echo "🐍 Creating new Python virtual environment..."
python3 -m venv .venv

echo "🔄 Activating virtual environment..."
source .venv/bin/activate

echo "⬆️ Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing Lightning and dependencies..."
pip install -r requirements.txt
pip install lightning-app

echo "🔍 Verifying Lightning installation..."
python -c "import lightning; print(f'Lightning version: {lightning.__version__}')"

echo "🎨 Setting up ComfyUI..."
if [ ! -d "ComfyUI" ]; then
    git clone https://github.com/comfyanonymous/ComfyUI.git
    cd ComfyUI
    pip install -r requirements.txt
    cd ..
fi

echo "📁 Creating model directories..."
mkdir -p ComfyUI/models/{checkpoints,loras,embeddings,vae}

echo "✅ Setup complete! You can now run: lightning run app app.py" 
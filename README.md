# FLUX - ComfyUI Lightning Studio

A Lightning AI app that provides a managed environment for running ComfyUI with GPU acceleration and persistent storage.

## Features

- 🚀 Runs ComfyUI in a managed Lightning environment
- 💾 Persistent model storage across sessions
- 🎮 Easy-to-use web interface for model management
- 🔄 Automatic GPU provisioning
- 📦 Simple setup and deployment

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/colour8k/FLUX.git
cd FLUX
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
lightning run app app.py
```

4. Access the interfaces:
- ComfyUI: `/proxy/8188`
- Management UI: `/proxy/7860`

## Structure

- `app.py`: Main Lightning application
- `requirements.txt`: Python dependencies
- `models/`: Directory for model storage (created automatically)
  - `checkpoints/`: Stable Diffusion models
  - `loras/`: LoRA models
  - `controlnet/`: ControlNet models
  - `vae/`: VAE models

## Requirements

- Python 3.8+
- Lightning AI account
- GPU access (provided by Lightning)

## License

MIT License
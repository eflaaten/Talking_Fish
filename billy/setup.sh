# To run type:
# chmod +x setup.sh
# ./setup.sh

#!/bin/bash

echo "🐟 Setting up your Talking Fish..."

# === Update System ===
sudo apt update && sudo apt upgrade -y

# === Install Required System Packages ===
echo "📦 Installing system dependencies..."
sudo apt install -y \
    python3-pyaudio \
    portaudio19-dev \
    python3-venv \
    python3-lgpio \
    libatlas-base-dev

# === Create Virtual Environment ===
echo "🍓 Creating virtual environment..."
python3 -m venv env
source env/bin/activate

# === Install Python Dependencies ===
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# === Setup Complete ===
echo "✅ Setup complete!"
echo "🧪 Now create a .env file with your API keys, then run:"
echo "   python main.py"

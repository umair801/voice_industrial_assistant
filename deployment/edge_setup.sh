#!/bin/bash
# Edge Device Deployment Script
# Automated setup for Raspberry Pi / Jetson Nano

set -e  # Exit on error

echo "================================"
echo "Voice Industrial Assistant"
echo "Edge Device Deployment"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}Please do not run as root${NC}"
    exit 1
fi

# Detect platform
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    echo "Detected: $MODEL"
else
    echo "Platform: Generic Linux"
fi

# Update system
echo -e "${YELLOW}Updating system...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio \
    alsa-utils \
    espeak \
    git

# Create project directory
PROJECT_DIR="$HOME/voice_industrial_assistant"
echo -e "${YELLOW}Creating project directory: $PROJECT_DIR${NC}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo -e "${RED}requirements.txt not found!${NC}"
    exit 1
fi

# Download Whisper model
echo -e "${YELLOW}Downloading Whisper model (this may take a few minutes)...${NC}"
python -c "import whisper; whisper.load_model('medium.en')"

# Create directory structure
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p logs logs/metrics data/samples config

# Copy example config if config doesn't exist
if [ ! -f config/config.yaml ]; then
    if [ -f config/config.example.yaml ]; then
        cp config/config.example.yaml config/config.yaml
        echo -e "${GREEN}Created config/config.yaml from example${NC}"
        echo -e "${YELLOW}Please edit config/config.yaml with your settings${NC}"
    fi
fi

# Create environment file
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# API Keys (replace with your actual keys)
ERP_API_KEY=your-erp-api-key-here
WMS_API_KEY=your-wms-api-key-here
LOG_LEVEL=INFO
EOF
    echo -e "${GREEN}Created .env file${NC}"
    echo -e "${YELLOW}Please edit .env with your API keys${NC}"
fi

# Create systemd service
echo -e "${YELLOW}Creating systemd service...${NC}"
sudo tee /etc/systemd/system/voice-assistant.service > /dev/null << EOF
[Unit]
Description=Voice Industrial Assistant
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Test audio devices
echo -e "${YELLOW}Testing audio devices...${NC}"
python -c "import sounddevice as sd; devices = sd.query_devices(); print('\nAvailable Audio Devices:'); [print(f'{i}: {d[\"name\"]}') for i, d in enumerate(devices)]"

# Final instructions
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano config/config.yaml"
echo "2. Set API keys: nano .env"
echo "3. Test the application: source venv/bin/activate && python src/main.py"
echo "4. Enable auto-start: sudo systemctl enable voice-assistant"
echo "5. Start service: sudo systemctl start voice-assistant"
echo ""
echo "Useful commands:"
echo "  - View logs: sudo journalctl -u voice-assistant -f"
echo "  - Check status: sudo systemctl status voice-assistant"
echo "  - Restart: sudo systemctl restart voice-assistant"
echo ""
echo -e "${YELLOW}Remember to configure your ERP/WMS API credentials!${NC}"

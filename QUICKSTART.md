# Quick Start Guide

Get the Voice Industrial Assistant running in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- Microphone and speaker
- Internet connection
- API credentials for your ERP/WMS systems

## Installation

### 1. Extract the files

```bash
unzip voice_industrial_assistant.zip
cd voice_industrial_assistant
```

### 2. Install dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 3. Configure

```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit with your settings
nano config/config.yaml
```

Update these key settings:
- `integrations.erp.base_url` - Your ERP API URL
- `integrations.erp.api_key` - Your ERP API key
- `integrations.wms.base_url` - Your WMS API URL
- `integrations.wms.api_key` - Your WMS API key

### 4. Run

```bash
python src/main.py
```

## First Commands

Try these voice commands:

1. **"Check stock for SKU AB-12345"**
   - Queries inventory for a specific SKU

2. **"Add 50 units of XY-9012 to B7-2"**
   - Updates inventory (requires confirmation)

3. **"Where is pallet 7823?"**
   - Finds location of a pallet

4. **"What's my next task?"**
   - Gets next work order

## Troubleshooting

### Microphone not detected

```bash
# List available devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Set specific device in config.yaml
audio:
  device_id: 0  # Use the correct number
```

### Low recognition accuracy

1. Move microphone closer (6-12 inches)
2. Reduce background noise
3. Use a better quality microphone

### API connection errors

1. Check your internet connection
2. Verify API credentials in config.yaml
3. Test API endpoints manually with curl

## Next Steps

- Read the full README.md for detailed features
- Check docs/DEPLOYMENT.md for production deployment
- Review config/config.example.yaml for all options

## Support

- Documentation: docs/
- Issues: GitHub Issues
- Email: support@yourcompany.com

Enjoy your voice-activated industrial assistant!

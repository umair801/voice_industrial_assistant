# Voice-Activated Industrial Assistant

A hands-free voice interface for warehouse, manufacturing, and field service workers to interact with inventory systems, work orders, and equipment databases without touchscreen interaction.

## Features

- **Noise-robust speech recognition** optimized for industrial environments
- **Natural language understanding** for domain-specific commands
- **System integration** with ERP/WMS via REST APIs
- **Confirmation flows** for critical operations
- **Privacy-first design** with local processing options
- **Edge deployment** support for offline capability

## Target Use Cases

- Inventory queries and updates
- Work order management
- Equipment troubleshooting guidance
- Location tracking
- Task completion logging

## System Requirements

### Hardware
- Raspberry Pi 5 (4GB RAM minimum) or NVIDIA Jetson Nano
- USB microphone (recommended: Shure MV7 or Blue Yeti)
- Bone conduction headset (optional, for noisy environments)

### Software
- Python 3.9+
- FFmpeg for audio processing
- Docker (for containerized deployment)

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd voice_industrial_assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download Whisper model
python -c "import whisper; whisper.load_model('medium.en')"
```

### 2. Configuration

```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit configuration with your API credentials
nano config/config.yaml
```

### 3. Run the Assistant

```bash
# Start the voice assistant
python src/main.py

# Or run with Docker
docker-compose up
```

## Project Structure

```
voice_industrial_assistant/
├── src/
│   ├── core/
│   │   ├── stt_engine.py          # Speech-to-text with noise reduction
│   │   ├── nlu_engine.py          # Natural language understanding
│   │   ├── dialogue_manager.py    # Conversation state management
│   │   └── tts_engine.py          # Text-to-speech responses
│   ├── integrations/
│   │   ├── erp_connector.py       # ERP system integration
│   │   ├── wms_connector.py       # Warehouse management integration
│   │   └── base_connector.py      # Base integration class
│   ├── utils/
│   │   ├── audio_processor.py     # Audio preprocessing
│   │   ├── logger.py              # Logging utilities
│   │   └── metrics.py             # Performance metrics
│   └── main.py                    # Application entry point
├── tests/                         # Unit and integration tests
├── config/                        # Configuration files
├── deployment/                    # Deployment scripts
├── docs/                          # Documentation
├── data/samples/                  # Sample audio files
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## Configuration

Edit `config/config.yaml`:

```yaml
stt:
  model: "medium.en"
  language: "en"
  noise_reduction: true
  
integrations:
  erp:
    base_url: "https://your-erp-system.com/api"
    api_key: "your-api-key"
  wms:
    base_url: "https://your-wms-system.com/api"
    api_key: "your-api-key"

dialogue:
  confirmation_required:
    - update_inventory
    - delete
    - mark_complete
  timeout_seconds: 30
```

## Usage Examples

### Inventory Query
**Voice Command:** "Check stock for SKU AB-12345"  
**Response:** "We have 143 units of AB-12345 in location A5-3"

### Inventory Update (with confirmation)
**Voice Command:** "Add 50 units of XY-9012 to B7-2"  
**Response:** "Confirm: Add 50 units of XY-9012. Say yes to proceed."  
**User:** "Yes"  
**Response:** "Updated: 50 units added to B7-2"

### Location Query
**Voice Command:** "Where is pallet 7823?"  
**Response:** "Pallet 7823 is in location C3-5"

### Work Order
**Voice Command:** "What's my next task?"  
**Response:** "Your next task is: Pick 25 units of SKU MN-4567 from A12-3"

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Test in noisy environment simulation
python tests/test_noise_robustness.py
```

## Performance Targets

- **Recognition Accuracy:** >90% in 85dB environment
- **Response Time:** <2 seconds end-to-end
- **Uptime:** 99.5%
- **User Adoption:** 80% within 3 months

## Deployment Options

### Option 1: Edge Device (Recommended)
- Full local processing for privacy
- Works offline
- Lower latency
- See `deployment/edge_setup.sh`

### Option 2: Cloud-Hybrid
- Better accuracy with cloud STT
- Centralized management
- Requires internet
- See `deployment/cloud_setup.sh`

## Monitoring

```bash
# View real-time metrics
python src/utils/metrics.py --dashboard

# Generate weekly report
python src/utils/metrics.py --report weekly
```

## Security Considerations

- **No voice data storage** unless explicitly enabled for training
- **API credentials** stored in environment variables
- **TLS encryption** for all API communications
- **Role-based access** for different worker levels

## Troubleshooting

### Low Recognition Accuracy
1. Check microphone positioning (6-12 inches from mouth)
2. Adjust noise reduction settings in config
3. Retrain with custom vocabulary

### High Latency
1. Use smaller Whisper model (`base.en` or `small.en`)
2. Enable GPU acceleration
3. Switch to edge deployment

### Integration Errors
1. Verify API credentials in config
2. Check network connectivity
3. Review logs in `logs/app.log`

## Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for guidelines.

## License

MIT License - see `LICENSE` file

## Support

- Documentation: `docs/`
- Issues: GitHub Issues
- Email: support@yourcompany.com

## Roadmap

- [ ] Multi-language support
- [ ] Custom wake word detection
- [ ] Mobile app interface
- [ ] Advanced analytics dashboard
- [ ] Voice biometric authentication

## Authors

Muhammad Umair - Machine Learning Engineer

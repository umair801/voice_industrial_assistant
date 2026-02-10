# Deployment Guide

This guide covers deployment options for the Voice Industrial Assistant.

## Deployment Options

### 1. Edge Device Deployment (Recommended for Privacy)

Deploy directly on edge devices (Raspberry Pi, NVIDIA Jetson) for maximum privacy and offline capability.

#### Prerequisites
- Raspberry Pi 5 (4GB RAM) or NVIDIA Jetson Nano
- Microphone (USB or built-in)
- Speaker/headset
- Internet connection (for ERP/WMS API access)

#### Setup Steps

```bash
# 1. Update system
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install dependencies
sudo apt-get install -y python3-pip ffmpeg portaudio19-dev espeak

# 3. Clone repository
git clone <repository-url>
cd voice_industrial_assistant

# 4. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 5. Install Python packages
pip install -r requirements.txt

# 6. Download Whisper model
python -c "import whisper; whisper.load_model('medium.en')"

# 7. Configure
cp config/config.example.yaml config/config.yaml
nano config/config.yaml  # Edit with your settings

# 8. Set environment variables
export ERP_API_KEY="your-erp-key"
export WMS_API_KEY="your-wms-key"

# 9. Run
python src/main.py
```

#### Auto-start on Boot

Create systemd service:

```bash
sudo nano /etc/systemd/system/voice-assistant.service
```

```ini
[Unit]
Description=Voice Industrial Assistant
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/voice_industrial_assistant
Environment="ERP_API_KEY=your-key"
Environment="WMS_API_KEY=your-key"
ExecStart=/home/pi/voice_industrial_assistant/venv/bin/python src/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable service:

```bash
sudo systemctl enable voice-assistant
sudo systemctl start voice-assistant
```

### 2. Docker Deployment

Deploy using Docker for easy management and scalability.

#### Prerequisites
- Docker 20.10+
- Docker Compose 1.29+

#### Setup Steps

```bash
# 1. Clone repository
git clone <repository-url>
cd voice_industrial_assistant

# 2. Configure environment
cp .env.example .env
nano .env  # Add API keys

# 3. Build and run
docker-compose up -d

# 4. View logs
docker-compose logs -f voice-assistant
```

#### Environment Variables (.env)

```bash
ERP_API_KEY=your-erp-api-key
WMS_API_KEY=your-wms-api-key
LOG_LEVEL=INFO
```

### 3. Cloud Deployment (AWS)

Deploy on AWS EC2 for centralized management.

#### Prerequisites
- AWS account
- EC2 instance (t3.medium or larger)
- Security group with required ports open

#### Setup Steps

```bash
# 1. Launch EC2 instance (Ubuntu 22.04)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@ec2-instance-ip

# 3. Follow edge deployment steps above

# 4. Configure nginx reverse proxy (optional)
sudo apt-get install nginx
# Configure nginx for API access
```

#### AWS Resources

**Recommended Instance Type:** t3.medium
- 2 vCPUs
- 4 GB RAM
- Cost: ~$30/month

**Storage:** 30 GB EBS

## Network Configuration

### Firewall Rules

For edge deployment, ensure the following ports are accessible:

- **Outbound:**
  - 443 (HTTPS) - For ERP/WMS API calls
  - 80 (HTTP) - For updates (optional)

### API Endpoints

Configure your ERP/WMS API endpoints in `config/config.yaml`:

```yaml
integrations:
  erp:
    base_url: "https://api.your-erp.com"
  wms:
    base_url: "https://api.your-wms.com"
```

## Performance Optimization

### For Raspberry Pi

1. **Use smaller Whisper model:**
```yaml
stt:
  model: "base.en"  # Faster than medium.en
```

2. **Disable noise reduction for speed:**
```yaml
stt:
  noise_reduction: false
```

3. **Overclock (optional):**
```bash
# Edit /boot/config.txt
over_voltage=6
arm_freq=2000
```

### For NVIDIA Jetson

1. **Enable GPU acceleration:**
```yaml
stt:
  device: "cuda"
```

2. **Maximize performance mode:**
```bash
sudo nvpmodel -m 0
sudo jetson_clocks
```

## Monitoring

### System Metrics

```bash
# CPU/Memory usage
htop

# Disk space
df -h

# Application logs
tail -f logs/voice_assistant.log
```

### Application Metrics

View metrics dashboard:

```bash
python src/utils/metrics.py --dashboard
```

Generate weekly report:

```bash
python src/utils/metrics.py --report weekly
```

## Troubleshooting

### Issue: Low recognition accuracy

**Solution:**
1. Check microphone placement (6-12 inches from mouth)
2. Adjust noise reduction settings
3. Use larger Whisper model

### Issue: High latency

**Solution:**
1. Use smaller Whisper model
2. Enable GPU acceleration
3. Check network latency to ERP/WMS

### Issue: Audio device not found

**Solution:**
```bash
# List audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Set specific device in config
audio:
  device_id: 0  # Use correct device number
```

### Issue: Integration errors

**Solution:**
1. Verify API credentials
2. Check network connectivity
3. Review API endpoint URLs
4. Check firewall rules

## Backup and Recovery

### Backup Configuration

```bash
# Backup config and logs
tar -czf backup_$(date +%Y%m%d).tar.gz config/ logs/

# Copy to remote location
scp backup_*.tar.gz user@backup-server:/backups/
```

### Restore

```bash
# Extract backup
tar -xzf backup_20241228.tar.gz
```

## Security Best Practices

1. **Use environment variables for API keys**
2. **Enable TLS for API communications**
3. **Restrict network access with firewall**
4. **Regular security updates**
5. **Audit logs for suspicious activity**

## Support

For issues or questions:
- GitHub Issues: <repository-url>/issues
- Documentation: docs/
- Email: support@yourcompany.com

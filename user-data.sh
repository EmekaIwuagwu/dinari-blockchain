#!/bin/bash
apt update -y
apt install -y python3 python3-pip python3-dev build-essential git curl

# Create DinariBlockchain user
useradd -m -s /bin/bash dinari

# Clone or create blockchain directory
sudo -u dinari mkdir -p /home/dinari/blockchain
cd /home/dinari/blockchain

# Create simple Python blockchain app
sudo -u dinari cat > app.py << 'PYEOF'
from flask import Flask, jsonify
import os
import time
import json
from datetime import datetime

app = Flask(__name__)

# Simple blockchain structure
blockchain_data = {
    "blocks": [],
    "transactions": [],
    "status": "running"
}

@app.route('/')
def home():
    return jsonify({
        "message": "DinariBlockchain is running!",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "blocks": len(blockchain_data["blocks"]),
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "uptime": time.time()})

@app.route('/api/blockchain/info')
def blockchain_info():
    return jsonify(blockchain_data)

if __name__ == '__main__':
    # Create genesis block
    genesis = {
        "index": 0,
        "timestamp": time.time(),
        "data": "Genesis Block - DinariBlockchain",
        "hash": "0000000000000000000000000000000000000000000000000000000000000000"
    }
    blockchain_data["blocks"].append(genesis)
    
    print("🚀 DinariBlockchain starting...")
    print("🌐 API: http://0.0.0.0:5000")
    print("🔍 Health: http://0.0.0.0:5000/health")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

# Install Flask
pip3 install flask

# Create systemd service
cat > /etc/systemd/system/dinari-blockchain.service << 'SVCEOF'
[Unit]
Description=DinariBlockchain
After=network.target

[Service]
Type=simple
User=dinari
WorkingDirectory=/home/dinari/blockchain
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
SVCEOF

# Enable and start service
systemctl daemon-reload
systemctl enable dinari-blockchain
systemctl start dinari-blockchain

# Open firewall
ufw allow 5000
ufw allow 8333
ufw allow 8545

echo "✅ DinariBlockchain installed and running!"

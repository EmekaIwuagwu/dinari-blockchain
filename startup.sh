#!/bin/bash
apt update && apt install -y python3 python3-pip
pip3 install flask

# Create blockchain app
cat > /home/ubuntu/blockchain.py << 'PY'
from flask import Flask, jsonify
import time

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "DinariBlockchain Running!", "status": "active"})

@app.route('/health')  
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
PY

# Start blockchain
nohup python3 /home/ubuntu/blockchain.py > /home/ubuntu/blockchain.log 2>&1 &

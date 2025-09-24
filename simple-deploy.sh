#!/bin/bash
# Simple Step-by-Step Oracle Cloud Deployment

set -e

COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaa7gystzyxk5pxolz4bk4e2datu4flt57evnfymzzt3onmttubcopq"

echo "🚀 Simple DinariBlockchain Deployment"

# Step 1: Test OCI connection
echo "Step 1: Testing OCI connection..."
if ! oci iam region list; then
    echo "❌ OCI CLI connection failed. Run './setup-oci-manual.sh' first"
    exit 1
fi
echo "✅ OCI connection working"

# Step 2: Get availability domain
echo "Step 2: Getting availability domain..."
AVAILABILITY_DOMAIN=$(oci iam availability-domain list --compartment-id ${COMPARTMENT_ID} --query 'data[0].name' --raw-output)
echo "✅ Availability Domain: ${AVAILABILITY_DOMAIN}"

# Step 3: Find Ubuntu image
echo "Step 3: Finding Ubuntu image..."
IMAGE_ID=$(oci compute image list --compartment-id ${COMPARTMENT_ID} --operating-system "Canonical Ubuntu" --shape "VM.Standard.E2.1.Micro" --limit 1 --query 'data[0].id' --raw-output)
echo "✅ Image ID: ${IMAGE_ID}"

# Step 4: Find subnet
echo "Step 4: Finding subnet..."
SUBNET_ID=$(oci network subnet list --compartment-id ${COMPARTMENT_ID} --limit 1 --query 'data[0].id' --raw-output)
echo "✅ Subnet ID: ${SUBNET_ID}"

# Step 5: Create simple startup script
echo "Step 5: Creating startup script..."
cat > user-data.sh << 'EOF'
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
EOF

chmod +x user-data.sh

# Step 6: Create instance
echo "Step 6: Creating Oracle Cloud instance..."
echo "This may take 2-3 minutes..."

INSTANCE_ID=$(oci compute instance launch \
    --availability-domain "${AVAILABILITY_DOMAIN}" \
    --compartment-id ${COMPARTMENT_ID} \
    --shape "VM.Standard.E2.1.Micro" \
    --image-id ${IMAGE_ID} \
    --subnet-id ${SUBNET_ID} \
    --display-name "dinari-blockchain-simple" \
    --user-data-file user-data.sh \
    --wait-for-state RUNNING \
    --query 'data.id' --raw-output)

echo "✅ Instance created: ${INSTANCE_ID}"

# Step 7: Get IP address
echo "Step 7: Getting public IP..."
sleep 30  # Wait for network interface
PUBLIC_IP=$(oci compute instance list-vnics --instance-id ${INSTANCE_ID} --query 'data[0]."public-ip"' --raw-output)
echo "✅ Public IP: ${PUBLIC_IP}"

# Step 8: Save deployment info
cat > deployment-success.txt << EOF
🎉 DinariBlockchain Deployment Successful!

Instance ID: ${INSTANCE_ID}
Public IP: ${PUBLIC_IP}
Region: eu-marseille-1

🌐 Access URLs:
- Main API: http://${PUBLIC_IP}:5000
- Health Check: http://${PUBLIC_IP}:5000/health  
- Blockchain Info: http://${PUBLIC_IP}:5000/api/blockchain/info

🔧 Management:
- SSH: ssh -i ~/.ssh/id_rsa opc@${PUBLIC_IP}
- Check Status: ssh opc@${PUBLIC_IP} 'sudo systemctl status dinari-blockchain'
- View Logs: ssh opc@${PUBLIC_IP} 'sudo journalctl -u dinari-blockchain -f'

⏳ Wait 2-3 minutes for the service to start, then test:
curl http://${PUBLIC_IP}:5000/health
EOF

echo "✅ Deployment complete! Check deployment-success.txt"
echo "🔗 Test your blockchain: http://${PUBLIC_IP}:5000"
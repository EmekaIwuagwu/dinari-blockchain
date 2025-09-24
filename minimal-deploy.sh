#!/bin/bash
# Ultra Simple DinariBlockchain Deployment

COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaa7gystzyxk5pxolz4bk4e2datu4flt57evnfymzzt3onmttubcopq"

echo "🚀 Ultra Simple DinariBlockchain Deployment"

# Get required info
AD=$(oci iam availability-domain list --compartment-id ${COMPARTMENT_ID} --query 'data[0].name' --raw-output)
IMAGE_ID=$(oci compute image list --compartment-id ${COMPARTMENT_ID} --operating-system "Canonical Ubuntu" --limit 1 --query 'data[0].id' --raw-output)
SUBNET_ID=$(oci network subnet list --compartment-id ${COMPARTMENT_ID} --limit 1 --query 'data[0].id' --raw-output)

# Create startup script
cat > startup.sh << 'EOF'
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
EOF

# Deploy instance
echo "Creating instance..."
INSTANCE_ID=$(oci compute instance launch \
    --availability-domain "${AD}" \
    --compartment-id ${COMPARTMENT_ID} \
    --shape "VM.Standard.E2.1.Micro" \
    --image-id ${IMAGE_ID} \
    --subnet-id ${SUBNET_ID} \
    --display-name "dinari-minimal" \
    --user-data-file startup.sh \
    --wait-for-state RUNNING \
    --query 'data.id' --raw-output)

sleep 30
PUBLIC_IP=$(oci compute instance list-vnics --instance-id ${INSTANCE_ID} --query 'data[0]."public-ip"' --raw-output)

echo "✅ Deployed!"
echo "Instance: ${INSTANCE_ID}"
echo "IP: ${PUBLIC_IP}"
echo "Test: curl http://${PUBLIC_IP}:5000/health"

# Save info
echo "IP: ${PUBLIC_IP}" > deployment.txt
echo "Instance: ${INSTANCE_ID}" >> deployment.txt
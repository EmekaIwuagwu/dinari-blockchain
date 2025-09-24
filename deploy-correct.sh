#!/bin/bash
# Deploy DinariBlockchain with CORRECT GitHub repository

COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaa7gystzyxk5pxolz4bk4e2datu4flt57evnfymzzt3onmttubcopq"

echo "🚀 Deploying DinariBlockchain with correct GitHub repo"

# Get deployment info
AD=$(oci iam availability-domain list --compartment-id ${COMPARTMENT_ID} --query 'data[0].name' --raw-output)
IMAGE_ID=$(oci compute image list --compartment-id ${COMPARTMENT_ID} --operating-system "Canonical Ubuntu" --limit 1 --query 'data[0].id' --raw-output)
SUBNET_ID=$(oci network subnet list --compartment-id ${COMPARTMENT_ID} --limit 1 --query 'data[0].id' --raw-output)

# Create cloud-init with CORRECT GitHub URL
cat > cloud-init-correct.yml << 'EOF'
#cloud-config
package_update: true

packages:
  - docker.io
  - git
  - python3
  - python3-pip
  - build-essential
  - libleveldb-dev

runcmd:
  - systemctl start docker
  - systemctl enable docker
  - usermod -aG docker ubuntu
  
  # Clone from CORRECT GitHub repository
  - git clone https://github.com/EmekaIwuagwu/dinari-blockchain.git /opt/dinari-blockchain
  - cd /opt/dinari-blockchain
  
  # Install Python dependencies
  - pip3 install -r requirements.txt
  
  # Create blockchain data directory
  - mkdir -p /opt/dinari-blockchain/blockchain_data
  
  # Copy .env file (create basic one if missing)
  - |
    if [ ! -f /opt/dinari-blockchain/.env ]; then
      cat > /opt/dinari-blockchain/.env << 'ENVEOF'
    # Basic DinariBlockchain Configuration
    BLOCKCHAIN_NAME=DinariBlockchain
    BLOCKCHAIN_VERSION=1.0.0
    BLOCKCHAIN_NETWORK=mainnet
    NODE_ENV=production
    FLASK_ENV=production
    
    NODE_TYPE=validator
    NODE_ID=dinari-validator-1
    P2P_PORT=8333
    API_PORT=5000
    HOST=0.0.0.0
    
    LEVELDB_CACHE_SIZE_MB=32
    MAX_CONNECTIONS=5
    MINING_ENABLED=true
    AUTO_MINING=true
    BLOCK_TIME=10
    
    DATABASE_TYPE=leveldb
    LEVELDB_PATH=/opt/dinari-blockchain/blockchain_data
    
    LOG_LEVEL=INFO
    DEBUG=false
    ENVEOF
    fi
  
  # Start blockchain with nohup
  - cd /opt/dinari-blockchain
  - nohup python3 app.py > /var/log/dinari-blockchain.log 2>&1 &
  
  # Log completion
  - echo "DinariBlockchain started with correct repo" >> /var/log/cloud-init-output.log

write_files:
  - path: /etc/systemd/system/dinari-blockchain.service
    content: |
      [Unit]
      Description=Dinari Blockchain Service
      After=network.target
      
      [Service]
      Type=simple
      User=ubuntu
      WorkingDirectory=/opt/dinari-blockchain
      ExecStart=/usr/bin/python3 app.py
      Restart=always
      Environment=LEVELDB_PATH=/opt/dinari-blockchain/blockchain_data
      Environment=FLASK_ENV=production
      Environment=BLOCKCHAIN_NETWORK=mainnet
      Environment=P2P_PORT=8333
      Environment=API_PORT=5000
      Environment=ENABLE_MINING=true
      
      [Install]
      WantedBy=multi-user.target
    permissions: '0644'

final_message: "DinariBlockchain deployment completed with correct GitHub repo!"
EOF

# Deploy instance
echo "Creating Oracle Cloud instance..."
INSTANCE_ID=$(oci compute instance launch \
    --availability-domain "${AD}" \
    --compartment-id ${COMPARTMENT_ID} \
    --shape "VM.Standard.E2.1.Micro" \
    --image-id ${IMAGE_ID} \
    --subnet-id ${SUBNET_ID} \
    --display-name "dinari-blockchain-correct" \
    --user-data-file cloud-init-correct.yml \
    --wait-for-state RUNNING \
    --query 'data.id' --raw-output)

echo "✅ Instance created: ${INSTANCE_ID}"

# Get public IP
sleep 30
PUBLIC_IP=$(oci compute instance list-vnics --instance-id ${INSTANCE_ID} --query 'data[0]."public-ip"' --raw-output)

echo "✅ Public IP: ${PUBLIC_IP}"

# Save deployment info
cat > deployment-correct.txt << EOF
🎉 DinariBlockchain Deployment (Correct Repo)

Instance ID: ${INSTANCE_ID}
Public IP: ${PUBLIC_IP}
Repository: https://github.com/EmekaIwuagwu/dinari-blockchain.git

🌐 Access URLs:
- Main API: http://${PUBLIC_IP}:5000
- Health: http://${PUBLIC_IP}:5000/health
- RPC: http://${PUBLIC_IP}:8545/rpc

🔧 SSH Access:
ssh -i ~/.ssh/id_rsa ubuntu@${PUBLIC_IP}

⏳ Wait 3-4 minutes for blockchain to start, then test:
curl http://${PUBLIC_IP}:5000/health
EOF

echo "🚀 Deployment complete! Check deployment-correct.txt"
echo "🔗 Your DinariBlockchain will be at: http://${PUBLIC_IP}:5000"
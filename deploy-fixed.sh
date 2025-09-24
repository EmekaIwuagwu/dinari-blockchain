#!/bin/bash
# Deploy DinariBlockchain with Always Free compatible image

COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaa7gystzyxk5pxolz4bk4e2datu4flt57evnfymzzt3onmttubcopq"

echo "🚀 Deploying DinariBlockchain (Fixed Image Compatibility)"

# Get deployment info
echo "Getting availability domain..."
AD=$(oci iam availability-domain list --compartment-id ${COMPARTMENT_ID} --query 'data[0].name' --raw-output)
echo "✅ Availability Domain: ${AD}"

# Find Always Free compatible Ubuntu image
echo "Finding Always Free compatible Ubuntu image..."
IMAGE_ID=$(oci compute image list \
    --compartment-id ${COMPARTMENT_ID} \
    --operating-system "Canonical Ubuntu" \
    --operating-system-version "22.04" \
    --shape "VM.Standard.E2.1.Micro" \
    --limit 1 \
    --query 'data[0].id' --raw-output)

if [ "$IMAGE_ID" = "null" ] || [ -z "$IMAGE_ID" ]; then
    echo "No specific Ubuntu 22.04 found, trying general Ubuntu..."
    IMAGE_ID=$(oci compute image list \
        --compartment-id ${COMPARTMENT_ID} \
        --operating-system "Canonical Ubuntu" \
        --limit 10 \
        --query 'data[?contains(to_string(@), `aarch64`) == `false`] | [0].id' --raw-output)
fi

if [ "$IMAGE_ID" = "null" ] || [ -z "$IMAGE_ID" ]; then
    echo "❌ No compatible Ubuntu image found. Using known working image..."
    # Use the image from your previous working instance
    IMAGE_ID="ocid1.image.oc1.eu-marseille-1.aaaaaaaae2dw33d5o44ro4ixmdadk74a25g2f3fstnpsla5kqhlrpq56mwbq"
fi

echo "✅ Using Image: ${IMAGE_ID}"

# Get subnet
echo "Getting subnet..."
SUBNET_ID=$(oci network subnet list --compartment-id ${COMPARTMENT_ID} --limit 1 --query 'data[0].id' --raw-output)
echo "✅ Subnet: ${SUBNET_ID}"

# Create cloud-init with correct GitHub URL
echo "Creating deployment configuration..."
cat > cloud-init-fixed.yml << 'EOF'
#cloud-config
package_update: true
package_upgrade: true

packages:
  - git
  - python3
  - python3-pip
  - python3-dev
  - build-essential
  - curl
  - htop

runcmd:
  # Create ubuntu user if it doesn't exist
  - id -u ubuntu &>/dev/null || useradd -m -s /bin/bash ubuntu
  
  # Clone DinariBlockchain from CORRECT repository
  - echo "Cloning DinariBlockchain from correct repo..."
  - git clone https://github.com/EmekaIwuagwu/dinari-blockchain.git /opt/dinari-blockchain
  - cd /opt/dinari-blockchain
  
  # Set ownership
  - chown -R ubuntu:ubuntu /opt/dinari-blockchain
  
  # Install Python dependencies
  - echo "Installing Python dependencies..."
  - pip3 install flask requests leveldb werkzeug cryptography ecdsa
  - pip3 install -r requirements.txt || echo "No requirements.txt found, using manual install"
  
  # Create necessary directories
  - mkdir -p /opt/dinari-blockchain/blockchain_data
  - mkdir -p /opt/dinari-blockchain/logs
  - mkdir -p /opt/dinari-blockchain/wallets
  - chown -R ubuntu:ubuntu /opt/dinari-blockchain
  
  # Create production .env file
  - |
    cat > /opt/dinari-blockchain/.env << 'ENVEOF'
    # DinariBlockchain Production Configuration
    BLOCKCHAIN_NAME=DinariBlockchain
    BLOCKCHAIN_VERSION=1.0.0
    BLOCKCHAIN_NETWORK=mainnet
    NODE_ENV=production
    FLASK_ENV=production
    
    # Node Configuration
    NODE_TYPE=validator
    NODE_ID=dinari-validator-1
    P2P_PORT=8333
    API_PORT=5000
    HOST=0.0.0.0
    
    # Memory Optimization for 1GB RAM
    LEVELDB_CACHE_SIZE_MB=32
    MAX_CONNECTIONS=5
    MAX_MEMORY_POOL_SIZE=100
    
    # Mining Configuration
    MINING_ENABLED=true
    ENABLE_MINING=true
    AUTO_MINING=true
    BLOCK_TIME=10
    
    # Database
    DATABASE_TYPE=leveldb
    LEVELDB_PATH=/opt/dinari-blockchain/blockchain_data
    
    # Security
    SECRET_KEY=dinari_blockchain_secret_key_2025
    
    # Logging
    LOG_LEVEL=INFO
    DEBUG=false
    ENVEOF
  
  - chown ubuntu:ubuntu /opt/dinari-blockchain/.env
  
  # Test Python import
  - cd /opt/dinari-blockchain && sudo -u ubuntu python3 -c "import flask; print('Flask imported successfully')"
  
  # Start blockchain service
  - echo "Starting DinariBlockchain service..."
  - systemctl daemon-reload
  - systemctl enable dinari-blockchain
  - systemctl start dinari-blockchain
  
  # Open firewall ports
  - ufw allow 22
  - ufw allow 5000
  - ufw allow 8333  
  - ufw allow 8545
  - echo "y" | ufw enable
  
  # Log completion
  - echo "DinariBlockchain deployment completed at $(date)" >> /var/log/dinari-deployment.log
  - echo "Service status:" >> /var/log/dinari-deployment.log
  - systemctl status dinari-blockchain >> /var/log/dinari-deployment.log

write_files:
  - path: /etc/systemd/system/dinari-blockchain.service
    content: |
      [Unit]
      Description=DinariBlockchain Service
      After=network.target
      
      [Service]
      Type=simple
      User=ubuntu
      Group=ubuntu
      WorkingDirectory=/opt/dinari-blockchain
      ExecStart=/usr/bin/python3 app.py
      Restart=always
      RestartSec=10
      
      # Environment variables
      Environment=LEVELDB_PATH=/opt/dinari-blockchain/blockchain_data
      Environment=FLASK_ENV=production
      Environment=BLOCKCHAIN_NETWORK=mainnet
      Environment=P2P_PORT=8333
      Environment=API_PORT=5000
      Environment=ENABLE_MINING=true
      Environment=PYTHONUNBUFFERED=1
      
      # Resource limits for 1GB RAM
      MemoryLimit=400M
      MemorySwapMax=0
      
      [Install]
      WantedBy=multi-user.target
    permissions: '0644'

final_message: "DinariBlockchain deployment completed successfully!"
EOF

# Deploy instance with compatible image
echo "Creating Oracle Cloud instance..."
INSTANCE_ID=$(oci compute instance launch \
    --availability-domain "${AD}" \
    --compartment-id ${COMPARTMENT_ID} \
    --shape "VM.Standard.E2.1.Micro" \
    --image-id ${IMAGE_ID} \
    --subnet-id ${SUBNET_ID} \
    --display-name "dinari-blockchain-fixed" \
    --user-data-file cloud-init-fixed.yml \
    --wait-for-state RUNNING \
    --query 'data.id' --raw-output)

if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" = "null" ]; then
    echo "❌ Failed to create instance"
    exit 1
fi

echo "✅ Instance created: ${INSTANCE_ID}"

# Get public IP
echo "Getting public IP address..."
sleep 30  # Wait for network interface
PUBLIC_IP=$(oci compute instance list-vnics --instance-id ${INSTANCE_ID} --query 'data[0]."public-ip"' --raw-output)

if [ -z "$PUBLIC_IP" ] || [ "$PUBLIC_IP" = "null" ]; then
    echo "⚠️  Could not get public IP immediately. Instance may still be initializing."
    echo "Check Oracle Cloud console for IP address."
    PUBLIC_IP="<CHECK_CONSOLE>"
fi

echo "✅ Public IP: ${PUBLIC_IP}"

# Save deployment info  
cat > deployment-fixed.txt << EOF
🎉 DinariBlockchain Deployment SUCCESS!

Instance ID: ${INSTANCE_ID}
Public IP: ${PUBLIC_IP}
GitHub Repo: https://github.com/EmekaIwuagwu/dinari-blockchain.git
Image Used: ${IMAGE_ID}

🌐 Access URLs:
- Main API: http://${PUBLIC_IP}:5000
- Health Check: http://${PUBLIC_IP}:5000/health
- Blockchain Info: http://${PUBLIC_IP}:5000/api/blockchain/info
- RPC Endpoint: http://${PUBLIC_IP}:8545/rpc

🔧 Management:
- SSH: ssh -i ~/.ssh/id_rsa ubuntu@${PUBLIC_IP}
- Check Status: ssh ubuntu@${PUBLIC_IP} 'sudo systemctl status dinari-blockchain'
- View Logs: ssh ubuntu@${PUBLIC_IP} 'sudo journalctl -u dinari-blockchain -f'
- Deployment Log: ssh ubuntu@${PUBLIC_IP} 'cat /var/log/dinari-deployment.log'

⏳ Wait 4-5 minutes for complete setup, then test:
curl http://${PUBLIC_IP}:5000/health

🔥 Your DinariBlockchain is deploying with the CORRECT repository!
EOF

echo ""
echo "🎉 Deployment initiated successfully!"
echo "📋 Check deployment-fixed.txt for details"
echo "⏳ Wait 4-5 minutes for blockchain to be ready"
if [ "$PUBLIC_IP" != "<CHECK_CONSOLE>" ]; then
    echo "🔗 Test URL: http://${PUBLIC_IP}:5000/health"
fi

# Clean up temporary files
rm -f cloud-init-fixed.yml

echo "🚀 DinariBlockchain deployment in progress!"
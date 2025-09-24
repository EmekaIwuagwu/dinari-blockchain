#!/bin/bash
# DinariBlockchain Oracle Cloud Deployment (No Local Docker Required)
# Builds directly on Oracle Cloud instance

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGION="eu-marseille-1"
COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaa7gystzyxk5pxolz4bk4e2datu4flt57evnfymzzt3onmttubcopq"

echo -e "${BLUE}🚀 DinariBlockchain Oracle Cloud Deployment (Cloud Build)${NC}"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check OCI CLI only
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v oci &> /dev/null; then
        log_error "OCI CLI not found. Installing..."
        
        # Install OCI CLI
        bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
        
        # Add to PATH
        echo 'export PATH=$PATH:~/bin' >> ~/.bashrc
        source ~/.bashrc
    fi
    
    log_success "Prerequisites check passed"
}

# Create deployment package
create_deployment_package() {
    log_info "Creating deployment package..."
    
    # Create a deployment directory
    mkdir -p deployment-package
    
    # Copy necessary files
    cp -r . deployment-package/ 2>/dev/null || :
    cp .env deployment-package/ 2>/dev/null || :
    
    # Create streamlined startup script
    cat > deployment-package/start.sh << 'EOF'
#!/bin/bash
# DinariBlockchain startup script for Oracle Cloud

# Install Python dependencies
pip3 install -r requirements.txt || pip install -r requirements.txt

# Create directories
mkdir -p blockchain_data logs wallets

# Set permissions
chmod +x app.py

# Start blockchain
echo "🚀 Starting DinariBlockchain..."
python3 app.py
EOF

    chmod +x deployment-package/start.sh
    
    # Create requirements if not exists
    if [ ! -f "requirements.txt" ]; then
        cat > deployment-package/requirements.txt << 'EOF'
flask==2.3.3
requests==2.31.0
leveldb==0.201
werkzeug==2.3.7
cryptography==41.0.7
ecdsa==0.18.0
EOF
    fi
    
    # Create systemd service file
    cat > deployment-package/dinari-blockchain.service << 'EOF'
[Unit]
Description=DinariBlockchain Node
After=network.target

[Service]
Type=simple
User=opc
WorkingDirectory=/home/opc/dinari-blockchain
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
    
    log_success "Deployment package created"
}

# Create cloud-init script with source deployment
create_cloud_init() {
    log_info "Creating cloud-init configuration..."
    
    # Encode the deployment package
    tar -czf deployment.tar.gz deployment-package/
    DEPLOYMENT_BASE64=$(base64 -w 0 deployment.tar.gz)
    
    cat > cloud-init.yml << EOF
#cloud-config
package_update: true
package_upgrade: true

packages:
  - python3
  - python3-pip
  - python3-dev
  - build-essential
  - curl
  - htop
  - git

write_files:
  - encoding: b64
    content: ${DEPLOYMENT_BASE64}
    path: /home/opc/deployment.tar.gz
    owner: opc:opc
    permissions: '0644'

runcmd:
  # Extract deployment package
  - cd /home/opc && tar -xzf deployment.tar.gz
  - mv deployment-package dinari-blockchain
  - chown -R opc:opc /home/opc/dinari-blockchain
  - chmod +x /home/opc/dinari-blockchain/start.sh
  
  # Install Python dependencies
  - cd /home/opc/dinari-blockchain && pip3 install -r requirements.txt
  
  # Create systemd service
  - cp /home/opc/dinari-blockchain/dinari-blockchain.service /etc/systemd/system/
  - systemctl daemon-reload
  - systemctl enable dinari-blockchain
  
  # Start DinariBlockchain
  - systemctl start dinari-blockchain
  
  # Create status script
  - |
    cat > /home/opc/blockchain-status.sh << 'EOL'
    #!/bin/bash
    echo "=== DinariBlockchain Status ==="
    echo "Service Status:"
    systemctl status dinari-blockchain --no-pager
    echo -e "\nLogs (last 20 lines):"
    journalctl -u dinari-blockchain -n 20 --no-pager
    echo -e "\nAPI Test:"
    curl -s http://localhost:5000/health || echo "API not responding"
    EOL
  - chmod +x /home/opc/blockchain-status.sh
  
  # Open firewall ports
  - ufw allow 5000
  - ufw allow 8333
  - ufw allow 8545
EOF

    log_success "Cloud-init configuration created"
}

# Deploy to Oracle Cloud
deploy_to_oracle() {
    log_info "Deploying to Oracle Cloud..."
    
    # Get availability domain
    AVAILABILITY_DOMAIN=$(oci iam availability-domain list --compartment-id ${COMPARTMENT_ID} --query 'data[0].name' --raw-output)
    
    # Get Ubuntu image OCID
    IMAGE_ID=$(oci compute image list \
        --compartment-id ${COMPARTMENT_ID} \
        --operating-system "Canonical Ubuntu" \
        --shape "VM.Standard.E2.1.Micro" \
        --limit 1 \
        --query 'data[0].id' --raw-output)
    
    # Get subnet ID
    SUBNET_ID=$(oci network subnet list \
        --compartment-id ${COMPARTMENT_ID} \
        --limit 1 \
        --query 'data[0].id' --raw-output)
    
    log_info "Creating Oracle Cloud instance..."
    
    # Create instance
    INSTANCE_ID=$(oci compute instance launch \
        --availability-domain "${AVAILABILITY_DOMAIN}" \
        --compartment-id ${COMPARTMENT_ID} \
        --shape "VM.Standard.E2.1.Micro" \
        --image-id ${IMAGE_ID} \
        --subnet-id ${SUBNET_ID} \
        --display-name "dinari-blockchain-node" \
        --user-data-file cloud-init.yml \
        --wait-for-state RUNNING \
        --query 'data.id' --raw-output)
    
    log_success "Instance created: ${INSTANCE_ID}"
    
    # Wait for IP assignment
    sleep 30
    
    # Get public IP
    PUBLIC_IP=$(oci compute instance list-vnics --instance-id ${INSTANCE_ID} --query 'data[0]."public-ip"' --raw-output)
    log_success "Public IP: ${PUBLIC_IP}"
    
    # Save deployment info
    cat > deployment-info.txt << EOF
=== DinariBlockchain Deployment Info ===
Instance ID: ${INSTANCE_ID}
Public IP: ${PUBLIC_IP}
Region: ${REGION}

🌐 Blockchain Endpoints:
API: http://${PUBLIC_IP}:5000
RPC: http://${PUBLIC_IP}:8545/rpc  
P2P: ${PUBLIC_IP}:8333

🔧 Management Commands:
SSH Access: ssh -i ~/.ssh/id_rsa opc@${PUBLIC_IP}
Status Check: ssh opc@${PUBLIC_IP} './blockchain-status.sh'
View Logs: ssh opc@${PUBLIC_IP} 'journalctl -u dinari-blockchain -f'
Restart Service: ssh opc@${PUBLIC_IP} 'sudo systemctl restart dinari-blockchain'

⏳ Wait 2-3 minutes for blockchain to initialize...
🔗 Test API: curl http://${PUBLIC_IP}:5000/health
EOF
    
    log_success "Deployment info saved to deployment-info.txt"
}

# Main deployment
main() {
    check_prerequisites
    create_deployment_package
    create_cloud_init
    deploy_to_oracle
    
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
    echo -e "${YELLOW}📋 Check deployment-info.txt for details${NC}"
    echo -e "${BLUE}⏳ Blockchain will be ready in 2-3 minutes${NC}"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    rm -rf deployment-package/ deployment.tar.gz cloud-init.yml
    
    if [ -f "deployment-info.txt" ]; then
        INSTANCE_ID=$(grep "Instance ID:" deployment-info.txt | cut -d' ' -f4)
        if [ ! -z "$INSTANCE_ID" ]; then
            oci compute instance terminate --instance-id ${INSTANCE_ID} --force
            log_success "Instance terminated"
        fi
    fi
}

case "${1:-deploy}" in
    deploy) main ;;
    cleanup) cleanup ;;
    *) echo "Usage: $0 [deploy|cleanup]"; exit 1 ;;
esac
#!/bin/bash
# DinariBlockchain Oracle Cloud Always Free Deployment Script
# Optimized for VM.Standard.E2.1.Micro (1GB RAM, 1/8 OCPU)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_NAME="dinari-blockchain"
REGION="eu-marseille-1"
COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaa7gystzyxk5pxolz4bk4e2datu4flt57evnfymzzt3onmttubcopq"
IMAGE_NAME="dinari-node"
REGISTRY="eu-marseille-1.ocir.io/axscu7pwokyf"

echo -e "${BLUE}🚀 DinariBlockchain Oracle Cloud Deployment${NC}"
echo -e "${BLUE}Region: ${REGION}${NC}"
echo -e "${BLUE}Instance Type: Always Free Tier (VM.Standard.E2.1.Micro)${NC}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check OCI CLI
    if ! command -v oci &> /dev/null; then
        log_error "OCI CLI not found. Install from: https://docs.oracle.com/en-us/iaas/tools/oci-cli/"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker."
        exit 1
    fi
    
    # Check .env file
    if [ ! -f ".env" ]; then
        log_error ".env file not found. Please create it with your Oracle Cloud settings."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker image
build_docker_image() {
    log_info "Building Docker image for DinariBlockchain..."
    
    # Create optimized Dockerfile for Always Free tier
    cat > Dockerfile.oracle << 'EOF'
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/blockchain_data /app/logs /app/wallets

# Set permissions
RUN chmod +x app.py

# Expose ports
EXPOSE 5000 8333 8545

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run with memory constraints
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

CMD ["python", "app.py"]
EOF

    # Build image
    docker build -f Dockerfile.oracle -t ${IMAGE_NAME}:latest .
    
    log_success "Docker image built successfully"
}

# Push to Oracle Container Registry
push_to_registry() {
    log_info "Pushing image to Oracle Container Registry..."
    
    # Login to OCIR
    echo "0tV{d(w.jpt9P_99.g#S" | docker login ${REGISTRY} -u axscu7pwokyf/devops4@qstix.com.ng --password-stdin
    
    # Tag and push image
    docker tag ${IMAGE_NAME}:latest ${REGISTRY}/${IMAGE_NAME}:latest
    docker push ${REGISTRY}/${IMAGE_NAME}:latest
    
    log_success "Image pushed to registry"
}

# Create compute instance
create_instance() {
    log_info "Creating Oracle Cloud compute instance..."
    
    # Create cloud-init script
    cat > cloud-init.yml << 'EOF'
#cloud-config
package_update: true
package_upgrade: true

packages:
  - docker.io
  - curl
  - htop

runcmd:
  # Start Docker service
  - systemctl start docker
  - systemctl enable docker
  
  # Add opc user to docker group
  - usermod -aG docker opc
  
  # Login to OCIR
  - echo "0tV{d(w.jpt9P_99.g#S" | docker login eu-marseille-1.ocir.io/axscu7pwokyf -u axscu7pwokyf/devops4@qstix.com.ng --password-stdin
  
  # Pull and run DinariBlockchain
  - docker pull eu-marseille-1.ocir.io/axscu7pwokyf/dinari-node:latest
  - docker run -d --name dinari-blockchain -p 5000:5000 -p 8333:8333 -p 8545:8545 --memory=800m --restart=unless-stopped eu-marseille-1.ocir.io/axscu7pwokyf/dinari-node:latest
  
  # Create startup script
  - |
    cat > /home/opc/start_blockchain.sh << 'EOL'
    #!/bin/bash
    docker start dinari-blockchain || docker run -d --name dinari-blockchain -p 5000:5000 -p 8333:8333 -p 8545:8545 --memory=800m --restart=unless-stopped eu-marseille-1.ocir.io/axscu7pwokyf/dinari-node:latest
    EOL
  - chmod +x /home/opc/start_blockchain.sh
  
write_files:
  - path: /etc/crontab
    content: |
      # Start blockchain on boot
      @reboot opc /home/opc/start_blockchain.sh
    append: true
EOF

    # Create instance
    INSTANCE_ID=$(oci compute instance launch \
        --availability-domain "tUAW:EU-MARSEILLE-1-AD-1" \
        --compartment-id ${COMPARTMENT_ID} \
        --shape "VM.Standard.E2.1.Micro" \
        --image-id $(oci compute image list --compartment-id ${COMPARTMENT_ID} --operating-system "Canonical Ubuntu" --shape "VM.Standard.E2.1.Micro" --limit 1 --query 'data[0].id' --raw-output) \
        --subnet-id $(oci network subnet list --compartment-id ${COMPARTMENT_ID} --limit 1 --query 'data[0].id' --raw-output) \
        --display-name "dinari-blockchain-node" \
        --user-data-file cloud-init.yml \
        --wait-for-state RUNNING \
        --query 'data.id' --raw-output)
    
    log_success "Instance created: ${INSTANCE_ID}"
    
    # Get public IP
    PUBLIC_IP=$(oci compute instance list-vnics --instance-id ${INSTANCE_ID} --query 'data[0]."public-ip"' --raw-output)
    log_success "Public IP: ${PUBLIC_IP}"
    
    # Save instance details
    cat > instance-details.txt << EOF
Instance ID: ${INSTANCE_ID}
Public IP: ${PUBLIC_IP}
Blockchain API: http://${PUBLIC_IP}:5000
RPC Endpoint: http://${PUBLIC_IP}:8545/rpc
P2P Port: ${PUBLIC_IP}:8333

Access via SSH:
ssh -i ~/.ssh/id_rsa opc@${PUBLIC_IP}

Check logs:
ssh opc@${PUBLIC_IP} 'docker logs dinari-blockchain'
EOF
    
    log_success "Instance details saved to instance-details.txt"
}

# Create security rules
create_security_rules() {
    log_info "Creating security rules for blockchain ports..."
    
    # Get default security list
    SECURITY_LIST_ID=$(oci network security-list list --compartment-id ${COMPARTMENT_ID} --limit 1 --query 'data[0].id' --raw-output)
    
    # Add ingress rules for blockchain ports
    oci network security-list update --security-list-id ${SECURITY_LIST_ID} \
        --ingress-security-rules '[
            {
                "source": "0.0.0.0/0",
                "protocol": "6",
                "tcpOptions": {
                    "destinationPortRange": {
                        "min": 5000,
                        "max": 5000
                    }
                }
            },
            {
                "source": "0.0.0.0/0",
                "protocol": "6",
                "tcpOptions": {
                    "destinationPortRange": {
                        "min": 8333,
                        "max": 8333
                    }
                }
            },
            {
                "source": "0.0.0.0/0",
                "protocol": "6",
                "tcpOptions": {
                    "destinationPortRange": {
                        "min": 8545,
                        "max": 8545
                    }
                }
            }
        ]' --force
    
    log_success "Security rules created"
}

# Main deployment function
deploy() {
    log_info "Starting DinariBlockchain deployment to Oracle Cloud Always Free..."
    
    check_prerequisites
    build_docker_image
    push_to_registry
    create_security_rules
    create_instance
    
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
    echo -e "${YELLOW}⏳ Wait 2-3 minutes for the blockchain to start...${NC}"
    echo -e "${BLUE}📁 Check instance-details.txt for connection info${NC}"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up deployment resources..."
    
    if [ -f "instance-details.txt" ]; then
        INSTANCE_ID=$(grep "Instance ID:" instance-details.txt | cut -d' ' -f3)
        if [ ! -z "$INSTANCE_ID" ]; then
            oci compute instance terminate --instance-id ${INSTANCE_ID} --force
            log_success "Instance terminated"
        fi
    fi
    
    # Remove local files
    rm -f Dockerfile.oracle cloud-init.yml instance-details.txt
    log_success "Cleanup complete"
}

# Script options
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Usage: $0 [deploy|cleanup]"
        exit 1
        ;;
esac
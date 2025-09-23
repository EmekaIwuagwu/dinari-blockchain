#!/bin/bash
# DinariBlockchain Deployment Script - 1GB RAM Optimized
# Simple deployment for Oracle Cloud Always Free tier

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] SUCCESS:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING:${NC} $1"
}

# ============================================================================
# CONFIGURATION
# ============================================================================

# Default configuration for 1GB RAM deployment
DEPLOYMENT_TYPE=${DEPLOYMENT_TYPE:-"lightweight"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
VALIDATOR_COUNT=${VALIDATOR_COUNT:-1}
RPC_COUNT=${RPC_COUNT:-1}
DOCKER_IMAGE=${DOCKER_IMAGE:-"dinari/blockchain:latest"}
BACKUP_ENABLED=${BACKUP_ENABLED:-false}

# Terraform configuration
TF_DIR="deploy/terraform"
TF_VAR_FILE="terraform.tfvars"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

check_requirements() {
    log "Checking deployment requirements..."
    
    # Check if running on limited resources
    TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
    if [ "$TOTAL_MEM" -lt 2000 ]; then
        warning "Detected limited memory ($TOTAL_MEM MB). Using lightweight configuration."
        DEPLOYMENT_TYPE="lightweight"
    fi
    
    # Check required tools
    for tool in docker terraform kubectl; do
        if ! command -v $tool &> /dev/null; then
            error "$tool is required but not installed"
            exit 1
        fi
    done
    
    # Check Oracle Cloud credentials
    if [ -z "$OCI_TENANCY_ID" ] || [ -z "$OCI_USER_ID" ]; then
        error "Oracle Cloud credentials not set. Please set OCI_TENANCY_ID and OCI_USER_ID"
        exit 1
    fi
    
    success "Requirements check passed"
}

generate_terraform_vars() {
    log "Generating Terraform variables for 1GB deployment..."
    
    cat > $TF_DIR/$TF_VAR_FILE << EOF
# DinariBlockchain - 1GB RAM Optimized Deployment
# Generated on $(date)

# Oracle Cloud Authentication (set via environment variables)
tenancy_ocid     = "$OCI_TENANCY_ID"
user_ocid        = "$OCI_USER_ID"
fingerprint      = "$OCI_FINGERPRINT"
private_key_path = "$OCI_PRIVATE_KEY_PATH"
region           = "${OCI_REGION:-us-ashburn-1}"
compartment_id   = "$OCI_COMPARTMENT_ID"

# SSH Key
ssh_public_key = file("${SSH_PUBLIC_KEY_PATH:-~/.ssh/id_rsa.pub}")

# Deployment Configuration
environment = "$ENVIRONMENT"
project_name = "dinari-blockchain-lightweight"

# 1GB RAM Instance Configuration
validator_count = $VALIDATOR_COUNT
rpc_count = $RPC_COUNT

# Oracle Cloud Always Free Tier
validator_instance_shape = "VM.Standard.A1.Flex"
validator_ocpus = 1
validator_memory_gbs = 1  # 1GB RAM limit

rpc_instance_shape = "VM.Standard.A1.Flex"
rpc_ocpus = 1
rpc_memory_gbs = 1  # 1GB RAM limit

# Storage (minimal)
blockchain_data_volume_size_gb = 20
boot_volume_size_gb = 50

# Load Balancer (Always Free)
load_balancer_shape = "10Mbps"
load_balancer_bandwidth_mbps = 10

# LevelDB Configuration (optimized for 1GB)
leveldb_cache_size_mb = 32
leveldb_backup_enabled = $BACKUP_ENABLED

# Blockchain Configuration
native_token_config = {
    name         = "Dinari"
    symbol       = "DINARI"
    total_supply = 100000000
    decimals     = 18
}

stablecoin_config = {
    name             = "Afrocoin"
    symbol           = "AFC"
    total_supply     = 200000000
    decimals         = 18
    collateral_ratio = 150
}

# Performance Tuning for 1GB RAM
enable_auto_scaling = false
preemptible_instances = false
enable_detailed_monitoring = false

# Cost Optimization
backup_storage_tier = "Standard"
enable_cross_region_backup = false
EOF
    
    success "Terraform variables generated for 1GB deployment"
}

build_docker_images() {
    log "Building lightweight Docker images..."
    
    # Build validator image
    docker build -f deploy/docker/Dockerfile.validator -t dinari/validator:lightweight .
    
    # Build RPC image  
    docker build -f deploy/docker/Dockerfile.rpc -t dinari/rpc:lightweight .
    
    # Tag as latest for deployment
    docker tag dinari/validator:lightweight $DOCKER_IMAGE
    docker tag dinari/rpc:lightweight $DOCKER_IMAGE
    
    success "Lightweight Docker images built"
}

deploy_infrastructure() {
    log "Deploying Oracle Cloud infrastructure..."
    
    cd $TF_DIR
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    log "Planning Terraform deployment..."
    terraform plan -var-file=$TF_VAR_FILE -out=tfplan
    
    # Apply deployment
    log "Applying Terraform deployment..."
    terraform apply tfplan
    
    cd - > /dev/null
    success "Infrastructure deployment completed"
}

deploy_kubernetes() {
    if [ "$DEPLOYMENT_TYPE" = "kubernetes" ]; then
        log "Deploying to Kubernetes (lightweight)..."
        
        # Deploy namespace and configmaps first
        kubectl apply -f deploy/kubernetes/validator-deployment.yaml
        kubectl apply -f deploy/kubernetes/rpc-deployment.yaml
        kubectl apply -f deploy/kubernetes/load-balancer.yaml
        
        # Wait for deployments
        kubectl wait --for=condition=available --timeout=300s deployment/dinari-validator -n dinari-blockchain
        kubectl wait --for=condition=available --timeout=300s deployment/dinari-rpc -n dinari-blockchain
        
        success "Kubernetes deployment completed"
    fi
}

test_deployment() {
    log "Testing deployment..."
    
    # Get load balancer IP from Terraform output
    cd $TF_DIR
    LB_IP=$(terraform output -raw load_balancer_ip 2>/dev/null || echo "")
    cd - > /dev/null
    
    if [ -n "$LB_IP" ]; then
        # Test health endpoint
        log "Testing health endpoint at http://$LB_IP/health"
        if curl -sf --max-time 10 http://$LB_IP/health > /dev/null; then
            success "Health check passed"
        else
            warning "Health check failed, but deployment may still be starting"
        fi
        
        # Test RPC endpoint
        log "Testing RPC endpoint..."
        RPC_RESPONSE=$(curl -sf --max-time 10 -X POST \
            -H "Content-Type: application/json" \
            -d '{"method":"dinari_getBlockchainInfo","params":[],"id":1}' \
            http://$LB_IP/rpc 2>/dev/null || echo "")
        
        if [ -n "$RPC_RESPONSE" ]; then
            success "RPC endpoint responding"
        else
            warning "RPC endpoint not responding yet"
        fi
        
        # Display endpoints
        echo ""
        success "=== Deployment Complete ==="
        echo "🌍 Blockchain API: http://$LB_IP"
        echo "🔗 Health Check: http://$LB_IP/health"
        echo "⚡ RPC Endpoint: http://$LB_IP/rpc"
        echo "📊 Blockchain Info: http://$LB_IP/api/blockchain/info"
        echo ""
    else
        warning "Could not retrieve load balancer IP"
    fi
}

cleanup_deployment() {
    log "Cleaning up deployment..."
    
    cd $TF_DIR
    terraform destroy -var-file=$TF_VAR_FILE -auto-approve
    cd - > /dev/null
    
    success "Deployment cleaned up"
}

show_usage() {
    echo "DinariBlockchain Deployment Script (1GB RAM Optimized)"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  deploy     Deploy complete infrastructure"
    echo "  build      Build Docker images only"
    echo "  test       Test existing deployment"
    echo "  cleanup    Destroy infrastructure"
    echo "  local      Deploy locally with docker-compose"
    echo ""
    echo "Options:"
    echo "  --environment [dev|staging|prod]  Deployment environment"
    echo "  --validators [1-3]                Number of validator nodes"
    echo "  --rpc-nodes [1-2]                 Number of RPC nodes"
    echo "  --backup                          Enable backups"
    echo ""
    echo "Environment Variables:"
    echo "  OCI_TENANCY_ID       Oracle Cloud tenancy ID"
    echo "  OCI_USER_ID          Oracle Cloud user ID"
    echo "  OCI_FINGERPRINT      API key fingerprint"
    echo "  OCI_PRIVATE_KEY_PATH Path to private key"
    echo "  OCI_COMPARTMENT_ID   Compartment ID"
    echo ""
    echo "Examples:"
    echo "  $0 deploy --environment prod --validators 1 --rpc-nodes 1"
    echo "  $0 local"
    echo "  $0 cleanup"
}

deploy_local() {
    log "Deploying locally with docker-compose (1GB optimized)..."
    
    # Build images first
    build_docker_images
    
    # Start services
    docker-compose -f deploy/docker/docker-compose.yml up -d
    
    # Wait for services
    sleep 30
    
    # Test local deployment
    if curl -sf http://localhost:8080/health > /dev/null; then
        success "Local deployment successful"
        echo ""
        echo "🌍 Local API: http://localhost:8080"
        echo "🔗 Health Check: http://localhost:8080/health"
        echo "⚡ RPC Endpoint: http://localhost:8080/rpc"
    else
        error "Local deployment failed"
        docker-compose -f deploy/docker/docker-compose.yml logs
        exit 1
    fi
}

# ============================================================================
# COMMAND LINE PARSING
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --validators)
            VALIDATOR_COUNT="$2"
            shift 2
            ;;
        --rpc-nodes)
            RPC_COUNT="$2"
            shift 2
            ;;
        --backup)
            BACKUP_ENABLED=true
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            COMMAND="$1"
            shift
            ;;
    esac
done

# ============================================================================
# MAIN EXECUTION
# ============================================================================

case "${COMMAND:-deploy}" in
    deploy)
        log "Starting DinariBlockchain deployment (1GB RAM optimized)..."
        check_requirements
        generate_terraform_vars
        build_docker_images
        deploy_infrastructure
        deploy_kubernetes
        test_deployment
        success "Deployment completed successfully!"
        ;;
    build)
        build_docker_images
        ;;
    test)
        test_deployment
        ;;
    cleanup)
        cleanup_deployment
        ;;
    local)
        deploy_local
        ;;
    *)
        error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
#!/bin/bash
# DinariBlockchain Validator Node Setup - 1GB RAM Optimized
# Lightweight installation script for Oracle Cloud Always Free

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

# ============================================================================
# SYSTEM OPTIMIZATION FOR 1GB RAM
# ============================================================================

optimize_system() {
    log "Optimizing system for 1GB RAM..."
    
    # Reduce swappiness (use less swap)
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    
    # Optimize memory usage
    echo 'vm.vfs_cache_pressure=50' >> /etc/sysctl.conf
    echo 'vm.dirty_ratio=5' >> /etc/sysctl.conf
    echo 'vm.dirty_background_ratio=3' >> /etc/sysctl.conf
    
    # Apply immediately
    sysctl -p
    
    # Disable unnecessary services
    systemctl disable snapd || true
    systemctl disable cups || true
    systemctl disable bluetooth || true
    
    success "System optimized for 1GB RAM"
}

# ============================================================================
# MINIMAL PACKAGE INSTALLATION
# ============================================================================

install_essentials() {
    log "Installing minimal essential packages..."
    
    # Update system
    apt-get update
    
    # Install only essential packages
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        git \
        python3 \
        python3-pip \
        python3-venv \
        build-essential \
        libleveldb-dev \
        libsnappy-dev \
        pkg-config \
        supervisor
    
    # Clean up
    apt-get autoremove -y
    apt-get autoclean
    rm -rf /var/lib/apt/lists/*
    
    success "Essential packages installed"
}

# ============================================================================
# DOCKER INSTALLATION (Lightweight)
# ============================================================================

install_docker() {
    log "Installing Docker (minimal setup)..."
    
    # Install Docker using convenience script (smaller footprint)
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Add ubuntu user to docker group
    usermod -aG docker ubuntu
    
    # Configure Docker for 1GB RAM
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << EOF
{
    "storage-driver": "overlay2",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "default-runtime": "runc",
    "live-restore": true,
    "userland-proxy": false,
    "no-new-privileges": true
}
EOF
    
    # Start Docker
    systemctl enable docker
    systemctl start docker
    
    success "Docker installed and configured for 1GB RAM"
}

# ============================================================================
# DINARI BLOCKCHAIN SETUP
# ============================================================================

setup_dinari_node() {
    log "Setting up DinariBlockchain validator node..."
    
    # Create dinari directory
    mkdir -p /opt/dinari
    cd /opt/dinari
    
    # Create minimal environment file
    cat > .env << EOF
NODE_ID=${node_id}
NODE_TYPE=${node_type}
NODE_ENV=${environment}
LEVELDB_PATH=/opt/dinari/data
LEVELDB_CACHE_SIZE_MB=64
MINING_ENABLED=${mining_enabled}
VALIDATOR_ENABLED=${validator_enabled}
P2P_PORT=8333
API_PORT=5000
LOG_LEVEL=INFO
EOF
    
    # Create data directory
    mkdir -p /opt/dinari/data
    chown -R ubuntu:ubuntu /opt/dinari
    
    success "DinariBlockchain validator node configured"
}

# ============================================================================
# CONTAINER STARTUP
# ============================================================================

create_startup_script() {
    log "Creating lightweight startup script..."
    
    cat > /opt/dinari/start-validator.sh << 'EOF'
#!/bin/bash
# Start DinariBlockchain Validator - 1GB RAM optimized

# Set memory limits
export MALLOC_TRIM_THRESHOLD_=131072
export MALLOC_TOP_PAD_=131072

# Start with memory constraints
docker run -d \
    --name dinari-validator \
    --restart unless-stopped \
    --memory="400m" \
    --memory-swap="400m" \
    --cpus="0.5" \
    -p 5000:5000 \
    -p 8333:8333 \
    -v /opt/dinari/data:/app/dinari_data \
    -v /opt/dinari/.env:/app/.env \
    --env-file /opt/dinari/.env \
    dinari/blockchain:latest

echo "DinariBlockchain Validator started with 400MB memory limit"
EOF
    
    chmod +x /opt/dinari/start-validator.sh
    
    success "Startup script created"
}

# ============================================================================
# MONITORING SETUP (Minimal)
# ============================================================================

setup_minimal_monitoring() {
    log "Setting up minimal monitoring..."
    
    # Create simple health check script
    cat > /opt/dinari/health-check.sh << 'EOF'
#!/bin/bash
# Simple health check for 1GB RAM systems

# Check if container is running
if ! docker ps | grep -q dinari-validator; then
    echo "CRITICAL: Validator container not running"
    exit 1
fi

# Check API health
if ! curl -sf http://localhost:5000/health > /dev/null; then
    echo "CRITICAL: API health check failed"
    exit 1
fi

# Check memory usage
MEMORY_USAGE=$(docker stats --no-stream --format "{{.MemUsage}}" dinari-validator | cut -d'/' -f1)
echo "OK: Validator running, Memory: $MEMORY_USAGE"
EOF
    
    chmod +x /opt/dinari/health-check.sh
    
    # Add to crontab for periodic checks
    (crontab -l 2>/dev/null; echo "*/5 * * * * /opt/dinari/health-check.sh >> /var/log/dinari-health.log 2>&1") | crontab -
    
    success "Minimal monitoring configured"
}

# ============================================================================
# SYSTEMD SERVICE
# ============================================================================

create_systemd_service() {
    log "Creating systemd service..."
    
    cat > /etc/systemd/system/dinari-validator.service << EOF
[Unit]
Description=DinariBlockchain Validator Node
Requires=docker.service
After=docker.service

[Service]
Type=forking
Restart=always
RestartSec=30
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/dinari
ExecStart=/opt/dinari/start-validator.sh
ExecStop=/usr/bin/docker stop dinari-validator
ExecReload=/usr/bin/docker restart dinari-validator

# Memory and process limits
LimitNOFILE=8192
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable dinari-validator
    
    success "Systemd service created"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    log "=== DinariBlockchain Validator Setup (1GB RAM) ==="
    
    # System optimization
    optimize_system
    
    # Install packages
    install_essentials
    install_docker
    
    # Setup blockchain node
    setup_dinari_node
    create_startup_script
    setup_minimal_monitoring
    create_systemd_service
    
    # Start the service
    log "Starting DinariBlockchain Validator..."
    systemctl start dinari-validator
    
    # Wait for startup
    sleep 30
    
    # Check status
    if systemctl is-active --quiet dinari-validator; then
        success "=== DinariBlockchain Validator Setup Complete ==="
        success "API available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
        success "Health check: curl http://localhost:5000/health"
        success "View logs: docker logs dinari-validator"
    else
        error "Validator service failed to start. Check logs: journalctl -u dinari-validator"
        exit 1
    fi
}

# Template variables (replaced by Terraform)
node_id="${node_id}"
node_type="${node_type}"
environment="${environment}"
mining_enabled="${mining_enabled}"
validator_enabled="${validator_enabled}"
docker_image="${docker_image}"

# Run main function
main "$@"
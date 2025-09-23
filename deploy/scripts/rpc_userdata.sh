#!/bin/bash
# DinariBlockchain RPC Node Setup - 1GB RAM Optimized
# Minimal RPC installation script for Oracle Cloud Always Free

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
# SYSTEM OPTIMIZATION FOR 1GB RAM (RPC NODE)
# ============================================================================

optimize_system() {
    log "Optimizing system for 1GB RAM RPC node..."
    
    # More aggressive memory optimization for RPC nodes
    echo 'vm.swappiness=5' >> /etc/sysctl.conf
    echo 'vm.vfs_cache_pressure=60' >> /etc/sysctl.conf
    echo 'vm.dirty_ratio=3' >> /etc/sysctl.conf
    echo 'vm.dirty_background_ratio=2' >> /etc/sysctl.conf
    
    # Apply immediately
    sysctl -p
    
    # Disable more services for RPC nodes
    systemctl disable snapd || true
    systemctl disable cups || true
    systemctl disable bluetooth || true
    systemctl disable ufw || true  # RPC nodes use minimal firewall
    
    success "System optimized for 1GB RAM RPC node"
}

# ============================================================================
# MINIMAL PACKAGE INSTALLATION (RPC)
# ============================================================================

install_essentials() {
    log "Installing minimal packages for RPC node..."
    
    # Update system
    apt-get update
    
    # Install only RPC essentials (no mining tools)
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        python3 \
        python3-pip \
        build-essential \
        libleveldb-dev \
        libsnappy-dev \
        pkg-config
    
    # Clean up aggressively
    apt-get autoremove -y --purge
    apt-get autoclean
    rm -rf /var/lib/apt/lists/*
    rm -rf /tmp/*
    
    success "Minimal RPC packages installed"
}

# ============================================================================
# DOCKER INSTALLATION (RPC Optimized)
# ============================================================================

install_docker() {
    log "Installing Docker for RPC node..."
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Add ubuntu user to docker group
    usermod -aG docker ubuntu
    
    # Configure Docker for RPC (even more conservative)
    mkdir -p /etc/docker
    cat > /etc/docker/daemon.json << EOF
{
    "storage-driver": "overlay2",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "5m",
        "max-file": "2"
    },
    "default-runtime": "runc",
    "live-restore": true,
    "userland-proxy": false,
    "no-new-privileges": true,
    "max-concurrent-downloads": 3,
    "max-concurrent-uploads": 5
}
EOF
    
    # Start Docker
    systemctl enable docker
    systemctl start docker
    
    success "Docker configured for RPC node (1GB RAM)"
}

# ============================================================================
# DINARI RPC NODE SETUP
# ============================================================================

setup_dinari_rpc() {
    log "Setting up DinariBlockchain RPC node..."
    
    # Create dinari directory
    mkdir -p /opt/dinari
    cd /opt/dinari
    
    # Create RPC-specific environment
    cat > .env << EOF
NODE_ID=${node_id}
NODE_TYPE=${node_type}
NODE_ENV=${environment}
LEVELDB_PATH=/opt/dinari/data
LEVELDB_CACHE_SIZE_MB=32
MINING_ENABLED=${mining_enabled}
VALIDATOR_ENABLED=${validator_enabled}
RPC_ENABLED=true
API_RATE_LIMIT=200
MAX_CONNECTIONS=50
P2P_PORT=8333
API_PORT=5000
LOG_LEVEL=WARNING
BOOTSTRAP_NODES=${bootstrap_nodes:-""}
EOF
    
    # Create data directory
    mkdir -p /opt/dinari/data
    chown -R ubuntu:ubuntu /opt/dinari
    
    success "DinariBlockchain RPC node configured"
}

# ============================================================================
# CONTAINER STARTUP (RPC)
# ============================================================================

create_startup_script() {
    log "Creating RPC startup script..."
    
    cat > /opt/dinari/start-rpc.sh << 'EOF'
#!/bin/bash
# Start DinariBlockchain RPC - 1GB RAM optimized

# Set memory limits (more aggressive for RPC)
export MALLOC_TRIM_THRESHOLD_=65536
export MALLOC_TOP_PAD_=65536

# Start with stricter memory constraints
docker run -d \
    --name dinari-rpc \
    --restart unless-stopped \
    --memory="300m" \
    --memory-swap="300m" \
    --memory-reservation="250m" \
    --cpus="0.3" \
    -p 5000:5000 \
    -p 8333:8333 \
    -v /opt/dinari/data:/app/dinari_data \
    -v /opt/dinari/.env:/app/.env \
    --env-file /opt/dinari/.env \
    --oom-kill-disable=false \
    dinari/blockchain:latest

echo "DinariBlockchain RPC started with 300MB memory limit"
EOF
    
    chmod +x /opt/dinari/start-rpc.sh
    
    success "RPC startup script created"
}

# ============================================================================
# MINIMAL MONITORING (RPC)
# ============================================================================

setup_minimal_monitoring() {
    log "Setting up minimal RPC monitoring..."
    
    # Create RPC health check script
    cat > /opt/dinari/health-check.sh << 'EOF'
#!/bin/bash
# Simple health check for RPC node

# Check if container is running
if ! docker ps | grep -q dinari-rpc; then
    echo "CRITICAL: RPC container not running"
    exit 1
fi

# Check API health
if ! curl -sf --max-time 5 http://localhost:5000/health > /dev/null; then
    echo "CRITICAL: RPC API health check failed"
    exit 1
fi

# Check memory usage
MEMORY_USAGE=$(docker stats --no-stream --format "{{.MemUsage}}" dinari-rpc | cut -d'/' -f1)
echo "OK: RPC running, Memory: $MEMORY_USAGE"
EOF
    
    chmod +x /opt/dinari/health-check.sh
    
    # Add to crontab (less frequent for RPC)
    (crontab -l 2>/dev/null; echo "*/10 * * * * /opt/dinari/health-check.sh >> /var/log/dinari-rpc-health.log 2>&1") | crontab -
    
    success "Minimal RPC monitoring configured"
}

# ============================================================================
# SYSTEMD SERVICE (RPC)
# ============================================================================

create_systemd_service() {
    log "Creating RPC systemd service..."
    
    cat > /etc/systemd/system/dinari-rpc.service << EOF
[Unit]
Description=DinariBlockchain RPC Node
Requires=docker.service
After=docker.service

[Service]
Type=forking
Restart=always
RestartSec=45
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/dinari
ExecStart=/opt/dinari/start-rpc.sh
ExecStop=/usr/bin/docker stop dinari-rpc
ExecReload=/usr/bin/docker restart dinari-rpc

# Stricter limits for RPC
LimitNOFILE=4096
LimitNPROC=2048
MemoryLimit=350M

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable dinari-rpc
    
    success "RPC systemd service created"
}

# ============================================================================
# REVERSE PROXY (Optional, minimal)
# ============================================================================

setup_simple_proxy() {
    if [ "${setup_proxy:-false}" = "true" ]; then
        log "Setting up simple nginx proxy..."
        
        # Install minimal nginx
        apt-get update
        apt-get install -y --no-install-recommends nginx-light
        
        # Create minimal nginx config
        cat > /etc/nginx/sites-available/dinari << 'EOF'
server {
    listen 80 default_server;
    server_name _;
    
    # Simple proxy to RPC node
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
EOF
        
        # Enable site and disable default
        rm -f /etc/nginx/sites-enabled/default
        ln -s /etc/nginx/sites-available/dinari /etc/nginx/sites-enabled/
        
        # Start nginx
        systemctl enable nginx
        systemctl start nginx
        
        success "Simple nginx proxy configured"
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    log "=== DinariBlockchain RPC Setup (1GB RAM) ==="
    
    # System optimization
    optimize_system
    
    # Install packages
    install_essentials
    install_docker
    
    # Setup RPC node
    setup_dinari_rpc
    create_startup_script
    setup_minimal_monitoring
    create_systemd_service
    
    # Optional proxy
    setup_simple_proxy
    
    # Start the service
    log "Starting DinariBlockchain RPC..."
    systemctl start dinari-rpc
    
    # Wait for startup
    sleep 20
    
    # Check status
    if systemctl is-active --quiet dinari-rpc; then
        success "=== DinariBlockchain RPC Setup Complete ==="
        success "API available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
        success "Health check: curl http://localhost:5000/health"
        success "RPC endpoint: curl -X POST -d '{\"method\":\"dinari_getBlockchainInfo\",\"id\":1}' http://localhost:5000/rpc"
        success "View logs: docker logs dinari-rpc"
    else
        error "RPC service failed to start. Check logs: journalctl -u dinari-rpc"
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
bootstrap_nodes="${bootstrap_nodes}"
setup_proxy="${setup_proxy:-false}"

# Run main function
main "$@"
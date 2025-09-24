#!/bin/bash
# Complete Afrocoin/DinariBlockchain Permanent Deployment Script
# Run once and leave running - includes systemd service, monitoring, and auto-restart

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="dinari-blockchain"
APP_USER="ubuntu"
APP_DIR="/opt/dinari-blockchain"
LOG_DIR="/var/log/dinari-blockchain"
DATA_DIR="/var/lib/dinari-blockchain"
SERVICE_NAME="dinari-blockchain-node"
PORT=5000
P2P_PORT=8333

echo -e "${BLUE}🚀 Dinari-Blockchain Permanent Deployment${NC}"
echo -e "${BLUE}This script sets up systemd service, monitoring, and auto-restart${NC}"

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

# System optimization for blockchain
optimize_system() {
    log_info "Optimizing system for blockchain..."
    
    # Update system
    apt update && apt upgrade -y
    
    # Install essential packages
    apt install -y python3 python3-pip python3-venv git curl wget htop nano
    apt install -y build-essential libssl-dev libffi-dev python3-dev
    
    # Optimize system parameters
    cat >> /etc/sysctl.conf << 'EOF'
# Blockchain optimizations
net.core.somaxconn = 4096
net.ipv4.tcp_max_syn_backlog = 4096
vm.swappiness = 10
EOF
    sysctl -p
    
    log_success "System optimized"
}

# Setup blockchain application
setup_blockchain() {
    log_info "Setting up Dinari-blockchain application..."
    
    # Create directories
    mkdir -p $APP_DIR $LOG_DIR $DATA_DIR
    
    # Clone or copy your blockchain code to APP_DIR
    # If you have it locally, copy it:
    if [ -d "./dinari-blockchain" ] || [ -d "." ]; then
        log_info "Copying blockchain code to $APP_DIR..."
        cp -r . $APP_DIR/
        chown -R $APP_USER:$APP_USER $APP_DIR
    else
        log_error "Blockchain code not found in current directory"
        exit 1
    fi
    
    # Create Python virtual environment
    cd $APP_DIR
    python3 -m venv venv
    source venv/bin/activate
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # Install basic requirements
        pip install flask plyvel cryptography requests
    fi
    
    # Set proper ownership
    chown -R $APP_USER:$APP_USER $APP_DIR $LOG_DIR $DATA_DIR
    
    log_success "Blockchain application setup complete"
}

# Create production environment file
create_env_file() {
    log_info "Creating production environment file..."
    
    cat > $APP_DIR/.env << 'EOF'
# Dinari-Blockchain Production Environment
NODE_ENV=production
DINARI_DEBUG=false
LEVELDB_CACHE_SIZE_MB=32
BLOCKCHAIN_NETWORK=mainnet
MINING_ENABLED=true
NODE_TYPE=validator
CONTRACTS_ENABLED=true
P2P_PORT=8333
RPC_PORT=5000
MAX_BLOCK_SIZE=1048576
MINING_DIFFICULTY=4
CONSENSUS_ALGORITHM=pos
VALIDATOR_REWARD=10
TRANSACTION_FEE=0.001
EOF
    
    chown $APP_USER:$APP_USER $APP_DIR/.env
    log_success "Environment file created"
}

# Create startup script
create_startup_script() {
    log_info "Creating startup script..."
    
    cat > $APP_DIR/start-production.sh << 'EOF'
#!/bin/bash
cd /opt/dinari-blockchain
source venv/bin/activate
export NODE_ENV=production
export DINARI_DEBUG=false
export LEVELDB_CACHE_SIZE_MB=32

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Start the blockchain
if [ -f app.py ]; then
    python app.py
elif [ -f main.py ]; then
    python main.py
elif [ -f rpc_server.py ]; then
    python rpc_server.py
else
    echo "No main application file found (app.py, main.py, or rpc_server.py)"
    exit 1
fi
EOF
    
    chmod +x $APP_DIR/start-production.sh
    chown $APP_USER:$APP_USER $APP_DIR/start-production.sh
    
    log_success "Startup script created"
}

# Create systemd service
create_systemd_service() {
    log_info "Creating systemd service for permanent running..."
    
    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Dinari-Blockchain Node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=NODE_ENV=production
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=$APP_DIR/start-production.sh
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME
KillMode=mixed
TimeoutStopSec=30
LimitNOFILE=65535

# Resource limits
MemoryLimit=800M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    
    log_success "Systemd service created and enabled"
}

# Setup monitoring and health checks
setup_monitoring() {
    log_info "Setting up monitoring and health checks..."
    
    # Create health check script
    cat > $APP_DIR/health-check.sh << 'EOF'
#!/bin/bash
# Dinari-Blockchain Health Check

LOG_FILE="/var/log/dinari-blockchain/health.log"

# Check if service is running
if ! systemctl is-active --quiet dinari-blockchain-node; then
    echo "$(date): ❌ Dinari-blockchain service is not running. Attempting restart..." >> $LOG_FILE
    systemctl restart dinari-blockchain-node
    sleep 15
    if systemctl is-active --quiet dinari-blockchain-node; then
        echo "$(date): ✅ Dinari-blockchain service restarted successfully" >> $LOG_FILE
    else
        echo "$(date): ❌ Failed to restart Dinari-blockchain service" >> $LOG_FILE
    fi
    exit 1
fi

# Check API health (if applicable)
if curl -sf --max-time 10 http://localhost:5000/health > /dev/null 2>&1; then
    echo "$(date): ✅ API health check passed" >> $LOG_FILE
elif curl -sf --max-time 10 http://localhost:8545/health > /dev/null 2>&1; then
    echo "$(date): ✅ RPC health check passed" >> $LOG_FILE
else
    echo "$(date): ⚠️  API health check failed, but service is running" >> $LOG_FILE
fi

# Check disk space
USAGE=$(df -h $APP_DIR | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $USAGE -gt 85 ]; then
    echo "$(date): ⚠️  Disk usage is ${USAGE}%" >> $LOG_FILE
fi

# Check memory usage
MEMORY_USAGE=$(systemctl show dinari-blockchain-node --property=MemoryCurrent --value)
MEMORY_MB=$((MEMORY_USAGE / 1024 / 1024))
echo "$(date): 📊 Memory usage: ${MEMORY_MB}MB" >> $LOG_FILE
EOF
    
    chmod +x $APP_DIR/health-check.sh
    chown $APP_USER:$APP_USER $APP_DIR/health-check.sh
    
    # Add to crontab for periodic checks (every 5 minutes)
    (crontab -u $APP_USER -l 2>/dev/null; echo "*/5 * * * * $APP_DIR/health-check.sh") | crontab -u $APP_USER -
    
    log_success "Monitoring setup complete"
}

# Setup log rotation
setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    cat > /etc/logrotate.d/dinari-blockchain << 'EOF'
/var/log/dinari-blockchain/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload dinari-blockchain-node
    endscript
}
EOF
    
    log_success "Log rotation configured"
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall..."
    
    # Install ufw if not present
    apt install -y ufw
    
    # Basic firewall rules
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow blockchain ports
    ufw allow $PORT comment 'Dinari-blockchain API'
    ufw allow $P2P_PORT comment 'Dinari-blockchain P2P'
    ufw allow 8545 comment 'Dinari-blockchain RPC'
    
    # Enable firewall
    ufw --force enable
    
    log_success "Firewall configured"
}

# Create management commands
create_management_commands() {
    log_info "Creating management commands..."
    
    cat > $APP_DIR/manage-blockchain.sh << 'EOF'
#!/bin/bash
# Dinari-Blockchain Management Script

SERVICE_NAME="dinari-blockchain-node"

case "$1" in
    start)
        echo "🚀 Starting Dinari-blockchain..."
        sudo systemctl start $SERVICE_NAME
        ;;
    stop)
        echo "🛑 Stopping Dinari-blockchain..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "🔄 Restarting Dinari-blockchain..."
        sudo systemctl restart $SERVICE_NAME
        ;;
    status)
        echo "📊 Dinari-blockchain status:"
        sudo systemctl status $SERVICE_NAME
        ;;
    logs)
        echo "📜 Viewing Dinari-blockchain logs (press Ctrl+C to exit):"
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    health)
        echo "🏥 Running health check..."
        /opt/dinari-blockchain/health-check.sh
        tail -10 /var/log/dinari-blockchain/health.log
        ;;
    backup)
        echo "💾 Creating blockchain data backup..."
        sudo tar -czf "/home/ubuntu/dinari-blockchain-backup-$(date +%Y%m%d-%H%M%S).tar.gz" -C /var/lib dinari-blockchain
        echo "✅ Backup created in /home/ubuntu/"
        ;;
    info)
        echo "ℹ️  Dinari-Blockchain Information:"
        echo "   Status: $(systemctl is-active dinari-blockchain-node)"
        echo "   Uptime: $(systemctl show dinari-blockchain-node --property=ActiveEnterTimestamp --value)"
        echo "   Memory: $(systemctl show dinari-blockchain-node --property=MemoryCurrent --value | awk '{print $1/1024/1024 " MB"}')"
        echo "   Logs: sudo journalctl -u dinari-blockchain-node"
        echo "   Data: /var/lib/dinari-blockchain"
        if curl -sf http://localhost:5000/health > /dev/null 2>&1; then
            echo "   API: ✅ http://localhost:5000"
        elif curl -sf http://localhost:8545/health > /dev/null 2>&1; then
            echo "   RPC: ✅ http://localhost:8545"
        fi
        ;;
    *)
        echo "Dinari-Blockchain Management"
        echo "Usage: $0 {start|stop|restart|status|logs|health|backup|info}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the blockchain"
        echo "  stop    - Stop the blockchain"  
        echo "  restart - Restart the blockchain"
        echo "  status  - Show service status"
        echo "  logs    - View live logs"
        echo "  health  - Run health check"
        echo "  backup  - Create data backup"
        echo "  info    - Show system info"
        exit 1
        ;;
esac
EOF
    
    chmod +x $APP_DIR/manage-blockchain.sh
    chown $APP_USER:$APP_USER $APP_DIR/manage-blockchain.sh
    
    # Create symlink for easy access
    ln -sf $APP_DIR/manage-blockchain.sh /usr/local/bin/dinari
    
    log_success "Management commands created"
}

# Main execution function
main() {
    log_info "=== Starting Dinari-Blockchain Permanent Deployment ==="
    
    # Run all setup functions
    optimize_system
    setup_blockchain
    create_env_file
    create_startup_script
    create_systemd_service
    setup_monitoring
    setup_log_rotation
    configure_firewall
    create_management_commands
    
    # Start the service
    log_info "Starting Dinari-blockchain service..."
    systemctl start $SERVICE_NAME
    
    # Wait for startup
    sleep 15
    
    # Check status
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_success "=== 🎉 Dinari-Blockchain Deployment Complete! ==="
        echo ""
        echo -e "${GREEN}✅ Service Status:${NC} $(systemctl is-active $SERVICE_NAME)"
        echo -e "${GREEN}✅ Auto-start:${NC} Enabled (will start automatically on boot)"
        echo -e "${GREEN}✅ Monitoring:${NC} Health checks every 5 minutes"
        echo -e "${GREEN}✅ Log rotation:${NC} Configured"
        echo -e "${GREEN}✅ Firewall:${NC} Configured"
        echo ""
        echo -e "${BLUE}🎯 Management Commands:${NC}"
        echo "   dinari start      # Start blockchain"
        echo "   dinari stop       # Stop blockchain"
        echo "   dinari restart    # Restart blockchain"
        echo "   dinari status     # Check status"
        echo "   dinari logs       # View logs"
        echo "   dinari health     # Health check"
        echo "   dinari backup     # Create backup"
        echo "   dinari info       # System information"
        echo ""
        
        # Use your AWS public IP
        PUBLIC_IP="54.90.115.78"
        
        echo -e "${BLUE}🌐 Access Points:${NC}"
        if curl -sf http://localhost:$PORT/health > /dev/null 2>&1; then
            echo "   API: http://$PUBLIC_IP:$PORT"
            echo "   Health: http://$PUBLIC_IP:$PORT/health"
        elif curl -sf http://localhost:8545/health > /dev/null 2>&1; then
            echo "   RPC: http://$PUBLIC_IP:8545"
            echo "   Health: http://$PUBLIC_IP:8545/health"
        fi
        echo ""
        
        log_success "🚀 Your Dinari-blockchain is now running permanently!"
        log_success "🔄 It will automatically restart on crashes and reboots"
        log_info "📜 View logs with: dinari logs"
        
    else
        log_error "❌ Service failed to start. Check logs with: journalctl -u $SERVICE_NAME"
        log_info "You can also try: dinari status"
        exit 1
    fi
}

# Run the deployment
main

echo ""
echo -e "${GREEN}=== Deployment completed successfully! ===${NC}"
echo -e "${BLUE}Your blockchain will keep running even after you close this session.${NC}"
#!/bin/bash
# DinariBlockchain Migration Entrypoint Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check required environment variables
check_env() {
    log "Checking environment variables..."
    
    required_vars=(
        "DATABASE_URL"
        "LEVELDB_PATH"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    success "Environment variables validated"
}

# Test database connection
test_db_connection() {
    log "Testing PostgreSQL connection..."
    
    if psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
        success "PostgreSQL connection successful"
    else
        error "Failed to connect to PostgreSQL database"
        exit 1
    fi
}

# Create database schema
create_schema() {
    log "Creating database schema..."
    
    if psql "$DATABASE_URL" -f /migration/database/001_initial_schema.sql; then
        success "Database schema created successfully"
    else
        error "Failed to create database schema"
        exit 1
    fi
}

# Backup existing data
backup_data() {
    if [[ "$BACKUP_BEFORE_MIGRATION" == "true" ]]; then
        log "Creating backup of existing PostgreSQL data..."
        
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_file="/migration/backup/postgres_backup_${timestamp}.sql"
        
        if pg_dump "$DATABASE_URL" > "$backup_file"; then
            success "Database backup created: $backup_file"
        else
            warning "Failed to create database backup, continuing anyway..."
        fi
    fi
}

# Run LevelDB to PostgreSQL migration
run_migration() {
    log "Starting LevelDB to PostgreSQL migration..."
    
    cd /migration
    
    if python database/migrate_from_leveldb.py \
        --leveldb-path "$LEVELDB_PATH" \
        --postgres-url "$DATABASE_URL" \
        --batch-size "${BATCH_SIZE:-1000}" \
        --mode "${MIGRATION_MODE:-full}"; then
        success "Migration completed successfully"
    else
        error "Migration failed"
        exit 1
    fi
}

# Verify migration integrity
verify_migration() {
    if [[ "$VERIFY_MIGRATION" == "true" ]]; then
        log "Verifying migration integrity..."
        
        if python database/verify_migration.py \
            --leveldb-path "$LEVELDB_PATH" \
            --postgres-url "$DATABASE_URL"; then
            success "Migration verification passed"
        else
            error "Migration verification failed"
            exit 1
        fi
    fi
}

# Create completion flag
create_completion_flag() {
    log "Creating migration completion flag..."
    echo "Migration completed at $(date)" > /migration/logs/migration_complete.flag
    success "Migration process completed successfully"
}

# Main migration process
main() {
    log "=== DinariBlockchain Database Migration Starting ==="
    
    # Create logs directory
    mkdir -p /migration/logs
    
    # Run migration steps
    check_env
    test_db_connection
    backup_data
    create_schema
    run_migration
    verify_migration
    create_completion_flag
    
    success "=== DinariBlockchain Database Migration Completed ==="
    
    # Keep container running for debugging if needed
    if [[ "$KEEP_ALIVE" == "true" ]]; then
        log "Keeping container alive for debugging..."
        tail -f /dev/null
    fi
}

# Handle different commands
case "${1:-migrate}" in
    "migrate")
        main
        ;;
    "schema-only")
        export MIGRATION_MODE="schema"
        main
        ;;
    "verify-only")
        check_env
        test_db_connection
        verify_migration
        ;;
    "backup-only")
        check_env
        test_db_connection
        backup_data
        ;;
    "shell")
        log "Starting interactive shell..."
        exec /bin/bash
        ;;
    *)
        error "Unknown command: $1"
        echo "Available commands: migrate, schema-only, verify-only, backup-only, shell"
        exit 1
        ;;
esac
# DinariBlockchain Oracle Cloud Variables
# LevelDB-Only Deployment Configuration

# ============================================================================
# ORACLE CLOUD AUTHENTICATION
# ============================================================================

variable "tenancy_ocid" {
  description = "OCID of the tenancy"
  type        = string
}

variable "user_ocid" {
  description = "OCID of the user"
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint of the API key"
  type        = string
}

variable "private_key_path" {
  description = "Path to the private key file"
  type        = string
  default     = "~/.oci/oci_api_key.pem"
}

variable "region" {
  description = "OCI region"
  type        = string
  default     = "us-ashburn-1"
}

variable "compartment_id" {
  description = "OCID of the compartment"
  type        = string
}

# ============================================================================
# DEPLOYMENT CONFIGURATION
# ============================================================================

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "dinari-blockchain"
}

variable "admin_ip_cidr" {
  description = "CIDR block for admin SSH access"
  type        = string
  default     = "0.0.0.0/0"
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

# ============================================================================
# DINARI BLOCKCHAIN CONFIGURATION
# ============================================================================

variable "dinari_docker_image" {
  description = "Docker image for DinariBlockchain nodes"
  type        = string
  default     = "dinari/blockchain:latest"
}

variable "blockchain_network_id" {
  description = "Blockchain network identifier"
  type        = string
  default     = "dinari-mainnet"
}

variable "consensus_algorithm" {
  description = "Consensus algorithm to use"
  type        = string
  default     = "proof_of_authority"
  validation {
    condition     = contains(["proof_of_authority", "proof_of_stake"], var.consensus_algorithm)
    error_message = "Consensus algorithm must be proof_of_authority or proof_of_stake."
  }
}

variable "block_time_seconds" {
  description = "Target block time in seconds"
  type        = number
  default     = 15
}

variable "gas_limit" {
  description = "Block gas limit"
  type        = number
  default     = 10000000
}

# ============================================================================
# VALIDATOR NODE CONFIGURATION
# ============================================================================

variable "validator_count" {
  description = "Number of validator nodes to deploy"
  type        = number
  default     = 3
  validation {
    condition     = var.validator_count >= 3 && var.validator_count <= 21
    error_message = "Validator count must be between 3 and 21."
  }
}

variable "validator_instance_shape" {
  description = "OCI instance shape for validator nodes"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "validator_ocpus" {
  description = "Number of OCPUs for validator instances"
  type        = number
  default     = 2
}

variable "validator_memory_gbs" {
  description = "Memory in GBs for validator instances"
  type        = number
  default     = 8
}

variable "validator_boot_volume_size_gb" {
  description = "Boot volume size in GB for validator nodes"
  type        = number
  default     = 50
}

# ============================================================================
# RPC NODE CONFIGURATION
# ============================================================================

variable "rpc_count" {
  description = "Number of RPC/API nodes to deploy"
  type        = number
  default     = 2
  validation {
    condition     = var.rpc_count >= 1 && var.rpc_count <= 10
    error_message = "RPC count must be between 1 and 10."
  }
}

variable "rpc_instance_shape" {
  description = "OCI instance shape for RPC nodes"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "rpc_ocpus" {
  description = "Number of OCPUs for RPC instances"
  type        = number
  default     = 2
}

variable "rpc_memory_gbs" {
  description = "Memory in GBs for RPC instances"
  type        = number
  default     = 8
}

variable "rpc_boot_volume_size_gb" {
  description = "Boot volume size in GB for RPC nodes"
  type        = number
  default     = 50
}

# ============================================================================
# LEVELDB STORAGE CONFIGURATION
# ============================================================================

variable "blockchain_data_volume_size_gb" {
  description = "Size of LevelDB data volume in GB"
  type        = number
  default     = 100
  validation {
    condition     = var.blockchain_data_volume_size_gb >= 50 && var.blockchain_data_volume_size_gb <= 32768
    error_message = "Blockchain data volume size must be between 50GB and 32TB."
  }
}

variable "leveldb_backup_enabled" {
  description = "Enable automatic LevelDB backups to object storage"
  type        = bool
  default     = true
}

variable "leveldb_backup_interval_hours" {
  description = "Interval between LevelDB backups in hours"
  type        = number
  default     = 24
}

variable "leveldb_backup_retention_days" {
  description = "Number of days to retain LevelDB backups"
  type        = number
  default     = 30
}

variable "leveldb_compression" {
  description = "Enable LevelDB compression"
  type        = bool
  default     = true
}

variable "leveldb_cache_size_mb" {
  description = "LevelDB cache size in MB"
  type        = number
  default     = 512
}

# ============================================================================
# NETWORKING CONFIGURATION
# ============================================================================

variable "vcn_cidr_block" {
  description = "CIDR block for the VCN"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr_block" {
  description = "CIDR block for the blockchain subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "p2p_port_range_start" {
  description = "Starting port for P2P communication"
  type        = number
  default     = 8333
}

variable "api_port" {
  description = "Port for API communication"
  type        = number
  default     = 5000
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in VCN"
  type        = bool
  default     = true
}

# ============================================================================
# LOAD BALANCER CONFIGURATION
# ============================================================================

variable "load_balancer_shape" {
  description = "Shape for the load balancer"
  type        = string
  default     = "flexible"
}

variable "load_balancer_bandwidth_mbps" {
  description = "Maximum bandwidth for load balancer in Mbps"
  type        = number
  default     = 100
}

variable "health_check_interval_seconds" {
  description = "Health check interval in seconds"
  type        = number
  default     = 30
}

variable "health_check_timeout_seconds" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 5
}

variable "health_check_retries" {
  description = "Number of health check retries"
  type        = number
  default     = 3
}

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

variable "enable_ssh_access" {
  description = "Enable SSH access to instances"
  type        = bool
  default     = true
}

variable "ssh_port" {
  description = "SSH port number"
  type        = number
  default     = 22
}

variable "enable_api_rate_limiting" {
  description = "Enable API rate limiting"
  type        = bool
  default     = true
}

variable "api_rate_limit_requests_per_minute" {
  description = "API rate limit requests per minute"
  type        = number
  default     = 1000
}

variable "enable_ddos_protection" {
  description = "Enable DDoS protection"
  type        = bool
  default     = true
}

# ============================================================================
# MONITORING AND ALERTING
# ============================================================================

variable "enable_monitoring" {
  description = "Enable monitoring and alerting"
  type        = bool
  default     = true
}

variable "cpu_alarm_threshold" {
  description = "CPU utilization threshold for alarms (percentage)"
  type        = number
  default     = 80
}

variable "memory_alarm_threshold" {
  description = "Memory utilization threshold for alarms (percentage)"
  type        = number
  default     = 85
}

variable "disk_alarm_threshold" {
  description = "Disk utilization threshold for alarms (percentage)"
  type        = number
  default     = 90
}

variable "notification_topic_id" {
  description = "OCID of notification topic for alarms"
  type        = string
  default     = ""
}

# ============================================================================
# BACKUP AND DISASTER RECOVERY
# ============================================================================

variable "backup_storage_tier" {
  description = "Storage tier for backups"
  type        = string
  default     = "Standard"
  validation {
    condition     = contains(["Standard", "InfrequentAccess", "Archive"], var.backup_storage_tier)
    error_message = "Backup storage tier must be Standard, InfrequentAccess, or Archive."
  }
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup replication"
  type        = bool
  default     = false
}

variable "backup_encryption_enabled" {
  description = "Enable backup encryption"
  type        = bool
  default     = true
}

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

variable "boot_volume_size_gb" {
  description = "Default boot volume size in GB"
  type        = number
  default     = 50
}

variable "boot_volume_vpus_per_gb" {
  description = "Volume performance units per GB for boot volumes"
  type        = number
  default     = 10
}

variable "data_volume_vpus_per_gb" {
  description = "Volume performance units per GB for data volumes"
  type        = number
  default     = 20
}

variable "enable_high_performance_storage" {
  description = "Enable high performance storage for LevelDB"
  type        = bool
  default     = true
}

# ============================================================================
# COST OPTIMIZATION
# ============================================================================

variable "enable_auto_scaling" {
  description = "Enable auto-scaling for compute instances"
  type        = bool
  default     = false
}

variable "preemptible_instances" {
  description = "Use preemptible instances for cost savings"
  type        = bool
  default     = false
}

variable "scheduled_shutdown_enabled" {
  description = "Enable scheduled shutdown for development environments"
  type        = bool
  default     = false
}

variable "shutdown_schedule_cron" {
  description = "Cron expression for scheduled shutdown"
  type        = string
  default     = "0 22 * * *"  # 10 PM daily
}

# ============================================================================
# ADVANCED CONFIGURATION
# ============================================================================

variable "custom_user_data_script" {
  description = "Custom user data script to run on instance startup"
  type        = string
  default     = ""
}

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain application logs"
  type        = number
  default     = 30
}

# ============================================================================
# BLOCKCHAIN-SPECIFIC FEATURES
# ============================================================================

variable "enable_smart_contracts" {
  description = "Enable smart contract functionality"
  type        = bool
  default     = true
}

variable "enable_afrocoin_stablecoin" {
  description = "Enable Afrocoin (AFC) stablecoin contract"
  type        = bool
  default     = true
}

variable "genesis_allocation" {
  description = "Genesis token allocation configuration"
  type = object({
    treasury_allocation    = number
    development_allocation = number
    community_allocation   = number
    validator_allocation   = number
    reserve_allocation     = number
  })
  default = {
    treasury_allocation    = 30000000
    development_allocation = 20000000
    community_allocation   = 15000000
    validator_allocation   = 25000000
    reserve_allocation     = 10000000
  }
}

variable "native_token_config" {
  description = "Native DINARI token configuration"
  type = object({
    name          = string
    symbol        = string
    total_supply  = number
    decimals      = number
  })
  default = {
    name         = "Dinari"
    symbol       = "DINARI"
    total_supply = 100000000
    decimals     = 18
  }
}

variable "stablecoin_config" {
  description = "AFC stablecoin configuration"
  type = object({
    name            = string
    symbol          = string
    total_supply    = number
    decimals        = number
    collateral_ratio = number
  })
  default = {
    name             = "Afrocoin"
    symbol           = "AFC"
    total_supply     = 200000000
    decimals         = 18
    collateral_ratio = 150
  }
}

# ============================================================================
# VALIDATION RULES
# ============================================================================

locals {
  # Validate that validator count is odd for better consensus
  validator_count_is_odd = var.validator_count % 2 == 1

  # Calculate total allocation
  total_genesis_allocation = (
    var.genesis_allocation.treasury_allocation +
    var.genesis_allocation.development_allocation +
    var.genesis_allocation.community_allocation +
    var.genesis_allocation.validator_allocation +
    var.genesis_allocation.reserve_allocation
  )

  # Validate total allocation equals total supply
  allocation_matches_supply = local.total_genesis_allocation == var.native_token_config.total_supply
}

# Validation checks
check "validator_count_odd" {
  assert {
    condition     = local.validator_count_is_odd
    error_message = "Validator count should be odd for better consensus."
  }
}

check "genesis_allocation_valid" {
  assert {
    condition     = local.allocation_matches_supply
    error_message = "Total genesis allocation (${local.total_genesis_allocation}) must equal total supply (${var.native_token_config.total_supply})."
  }
}
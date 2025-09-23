# DinariBlockchain Oracle Cloud Outputs
# LevelDB-Only Deployment Information

# ============================================================================
# NETWORK OUTPUTS
# ============================================================================

output "vcn_id" {
  description = "OCID of the Virtual Cloud Network"
  value       = oci_core_vcn.dinari_vcn.id
}

output "vcn_cidr_block" {
  description = "CIDR block of the VCN"
  value       = oci_core_vcn.dinari_vcn.cidr_blocks[0]
}

output "subnet_id" {
  description = "OCID of the blockchain subnet"
  value       = oci_core_subnet.dinari_subnet.id
}

output "internet_gateway_id" {
  description = "OCID of the internet gateway"
  value       = oci_core_internet_gateway.dinari_igw.id
}

# ============================================================================
# VALIDATOR NODE OUTPUTS
# ============================================================================

output "validator_instance_ids" {
  description = "OCIDs of validator instances"
  value       = oci_core_instance.dinari_validator[*].id
}

output "validator_public_ips" {
  description = "Public IP addresses of validator nodes"
  value       = oci_core_instance.dinari_validator[*].public_ip
}

output "validator_private_ips" {
  description = "Private IP addresses of validator nodes"
  value       = oci_core_instance.dinari_validator[*].private_ip
}

output "validator_node_info" {
  description = "Complete validator node information"
  value = {
    for i in range(var.validator_count) : "validator-${i + 1}" => {
      instance_id  = oci_core_instance.dinari_validator[i].id
      public_ip    = oci_core_instance.dinari_validator[i].public_ip
      private_ip   = oci_core_instance.dinari_validator[i].private_ip
      display_name = oci_core_instance.dinari_validator[i].display_name
      shape        = oci_core_instance.dinari_validator[i].shape
      p2p_port     = 8333 + i
      api_port     = 5000
      ssh_command  = "ssh ubuntu@${oci_core_instance.dinari_validator[i].public_ip}"
      api_url      = "http://${oci_core_instance.dinari_validator[i].public_ip}:5000"
      health_url   = "http://${oci_core_instance.dinari_validator[i].public_ip}:5000/health"
    }
  }
}

# ============================================================================
# RPC NODE OUTPUTS
# ============================================================================

output "rpc_instance_ids" {
  description = "OCIDs of RPC instances"
  value       = oci_core_instance.dinari_rpc[*].id
}

output "rpc_public_ips" {
  description = "Public IP addresses of RPC nodes"
  value       = oci_core_instance.dinari_rpc[*].public_ip
}

output "rpc_private_ips" {
  description = "Private IP addresses of RPC nodes"
  value       = oci_core_instance.dinari_rpc[*].private_ip
}

output "rpc_node_info" {
  description = "Complete RPC node information"
  value = {
    for i in range(var.rpc_count) : "rpc-${i + 1}" => {
      instance_id  = oci_core_instance.dinari_rpc[i].id
      public_ip    = oci_core_instance.dinari_rpc[i].public_ip
      private_ip   = oci_core_instance.dinari_rpc[i].private_ip
      display_name = oci_core_instance.dinari_rpc[i].display_name
      shape        = oci_core_instance.dinari_rpc[i].shape
      p2p_port     = 8333 + i + 10
      api_port     = 5000
      ssh_command  = "ssh ubuntu@${oci_core_instance.dinari_rpc[i].public_ip}"
      api_url      = "http://${oci_core_instance.dinari_rpc[i].public_ip}:5000"
      health_url   = "http://${oci_core_instance.dinari_rpc[i].public_ip}:5000/health"
      rpc_url      = "http://${oci_core_instance.dinari_rpc[i].public_ip}:5000/rpc"
    }
  }
}

# ============================================================================
# LOAD BALANCER OUTPUTS
# ============================================================================

output "load_balancer_id" {
  description = "OCID of the load balancer"
  value       = oci_load_balancer_load_balancer.dinari_lb.id
}

output "load_balancer_ip" {
  description = "Public IP address of the load balancer"
  value       = oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address
}

output "load_balancer_url" {
  description = "Public URL of the load balancer"
  value       = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}"
}

output "blockchain_api_endpoints" {
  description = "Main blockchain API endpoints"
  value = {
    load_balancer = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}"
    health_check  = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/health"
    rpc_endpoint  = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/rpc"
    api_docs      = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/api"
    blockchain_info = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/api/blockchain/info"
  }
}

# ============================================================================
# LEVELDB STORAGE OUTPUTS
# ============================================================================

output "validator_storage_volume_ids" {
  description = "OCIDs of validator storage volumes"
  value       = oci_core_volume.validator_storage[*].id
}

output "rpc_storage_volume_ids" {
  description = "OCIDs of RPC storage volumes"
  value       = oci_core_volume.rpc_storage[*].id
}

output "storage_configuration" {
  description = "LevelDB storage configuration"
  value = {
    validator_volumes = {
      for i in range(var.validator_count) : "validator-${i + 1}" => {
        volume_id   = oci_core_volume.validator_storage[i].id
        size_gb     = oci_core_volume.validator_storage[i].size_in_gbs
        mount_path  = "/app/dinari_data"
        backup_enabled = var.leveldb_backup_enabled
      }
    }
    rpc_volumes = {
      for i in range(var.rpc_count) : "rpc-${i + 1}" => {
        volume_id   = oci_core_volume.rpc_storage[i].id
        size_gb     = oci_core_volume.rpc_storage[i].size_in_gbs
        mount_path  = "/app/dinari_data"
        backup_enabled = var.leveldb_backup_enabled
      }
    }
    total_storage_gb = (var.validator_count + var.rpc_count) * var.blockchain_data_volume_size_gb
  }
}

# ============================================================================
# BACKUP OUTPUTS
# ============================================================================

output "backup_bucket_name" {
  description = "Name of the backup storage bucket"
  value       = oci_objectstorage_bucket.dinari_backups.name
}

output "backup_bucket_namespace" {
  description = "Namespace of the backup storage bucket"
  value       = oci_objectstorage_bucket.dinari_backups.namespace
}

output "backup_configuration" {
  description = "Backup configuration details"
  value = {
    bucket_name       = oci_objectstorage_bucket.dinari_backups.name
    namespace         = oci_objectstorage_bucket.dinari_backups.namespace
    storage_tier      = var.backup_storage_tier
    enabled           = var.leveldb_backup_enabled
    interval_hours    = var.leveldb_backup_interval_hours
    retention_days    = var.leveldb_backup_retention_days
    encryption_enabled = var.backup_encryption_enabled
  }
}

# ============================================================================
# BLOCKCHAIN CONFIGURATION OUTPUTS
# ============================================================================

output "blockchain_configuration" {
  description = "Complete blockchain configuration"
  value = {
    network_id        = var.blockchain_network_id
    consensus         = var.consensus_algorithm
    block_time        = var.block_time_seconds
    gas_limit         = var.gas_limit
    validator_count   = var.validator_count
    rpc_count         = var.rpc_count
    
    native_token = {
      name         = var.native_token_config.name
      symbol       = var.native_token_config.symbol
      total_supply = var.native_token_config.total_supply
      decimals     = var.native_token_config.decimals
    }
    
    stablecoin = {
      name             = var.stablecoin_config.name
      symbol           = var.stablecoin_config.symbol
      total_supply     = var.stablecoin_config.total_supply
      decimals         = var.stablecoin_config.decimals
      collateral_ratio = var.stablecoin_config.collateral_ratio
    }
    
    genesis_allocation = var.genesis_allocation
    
    storage = {
      type             = "LevelDB"
      cache_size_mb    = var.leveldb_cache_size_mb
      compression      = var.leveldb_compression
      volume_size_gb   = var.blockchain_data_volume_size_gb
    }
  }
}

# ============================================================================
# SECURITY OUTPUTS
# ============================================================================

output "security_configuration" {
  description = "Security configuration details"
  value = {
    ssh_access_enabled    = var.enable_ssh_access
    ssh_port             = var.ssh_port
    api_rate_limiting    = var.enable_api_rate_limiting
    ddos_protection      = var.enable_ddos_protection
    admin_access_cidr    = var.admin_ip_cidr
    
    allowed_ports = [
      {
        port        = 80
        protocol    = "HTTP"
        description = "HTTP API access"
      },
      {
        port        = 443
        protocol    = "HTTPS"
        description = "HTTPS API access"
      },
      {
        port        = 5000
        protocol    = "HTTP"
        description = "Direct API access"
      },
      {
        port_range  = "${var.p2p_port_range_start}-${var.p2p_port_range_start + var.validator_count + var.rpc_count}"
        protocol    = "TCP"
        description = "P2P blockchain communication"
      }
    ]
  }
}

# ============================================================================
# DEPLOYMENT SUMMARY
# ============================================================================

output "deployment_summary" {
  description = "Complete deployment summary"
  value = {
    environment     = var.environment
    region          = var.region
    project_name    = var.project_name
    deployment_time = timestamp()
    
    infrastructure = {
      validator_nodes = var.validator_count
      rpc_nodes      = var.rpc_count
      total_instances = var.validator_count + var.rpc_count
      storage_type    = "LevelDB"
      total_storage_gb = (var.validator_count + var.rpc_count) * var.blockchain_data_volume_size_gb
    }
    
    network = {
      vcn_cidr        = var.vcn_cidr_block
      subnet_cidr     = var.subnet_cidr_block
      load_balancer   = "enabled"
      public_access   = "enabled"
    }
    
    costs_estimate = {
      validator_instances_monthly = "${var.validator_count * 50}" # Rough estimate
      rpc_instances_monthly      = "${var.rpc_count * 50}"        # Rough estimate
      storage_monthly            = "${(var.validator_count + var.rpc_count) * var.blockchain_data_volume_size_gb * 0.1}"
      load_balancer_monthly      = "25"
      total_estimated_monthly    = "${(var.validator_count + var.rpc_count) * 50 + (var.validator_count + var.rpc_count) * var.blockchain_data_volume_size_gb * 0.1 + 25}"
      currency                   = "USD"
      note                       = "Estimates based on Oracle Cloud pricing, actual costs may vary"
    }
  }
}

# ============================================================================
# QUICK ACCESS COMMANDS
# ============================================================================

output "quick_access_commands" {
  description = "Useful commands for managing the deployment"
  value = {
    check_blockchain_health = "curl -s ${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/health | jq"
    get_blockchain_info     = "curl -s ${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/api/blockchain/info | jq"
    test_rpc_endpoint      = "curl -X POST -H 'Content-Type: application/json' -d '{\"method\":\"dinari_getBlockchainInfo\",\"params\":[],\"id\":1}' ${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/rpc | jq"
    
    ssh_to_validator_1 = "ssh ubuntu@${oci_core_instance.dinari_validator[0].public_ip}"
    ssh_to_rpc_1      = "ssh ubuntu@${oci_core_instance.dinari_rpc[0].public_ip}"
    
    view_validator_logs = "ssh ubuntu@${oci_core_instance.dinari_validator[0].public_ip} 'sudo docker logs dinari-validator'"
    view_rpc_logs      = "ssh ubuntu@${oci_core_instance.dinari_rpc[0].public_ip} 'sudo docker logs dinari-rpc'"
    
    backup_leveldb = "ssh ubuntu@${oci_core_instance.dinari_validator[0].public_ip} 'sudo /opt/dinari/scripts/backup_leveldb.sh'"
  }
}

# ============================================================================
# CONNECTION STRINGS
# ============================================================================

output "connection_info" {
  description = "Connection information for external services"
  value = {
    json_rpc_endpoint = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/rpc"
    rest_api_endpoint = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/api"
    websocket_endpoint = "ws://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/ws"
    
    # For wallet integration
    network_config = {
      network_name     = "DinariBlockchain ${title(var.environment)}"
      chain_id         = var.blockchain_network_id
      rpc_url          = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/rpc"
      block_explorer   = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}"
      native_currency = {
        name     = var.native_token_config.name
        symbol   = var.native_token_config.symbol
        decimals = var.native_token_config.decimals
      }
    }
  }
}

# ============================================================================
# MONITORING URLS
# ============================================================================

output "monitoring_urls" {
  description = "Monitoring and health check URLs"
  value = {
    load_balancer_health = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/health"
    blockchain_stats     = "http://${oci_load_balancer_load_balancer.dinari_lb.ip_addresses[0].ip_address}/api/stats"
    
    validator_nodes = {
      for i in range(var.validator_count) : "validator-${i + 1}" => {
        health = "http://${oci_core_instance.dinari_validator[i].public_ip}:5000/health"
        stats  = "http://${oci_core_instance.dinari_validator[i].public_ip}:5000/api/stats"
      }
    }
    
    rpc_nodes = {
      for i in range(var.rpc_count) : "rpc-${i + 1}" => {
        health = "http://${oci_core_instance.dinari_rpc[i].public_ip}:5000/health"
        stats  = "http://${oci_core_instance.dinari_rpc[i].public_ip}:5000/api/stats"
      }
    }
  }
}
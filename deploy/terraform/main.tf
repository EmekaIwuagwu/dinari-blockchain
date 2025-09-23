# DinariBlockchain Oracle Cloud Infrastructure
# LevelDB-Only Deployment (No PostgreSQL migration)

terraform {
  required_version = ">= 1.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

provider "oci" {
  region              = var.region
  tenancy_ocid        = var.tenancy_ocid
  user_ocid           = var.user_ocid
  fingerprint         = var.fingerprint
  private_key_path    = var.private_key_path
}

# Data sources
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_id
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                   = "VM.Standard.E4.Flex"
  sort_by                 = "TIMECREATED"
  sort_order              = "DESC"
}

# ============================================================================
# NETWORKING (SIMPLIFIED)
# ============================================================================

resource "oci_core_vcn" "dinari_vcn" {
  compartment_id = var.compartment_id
  cidr_blocks    = ["10.0.0.0/16"]
  display_name   = "dinari-blockchain-vcn"
  dns_label      = "dinarivcn"

  freeform_tags = {
    Environment = var.environment
    Project     = "dinari-blockchain"
    Storage     = "leveldb-only"
  }
}

resource "oci_core_internet_gateway" "dinari_igw" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.dinari_vcn.id
  display_name   = "dinari-internet-gateway"
  enabled        = true
}

resource "oci_core_route_table" "dinari_rt" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.dinari_vcn.id
  display_name   = "dinari-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.dinari_igw.id
  }
}

# Single subnet for blockchain nodes
resource "oci_core_subnet" "dinari_subnet" {
  compartment_id      = var.compartment_id
  vcn_id              = oci_core_vcn.dinari_vcn.id
  cidr_block          = "10.0.1.0/24"
  display_name        = "dinari-blockchain-subnet"
  dns_label           = "dinarichain"
  route_table_id      = oci_core_route_table.dinari_rt.id
  security_list_ids   = [oci_core_security_list.dinari_sl.id]

  freeform_tags = {
    Environment = var.environment
    Project     = "dinari-blockchain"
  }
}

# ============================================================================
# SECURITY (SIMPLIFIED)
# ============================================================================

resource "oci_core_security_list" "dinari_sl" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.dinari_vcn.id
  display_name   = "dinari-security-list"

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }

  # HTTP/HTTPS API access
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 5000
      max = 5000
    }
  }

  # P2P blockchain communication
  ingress_security_rules {
    protocol = "6"
    source   = "10.0.0.0/16"
    tcp_options {
      min = 8333
      max = 8340
    }
  }

  # SSH access
  ingress_security_rules {
    protocol = "6"
    source   = var.admin_ip_cidr
    tcp_options {
      min = 22
      max = 22
    }
  }
}

# ============================================================================
# VALIDATOR NODES (LevelDB-Only)
# ============================================================================

resource "oci_core_instance" "dinari_validator" {
  count = var.validator_count

  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[count.index % length(data.oci_identity_availability_domains.ads.availability_domains)].name
  display_name        = "dinari-validator-${count.index + 1}"
  shape               = var.validator_instance_shape

  shape_config {
    ocpus         = var.validator_ocpus
    memory_in_gbs = var.validator_memory_gbs
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.dinari_subnet.id
    display_name     = "dinari-validator-${count.index + 1}-vnic"
    assign_public_ip = true
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.ubuntu.images[0].id
    boot_volume_size_in_gbs = var.boot_volume_size_gb
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/../scripts/leveldb_node_userdata.sh", {
      node_id      = "validator-${count.index + 1}"
      node_type    = "validator"
      docker_image = var.dinari_docker_image
      environment  = var.environment
      p2p_port     = 8333 + count.index
      api_port     = 5000
      mining_enabled = true
      validator_enabled = true
    }))
  }

  freeform_tags = {
    Environment = var.environment
    Project     = "dinari-blockchain"
    Role        = "validator"
    Storage     = "leveldb"
    NodeID      = "validator-${count.index + 1}"
  }
}

# ============================================================================
# RPC NODES (LevelDB-Only)
# ============================================================================

resource "oci_core_instance" "dinari_rpc" {
  count = var.rpc_count

  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[count.index % length(data.oci_identity_availability_domains.ads.availability_domains)].name
  display_name        = "dinari-rpc-${count.index + 1}"
  shape               = var.rpc_instance_shape

  shape_config {
    ocpus         = var.rpc_ocpus
    memory_in_gbs = var.rpc_memory_gbs
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.dinari_subnet.id
    display_name     = "dinari-rpc-${count.index + 1}-vnic"
    assign_public_ip = true
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.ubuntu.images[0].id
    boot_volume_size_in_gbs = var.boot_volume_size_gb
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/../scripts/leveldb_node_userdata.sh", {
      node_id      = "rpc-${count.index + 1}"
      node_type    = "rpc"
      docker_image = var.dinari_docker_image
      environment  = var.environment
      p2p_port     = 8333 + count.index + 10
      api_port     = 5000
      mining_enabled = false
      validator_enabled = false
    }))
  }

  freeform_tags = {
    Environment = var.environment
    Project     = "dinari-blockchain"
    Role        = "rpc"
    Storage     = "leveldb"
    NodeID      = "rpc-${count.index + 1}"
  }
}

# ============================================================================
# LOAD BALANCER (SIMPLIFIED)
# ============================================================================

resource "oci_load_balancer_load_balancer" "dinari_lb" {
  compartment_id = var.compartment_id
  display_name   = "dinari-blockchain-lb"
  shape          = "flexible"
  subnet_ids     = [oci_core_subnet.dinari_subnet.id]

  shape_details {
    maximum_bandwidth_in_mbps = 100
    minimum_bandwidth_in_mbps = 10
  }

  freeform_tags = {
    Environment = var.environment
    Project     = "dinari-blockchain"
    Storage     = "leveldb-only"
  }
}

# Backend set for RPC nodes
resource "oci_load_balancer_backend_set" "dinari_rpc_backend_set" {
  load_balancer_id = oci_load_balancer_load_balancer.dinari_lb.id
  name             = "dinari-rpc-backend-set"
  policy           = "ROUND_ROBIN"

  health_checker {
    protocol            = "HTTP"
    url_path            = "/health"
    port                = 5000
    return_code         = 200
    timeout_in_millis   = 5000
    interval_ms         = 30000
    retries             = 3
  }
}

# Add RPC nodes to backend set
resource "oci_load_balancer_backend" "dinari_rpc_backend" {
  count = var.rpc_count

  load_balancer_id = oci_load_balancer_load_balancer.dinari_lb.id
  backendset_name  = oci_load_balancer_backend_set.dinari_rpc_backend_set.name
  ip_address       = oci_core_instance.dinari_rpc[count.index].private_ip
  port             = 5000
  backup           = false
  drain            = false
  offline          = false
  weight           = 1
}

# HTTP listener
resource "oci_load_balancer_listener" "dinari_http_listener" {
  load_balancer_id         = oci_load_balancer_load_balancer.dinari_lb.id
  name                     = "dinari-http-listener"
  default_backend_set_name = oci_load_balancer_backend_set.dinari_rpc_backend_set.name
  port                     = 80
  protocol                 = "HTTP"
}

# ============================================================================
# BLOCK STORAGE FOR LEVELDB DATA
# ============================================================================

resource "oci_core_volume" "validator_storage" {
  count = var.validator_count

  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[count.index % length(data.oci_identity_availability_domains.ads.availability_domains)].name
  display_name        = "dinari-validator-${count.index + 1}-storage"
  size_in_gbs         = var.blockchain_data_volume_size_gb

  freeform_tags = {
    Environment = var.environment
    Project     = "dinari-blockchain"
    NodeID      = "validator-${count.index + 1}"
    Purpose     = "leveldb-data"
  }
}

resource "oci_core_volume_attachment" "validator_storage_attachment" {
  count = var.validator_count

  attachment_type = "iscsi"
  instance_id     = oci_core_instance.dinari_validator[count.index].id
  volume_id       = oci_core_volume.validator_storage[count.index].id
}

resource "oci_core_volume" "rpc_storage" {
  count = var.rpc_count

  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[count.index % length(data.oci_identity_availability_domains.ads.availability_domains)].name
  display_name        = "dinari-rpc-${count.index + 1}-storage"
  size_in_gbs         = var.blockchain_data_volume_size_gb

  freeform_tags = {
    Environment = var.environment
    Project     = "dinari-blockchain"
    NodeID      = "rpc-${count.index + 1}"
    Purpose     = "leveldb-data"
  }
}

resource "oci_core_volume_attachment" "rpc_storage_attachment" {
  count = var.rpc_count

  attachment_type = "iscsi"
  instance_id     = oci_core_instance.dinari_rpc[count.index].id
  volume_id       = oci_core_volume.rpc_storage[count.index].id
}

# ============================================================================
# OBJECT STORAGE FOR BACKUPS
# ============================================================================

resource "oci_objectstorage_bucket" "dinari_backups" {
  compartment_id = var.compartment_id
  name           = "dinari-leveldb-backups-${var.environment}"
  namespace      = data.oci_objectstorage_namespace.user_namespace.namespace

  access_type           = "NoPublicAccess"
  storage_tier          = "Standard"
  object_events_enabled = true
  versioning            = "Enabled"

  freeform_tags = {
    Environment = var.environment
    Project     = "dinari-blockchain"
    Purpose     = "leveldb-backups"
  }
}

data "oci_objectstorage_namespace" "user_namespace" {
  compartment_id = var.compartment_id
}
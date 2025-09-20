#!/usr/bin/env python3
"""
DinariBlockchain - API Server
app.py - Complete Flask API server with DT address system and genesis compatibility for Render.com deployment
"""

import os
import json
import time
import hashlib
import time
import logging
import secrets
from flask import Flask, request, jsonify
from flask_cors import CORS
from decimal import Decimal
import threading

# Import DinariBlockchain components
from Dinari import (
    DinariBlockchain,
    DinariNode,
    Transaction,
    ContractManager,
    create_wallet,
    setup_logging
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for web frontend

# Global variables
blockchain_node = None
blockchain = None
contract_manager = None

# Configuration
PORT = int(os.getenv('PORT', 5000))  # Render.com sets PORT
NODE_ID = os.getenv('NODE_ID', 'api_node')

# Find available P2P port to avoid conflicts
def find_available_port(start_port: int = 8333) -> int:
    """Find an available port starting from start_port"""
    import socket
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return start_port  # Fallback to original port

def handle_dinari_getDualTokenStatus(params):
    """Get dual token (DINARI + AFC) status and canonical prices"""
    try:
        # Get current blockchain info
        blockchain_info = blockchain.get_blockchain_info()
        
        # Get AFC supply from Afrocoin contract
        try:
            afc_result = blockchain.call_contract("afrocoin_stablecoin", {
                "function": "get_total_afc_supply",
                "args": {}
            }, "system", Decimal("0"))
            afc_supply = str(afc_result.get("total_afc_supply", "200000000"))
        except:
            afc_supply = "200000000"  # Default 200M AFC
        
        # Get current timestamp
        from datetime import datetime
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        # Build dual token status response
        dual_status = {
            "dinari": {
                "symbol": "DINARI",
                "name": "Dinari Native Token",
                "price_usd": "1.00",  # Canonical price authority
                "supply_circulating": str(blockchain_info.get("total_dinari_supply", "0")),
                "supply_max": "100000000",  # 100M max supply
                "decimals": 18,
                "contract_type": "native",
                "oracle_status": "active",
                "use_case": "gas_fees_governance"
            },
            "afc": {
                "symbol": "AFC", 
                "name": "Afrocoin Stablecoin",
                "price_usd": "1.00",  # Canonical price authority
                "supply_circulating": afc_supply,
                "supply_max": "200000000",  # 200M max supply
                "decimals": 18,
                "contract_type": "stablecoin",
                "contract_address": "afrocoin_stablecoin",
                "oracle_status": "active",
                "peg_mechanism": "dinari_collateral",
                "use_case": "payments_transfers"
            },
            "price_authority": {
                "canonical_source": "dinari_protocol",
                "dinari_price_feed": "1.00",
                "afc_price_feed": "1.00", 
                "external_markets_follow": True,
                "oracle_update_frequency": "60_seconds"
            },
            "network_stats": {
                "block_height": blockchain_info.get("height", 0),
                "total_validators": blockchain_info.get("validators", 0),
                "total_contracts": blockchain_info.get("contracts", 0),
                "total_transactions": blockchain_info.get("total_transactions", 0),
                "mining_active": blockchain_info.get("mining_active", False)
            },
            "dual_oracle_active": True,
            "protocol_version": "1.0.0",
            "last_updated": current_time
        }
        
        return {"success": True, "data": dual_status}
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get dual token status: {str(e)}"}

P2P_PORT = find_available_port(int(os.getenv('P2P_PORT', 8333)))

class DinariAddress:
    """
    DinariBlockchain Address System with Genesis Compatibility
    
    Supports both:
    - New format: DT + 40 hex chars (42 total)
    - Legacy genesis: DT + variable length (for backward compatibility)
    
    Address Format: DT + 40 character hex string
    Example: DT1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2
    
    - DT: Dinari Token prefix (2 chars)
    - 40 chars: SHA-256 hash truncated to 160 bits (40 hex chars)
    - Case sensitive
    - Total length: 42 characters
    """
    
    PREFIX = "DT"
    ADDRESS_LENGTH = 42  # DT + 40 hex chars
    HASH_LENGTH = 40     # 160 bits = 40 hex chars
    
    # Known genesis addresses that bypass strict validation
    GENESIS_ADDRESSES = {
    "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",  # 30M DINARI - Main Treasury
    "DT1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx",   # 25M DINARI - Validators Fund  
    "DT1cqgze3fqpw0dqh9j8l2dqqyr89c0q5c2jdpg8x",   # 20M DINARI - Development Fund
    "DT1xz2f8l8lh8vqw3r6n4s2k7j9p1d5g8h3m6c4v7",   # 15M DINARI - Community Treasury
    "DT1a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5"    # 10M DINARI - Reserve Fund
    }
    
    @classmethod
    def generate_address(cls, seed: str = None) -> str:
        """
        Generate a new DinariBlockchain address (42 chars)
        
        Args:
            seed: Optional seed string. If None, uses secure random
            
        Returns:
            DT-prefixed address string
        """
        if seed is None:
            # Generate secure random seed
            seed = secrets.token_hex(32)
        
        # Create SHA-256 hash
        hash_obj = hashlib.sha256(seed.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # Take first 40 characters (160 bits)
        address_hash = hash_hex[:cls.HASH_LENGTH]
        
        # Combine prefix with hash
        address = f"{cls.PREFIX}{address_hash}"
        
        return address
    
    @classmethod
    def generate_from_wallet_name(cls, wallet_name: str) -> str:
        """
        Generate deterministic address from wallet name
        
        Args:
            wallet_name: Name of the wallet
            
        Returns:
            DT-prefixed address
        """
        return cls.generate_address(wallet_name)
    
    @classmethod
    def generate_multisig_address(cls, public_keys: list, threshold: int) -> str:
        """
        Generate a multisig address from multiple public keys
        
        Args:
            public_keys: List of public key strings
            threshold: Required signatures threshold
            
        Returns:
            DT-prefixed multisig address
        """
        # Sort public keys for deterministic address generation
        sorted_keys = sorted(public_keys)
        multisig_data = f"multisig_{threshold}_{','.join(sorted_keys)}"
        return cls.generate_address(multisig_data)
    
    @classmethod
    def is_valid_address(cls, address: str) -> bool:
        """
        Validate a Dinari address format with genesis compatibility
        
        Args:
            address: Address string to validate
            
        Returns:
            bool: True if valid DT address (new format or known genesis)
        """
        if not isinstance(address, str):
            return False
        
        if not address.startswith(cls.PREFIX):
            return False
        
        # Allow known genesis addresses (legacy format)
        if address in cls.GENESIS_ADDRESSES:
            return True
        
        # Strict validation for new addresses
        if len(address) != cls.ADDRESS_LENGTH:
            return False
        
        # Check if the hash part is valid hex
        hash_part = address[len(cls.PREFIX):]
        try:
            int(hash_part, 16)
            return len(hash_part) == cls.HASH_LENGTH
        except ValueError:
            return False
    
    @classmethod
    def is_genesis_address(cls, address: str) -> bool:
        """Check if address is a known genesis address"""
        return address in cls.GENESIS_ADDRESSES
    
    @classmethod
    def get_genesis_addresses(cls) -> set:
        """Get all known genesis addresses"""
        return cls.GENESIS_ADDRESSES.copy()
    
    @classmethod
    def get_address_info(cls, address: str) -> dict:
        """Get detailed information about an address"""
        return {
            "address": address,
            "is_valid": cls.is_valid_address(address),
            "is_genesis": cls.is_genesis_address(address),
            "length": len(address),
            "prefix": address[:2] if len(address) >= 2 else "",
            "hash_part": address[2:] if len(address) > 2 else "",
            "expected_format": "DT + 40 hex characters",
            "expected_length": cls.ADDRESS_LENGTH
        }

def initialize_blockchain():
    """Initialize blockchain and node"""
    global blockchain_node, blockchain, contract_manager
    
    try:
        logger.info(f"🚀 Initializing DinariBlockchain API Server")
        logger.info(f"   Node ID: {NODE_ID}")
        logger.info(f"   P2P Port: {P2P_PORT}")
        logger.info(f"   API Port: {PORT}")
        logger.info(f"   Address Format: DT-prefixed addresses")
        logger.info(f"   Genesis Compatibility: {len(DinariAddress.GENESIS_ADDRESSES)} known addresses")
        
        # Create blockchain instance first (auto-starts mining and validators)
        blockchain = DinariBlockchain()
        
        # Create contract manager
        contract_manager = ContractManager(blockchain)
        
        # Try to initialize P2P node (but don't fail if port is busy)
        try:
            blockchain_node = DinariNode(
                host="0.0.0.0",
                port=P2P_PORT,
                node_id=NODE_ID
            )
            
            # Set blockchain reference on node
            if hasattr(blockchain_node, 'set_blockchain'):
                blockchain_node.set_blockchain(blockchain)
            
            # Start node in background thread
            def start_node():
                try:
                    if hasattr(blockchain_node, 'start'):
                        blockchain_node.start()
                    logger.info("✅ P2P Node started successfully")
                except Exception as e:
                    logger.warning(f"P2P Node failed to start (non-critical): {e}")
                    logger.info("⚠️  API will work without P2P networking")
            
            # Start node in background
            node_thread = threading.Thread(target=start_node, daemon=True)
            node_thread.start()
            
        except Exception as e:
            logger.warning(f"P2P Node initialization failed (non-critical): {e}")
            logger.info("⚠️  Continuing with API-only mode")
            blockchain_node = None
        
        logger.info("✅ Blockchain initialized successfully")
        logger.info(f"⚡ Automatic mining: {'ACTIVE' if blockchain.mining_active else 'INACTIVE'}")
        logger.info(f"👥 Validators: {len(blockchain.validators)}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize blockchain: {e}")
        raise

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check for monitoring"""
    try:
        status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'node_id': NODE_ID,
            'api_port': PORT,
            'p2p_port': P2P_PORT,
            'address_format': 'DT-prefixed',
            'genesis_compatibility': True,
            'known_genesis_addresses': len(DinariAddress.GENESIS_ADDRESSES)
        }
        
        if blockchain:
            try:
                chain_info = blockchain.get_chain_info()
                status.update({
                    'blockchain': {
                        'height': chain_info.get('height', 0),
                        'transactions': chain_info.get('total_transactions', 0),
                        'pending': chain_info.get('pending_transactions', 0),
                        'contracts': chain_info.get('contracts', 0),
                        'mining_active': chain_info.get('mining_active', False)
                    }
                })
            except Exception as e:
                logger.warning(f"Could not get blockchain info: {e}")
        
        if blockchain_node:
            try:
                if hasattr(blockchain_node, 'get_network_info'):
                    node_info = blockchain_node.get_network_info()
                    status.update({
                        'network': {
                            'connected_peers': node_info.get('connected_peers', 0),
                            'is_validator': node_info.get('is_validator', False)
                        }
                    })
                else:
                    status.update({
                        'network': {
                            'connected_peers': 0,
                            'is_validator': False,
                            'status': 'P2P disabled'
                        }
                    })
            except Exception as e:
                logger.warning(f"Could not get network info: {e}")
                status.update({
                    'network': {
                        'connected_peers': 0,
                        'is_validator': False,
                        'status': 'P2P error'
                    }
                })
        else:
            status.update({
                'network': {
                    'connected_peers': 0,
                    'is_validator': False,
                    'status': 'P2P not initialized'
                }
            })
        
        return jsonify(status), 200
        
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Blockchain info endpoints
@app.route('/api/blockchain/info', methods=['GET'])
def blockchain_info():
    """Get blockchain information"""
    try:
        if not blockchain:
            return jsonify({'error': 'Blockchain not initialized'}), 503
        
        chain_info = blockchain.get_chain_info()
        
        # Get AFC supply from Afrocoin contract
        afc_supply = "0"
        try:
            afrocoin_contract = blockchain.get_afrocoin_contract()
            if afrocoin_contract:
                afc_supply = afrocoin_contract.state.variables.get('total_supply', '0')
        except:
            afc_supply = "200000000"  # Default to 200M if can't read from contract
        
        info = {
            'network_id': 'dinari_mainnet',
            'native_token': 'DINARI',
            'stablecoin': 'AFC (Afrocoin)',
            'address_format': 'DT-prefixed addresses',
            'genesis_compatibility': True,
            'known_genesis_addresses': len(DinariAddress.GENESIS_ADDRESSES),
            'chain_height': chain_info.get('height', 0),
            'total_transactions': chain_info.get('total_transactions', 0),
            'pending_transactions': chain_info.get('pending_transactions', 0),
            'validators': chain_info.get('validators', 0),
            'contracts': chain_info.get('contracts', 0),
            'total_dinari_supply': chain_info.get('total_dinari_supply', '0'),
            'total_afc_supply': afc_supply,  # ADD AFC supply
            'mining_active': chain_info.get('mining_active', False),
            'last_block_hash': chain_info.get('last_block_hash', '')[:16] + '...' if chain_info.get('last_block_hash') else 'None'
        }
        
        return jsonify(info), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/blockchain/balance/<address>', methods=['GET'])
def get_balance(address):
    """Get balance for an address"""
    try:
        if not blockchain:
            return jsonify({'error': 'Blockchain not initialized'}), 503
        
        # Validate DT address format (now supports genesis addresses)
        if not DinariAddress.is_valid_address(address):
            return jsonify({'error': 'Invalid DT address format. Address must start with "DT" followed by 40 hex characters.'}), 400
        
        # Get DINARI balance
        dinari_balance = "0"
        afc_balance = "0"
        
        if hasattr(blockchain, 'get_dinari_balance'):
            dinari_balance = str(blockchain.get_dinari_balance(address))
        
        if hasattr(blockchain, 'get_afrocoin_balance'):
            afc_balance = str(blockchain.get_afrocoin_balance(address))
        
        address_info = DinariAddress.get_address_info(address)
        
        return jsonify({
            'address': address,
            'address_format': 'DT-prefixed',
            'is_genesis': address_info['is_genesis'],
            'balances': {
                'DINARI': dinari_balance,
                'AFC': afc_balance
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/blockchain/transaction', methods=['POST'])
def submit_transaction():
    """Submit a new transaction"""
    try:
        if not blockchain:
            return jsonify({'error': 'Blockchain not initialized'}), 503
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['from_address', 'to_address', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Validate DT addresses (now supports genesis addresses)
        if not DinariAddress.is_valid_address(data['from_address']):
            return jsonify({'error': 'Invalid from_address. Must be DT-prefixed address.'}), 400
        
        if not DinariAddress.is_valid_address(data['to_address']):
            return jsonify({'error': 'Invalid to_address. Must be DT-prefixed address.'}), 400
        
        # Create transaction
        tx = Transaction(
            from_address=data['from_address'],
            to_address=data['to_address'],
            amount=Decimal(str(data['amount'])),
            gas_price=Decimal(str(data.get('gas_price', '0.001'))),
            gas_limit=int(data.get('gas_limit', 21000)),
            nonce=int(data.get('nonce', 0)),
            data=data.get('data', '')
        )
        
        # Add transaction to blockchain
        success = blockchain.add_transaction(tx)
        
        if success:
            return jsonify({
                'success': True,
                'transaction_hash': tx.get_hash(),
                'message': 'Transaction submitted successfully',
                'from_genesis': DinariAddress.is_genesis_address(data['from_address']),
                'to_genesis': DinariAddress.is_genesis_address(data['to_address'])
            }), 200
        else:
            return jsonify({'error': 'Failed to submit transaction'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/blockchain/block/<int:block_index>', methods=['GET'])
def get_block(block_index):
    """Get block by index"""
    try:
        if not blockchain:
            return jsonify({'error': 'Blockchain not initialized'}), 503
        
        chain_info = blockchain.get_chain_info()
        if block_index >= chain_info.get('height', 0) or block_index < 0:
            return jsonify({'error': 'Block not found'}), 404
        
        # Try to get block by hash (would need implementation)
        return jsonify({
            'message': 'Block retrieval by index not yet implemented',
            'available_height': chain_info.get('height', 0)
        }), 501
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contracts/deploy', methods=['POST'])
def deploy_contract():
    """Deploy a smart contract"""
    try:
        if not contract_manager:
            return jsonify({'error': 'Contract manager not initialized'}), 503
        
        data = request.get_json()
        
        required_fields = ['contract_id', 'owner']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Validate owner address (now supports genesis addresses)
        if not DinariAddress.is_valid_address(data['owner']):
            return jsonify({'error': 'Invalid owner address. Must be DT-prefixed address.'}), 400
        
        # Deploy contract
        contract = contract_manager.deploy_contract(
            contract_id=data['contract_id'],
            code=data.get('code', 'Default contract code'),
            owner=data['owner'],
            contract_type=data.get('contract_type', 'general'),
            initial_state=data.get('initial_state', {})
        )
        
        return jsonify({
            'success': True,
            'contract_id': data['contract_id'],
            'owner': data['owner'],
            'owner_is_genesis': DinariAddress.is_genesis_address(data['owner']),
            'contract_type': data.get('contract_type', 'general')
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contracts/call', methods=['POST'])
def call_contract():
    """Call smart contract function"""
    try:
        if not contract_manager:
            return jsonify({'error': 'Contract manager not initialized'}), 503
        
        data = request.get_json()
        
        required_fields = ['contract_id', 'function_name', 'caller']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Validate caller address (now supports genesis addresses)
        if not DinariAddress.is_valid_address(data['caller']):
            return jsonify({'error': 'Invalid caller address. Must be DT-prefixed address.'}), 400
        
        function_data = {
            'function': data['function_name'],
            'args': data.get('args', {})
        }
        
        result = contract_manager.execute_contract(
            contract_id=data['contract_id'],
            function_data=function_data,
            caller=data['caller'],
            value=Decimal(str(data.get('value', '0')))
        )
        
        return jsonify({
            'success': result.get('success', False),
            'result': result.get('result', ''),
            'gas_used': result.get('gas_used', 0),
            'error': result.get('error', None),
            'caller_is_genesis': DinariAddress.is_genesis_address(data['caller'])
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contracts/afrocoin', methods=['GET'])
def afrocoin_info():
    """Get Afrocoin contract information"""
    try:
        if not contract_manager:
            return jsonify({'error': 'Contract manager not initialized'}), 503
        
        afrocoin_contract = contract_manager.get_afrocoin_contract()
        
        if afrocoin_contract:
            return jsonify({
                'contract_id': 'afrocoin_stablecoin',
                'name': 'Afrocoin',
                'symbol': 'AFC',
                'type': 'stablecoin',
                'status': 'deployed',
                'backed_by': 'DINARI',
                'owner': afrocoin_contract.owner,
                'owner_is_genesis': DinariAddress.is_genesis_address(afrocoin_contract.owner),
                'address_format': 'DT-prefixed'
            })
        else:
            return jsonify({
                'contract_id': 'afrocoin_stablecoin',
                'status': 'not_found'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/genesis/addresses', methods=['GET'])
def get_genesis_addresses():
    """Get all known genesis addresses and their info"""
    try:
        genesis_addresses = []
        
        for address in DinariAddress.get_genesis_addresses():
            address_info = DinariAddress.get_address_info(address)
            
            # Get balance if blockchain is available
            dinari_balance = "0"
            afc_balance = "0"
            
            if blockchain:
                try:
                    dinari_balance = str(blockchain.get_dinari_balance(address))
                    afc_balance = str(blockchain.get_afrocoin_balance(address))
                except:
                    pass
            
            genesis_addresses.append({
                **address_info,
                'balances': {
                    'DINARI': dinari_balance,
                    'AFC': afc_balance
                }
            })
        
        return jsonify({
            'total_genesis_addresses': len(genesis_addresses),
            'genesis_addresses': genesis_addresses
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/genesis/fund/<address>', methods=['POST'])
def fund_from_genesis(address):
    """Fund an address from genesis addresses (for testing)"""
    try:
        if not blockchain:
            return jsonify({'error': 'Blockchain not initialized'}), 503
        
        # Validate recipient address
        if not DinariAddress.is_valid_address(address):
            return jsonify({'error': 'Invalid recipient address format'}), 400
        
        data = request.get_json() if request.get_json() else {}
        amount = Decimal(str(data.get('amount', '100')))  # Default 100 DINARI
        
        # Find a genesis address with sufficient balance
        funded = False
        for genesis_addr in DinariAddress.get_genesis_addresses():
            try:
                balance = blockchain.get_dinari_balance(genesis_addr)
                if balance >= amount + Decimal('0.001'):  # Amount + gas fee
                    # Create transaction from genesis to recipient
                    tx = Transaction(
                        from_address=genesis_addr,
                        to_address=address,
                        amount=amount,
                        gas_price=Decimal('0.001'),
                        gas_limit=21000,
                        nonce=0,
                        data=f"Genesis funding to {address}"
                    )
                    
                    success = blockchain.add_transaction(tx)
                    if success:
                        funded = True
                        return jsonify({
                            'success': True,
                            'transaction_hash': tx.get_hash(),
                            'from_genesis': genesis_addr,
                            'to_address': address,
                            'amount': str(amount),
                            'message': f'Funded {amount} DINARI from genesis'
                        }), 200
            except Exception as e:
                logger.warning(f"Failed to fund from {genesis_addr}: {e}")
                continue
        
        if not funded:
            return jsonify({
                'success': False,
                'error': 'No genesis address has sufficient balance'
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/rpc', methods=['POST'])
def rpc_handler():
    """Complete JSON-RPC 2.0 endpoint for DinariBlockchain"""
    try:
        data = request.get_json()
        
        if not data or 'method' not in data:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {"code": -32600, "message": "Invalid Request"},
                "id": data.get('id') if data else None
            }), 400
        
        method = data['method']
        params = data.get('params', [])
        rpc_id = data.get('id', 1)
        
        # Handle RPC methods
        try:
            if method == 'dinari_ping':
                result = "pong"
                
            elif method == 'dinari_getBlockchainInfo':
                if blockchain:
                    chain_info = blockchain.get_chain_info()
                    
                    # Get AFC supply from Afrocoin contract
                    afc_supply = "0"
                    try:
                        afrocoin_contract = blockchain.get_afrocoin_contract()
                        if afrocoin_contract:
                            afc_supply = afrocoin_contract.state.variables.get('total_supply', '0')
                    except:
                        afc_supply = "200000000"  # Default to 200M
                    
                    result = {
                        "network_id": "dinari_mainnet",
                        "native_token": "DINARI", 
                        "stablecoin": "AFC",
                        "address_format": "DT-prefixed",
                        "genesis_compatibility": True,
                        "known_genesis_addresses": len(DinariAddress.GENESIS_ADDRESSES),
                        "height": chain_info.get('height', 0),
                        "total_transactions": chain_info.get('total_transactions', 0),
                        "pending_transactions": chain_info.get('pending_transactions', 0),
                        "validators": chain_info.get('validators', 0),
                        "contracts": chain_info.get('contracts', 0),
                        "total_dinari_supply": chain_info.get('total_dinari_supply', '0'),
                        "total_afc_supply": afc_supply,  # ADD AFC supply
                        "mining_active": chain_info.get('mining_active', False)
                    }
                else:
                    result = {"error": "Blockchain not initialized"}
                    
            elif method == 'dinari_getBalance':
                if not params:
                    raise ValueError("Address parameter required")
                address = params[0]
                
                # Validate DT address format (now supports genesis addresses)
                if not DinariAddress.is_valid_address(address):
                    raise ValueError("Invalid DT address format")
                
                if blockchain:
                    dinari_bal = str(blockchain.get_dinari_balance(address))
                    afc_bal = str(blockchain.get_afrocoin_balance(address))
                    result = {
                        "address": address,
                        "is_genesis": DinariAddress.is_genesis_address(address),
                        "DINARI": dinari_bal, 
                        "AFC": afc_bal
                    }
                else:
                    result = {"DINARI": "0", "AFC": "0"}
                    
            elif method == 'dinari_createWallet':
                wallet_name = params[0] if params else f"wallet_{int(time.time())}"
                wallet = create_wallet()
                
                # Generate DT-prefixed address
                dt_address = DinariAddress.generate_from_wallet_name(wallet_name)
                
                result = {
                    "success": True,
                    "wallet_name": wallet_name,
                    "message": "Wallet created successfully",
                    "address": dt_address,
                    "address_format": "DT-prefixed",
                    "is_genesis": False
                }
                
            elif method == 'dinari_generateAddress':
                # New method to generate DT address
                seed = params[0] if params else None
                dt_address = DinariAddress.generate_address(seed)
                
                result = {
                    "address": dt_address,
                    "address_format": "DT-prefixed",
                    "length": len(dt_address),
                    "is_genesis": False
                }
                
            elif method == 'dinari_validateAddress':
                if not params:
                    raise ValueError("Address parameter required")
                address = params[0]
                
                address_info = DinariAddress.get_address_info(address)
                result = address_info
                
            elif method == 'dinari_getGenesisAddresses':
                # New method to get all genesis addresses
                genesis_addresses = []
                for addr in DinariAddress.get_genesis_addresses():
                    addr_info = DinariAddress.get_address_info(addr)
                    if blockchain:
                        try:
                            dinari_balance = str(blockchain.get_dinari_balance(addr))
                            afc_balance = str(blockchain.get_afrocoin_balance(addr))
                            addr_info['balances'] = {
                                'DINARI': dinari_balance,
                                'AFC': afc_balance
                            }
                        except:
                            addr_info['balances'] = {'DINARI': '0', 'AFC': '0'}
                    genesis_addresses.append(addr_info)
                
                result = {
                    "total_genesis_addresses": len(genesis_addresses),
                    "genesis_addresses": genesis_addresses
                }
                
            elif method == 'dinari_fundFromGenesis':
                # New method to fund from genesis (for testing)
                if len(params) < 2:
                    raise ValueError("Required: recipient_address, amount")
                
                recipient = params[0]
                amount = Decimal(str(params[1]))
                
                if not DinariAddress.is_valid_address(recipient):
                    raise ValueError("Invalid recipient address format")
                
                # Find genesis address with sufficient balance
                for genesis_addr in DinariAddress.get_genesis_addresses():
                    try:
                        balance = blockchain.get_dinari_balance(genesis_addr)
                        if balance >= amount + Decimal('0.001'):
                            tx = Transaction(
                                from_address=genesis_addr,
                                to_address=recipient,
                                amount=amount,
                                gas_price=Decimal('0.001'),
                                gas_limit=21000,
                                nonce=0,
                                data="Genesis funding"
                            )
                            
                            success = blockchain.add_transaction(tx)
                            if success:
                                result = {
                                    "success": True,
                                    "transaction_hash": tx.get_hash(),
                                    "from_genesis": genesis_addr,
                                    "to_address": recipient,
                                    "amount": str(amount)
                                }
                                break
                    except:
                        continue
                else:
                    result = {"success": False, "error": "No genesis address has sufficient balance"}
                
            elif method == 'dinari_sendTransaction':
                if len(params) < 3:
                    raise ValueError("Required: from_address, to_address, amount")
                
                from_addr = params[0]
                to_addr = params[1] 
                amount = params[2]
                gas_price = params[3] if len(params) > 3 else "0.001"
                data_field = params[4] if len(params) > 4 else ""
                
                # Validate DT addresses (now supports genesis addresses)
                if not DinariAddress.is_valid_address(from_addr):
                    raise ValueError("Invalid from_address format")
                if not DinariAddress.is_valid_address(to_addr):
                    raise ValueError("Invalid to_address format")
                
                if blockchain:
                    tx = Transaction(
                        from_address=from_addr,
                        to_address=to_addr,
                        amount=Decimal(str(amount)),
                        gas_price=Decimal(str(gas_price)),
                        gas_limit=21000,
                        nonce=0,
                        data=data_field
                    )
                    
                    success = blockchain.add_transaction(tx)
                    if success:
                        result = {
                            "success": True,
                            "transaction_hash": tx.get_hash(),
                            "from": from_addr,
                            "to": to_addr,
                            "amount": amount,
                            "gas_price": gas_price,
                            "from_genesis": DinariAddress.is_genesis_address(from_addr),
                            "to_genesis": DinariAddress.is_genesis_address(to_addr)
                        }
                    else:
                        result = {"success": False, "error": "Transaction failed"}
                else:
                    result = {"success": False, "error": "Blockchain not available"}
                    
            elif method == 'dinari_callContract':
                if len(params) < 3:
                    raise ValueError("Required: contract_id, function_name, caller")
                    
                contract_id = params[0]
                function_name = params[1]
                caller = params[2]
                args = params[3] if len(params) > 3 else {}
                
                # Validate caller address (now supports genesis addresses)
                if not DinariAddress.is_valid_address(caller):
                    raise ValueError("Invalid caller address format")
                
                if contract_manager:
                    function_data = {
                        'function': function_name,
                        'args': args
                    }
                    
                    contract_result = contract_manager.execute_contract(
                        contract_id=contract_id,
                        function_data=function_data,
                        caller=caller,
                        value=Decimal('0')
                    )
                    
                    result = {
                        "success": contract_result.get('success', False),
                        "result": contract_result.get('result', ''),
                        "gas_used": contract_result.get('gas_used', 0),
                        "error": contract_result.get('error', None),
                        "caller_is_genesis": DinariAddress.is_genesis_address(caller)
                    }
                else:
                    result = {"success": False, "error": "Contract manager not available"}
                    
            elif method == 'dinari_getNetworkInfo':
                if blockchain_node and hasattr(blockchain_node, 'get_network_info'):
                    network_info = blockchain_node.get_network_info()
                    result = {
                        "node_id": NODE_ID,
                        "connected_peers": network_info.get('connected_peers', 0),
                        "is_validator": network_info.get('is_validator', False),
                        "p2p_port": P2P_PORT,
                        "api_port": PORT,
                        "address_format": "DT-prefixed",
                        "genesis_compatibility": True,
                        "p2p_status": "active"
                    }
                else:
                    result = {
                        "node_id": NODE_ID,
                        "connected_peers": 0,
                        "is_validator": False,
                        "p2p_port": P2P_PORT,
                        "api_port": PORT,
                        "address_format": "DT-prefixed",
                        "genesis_compatibility": True,
                        "p2p_status": "disabled"
                    }
                    
            elif method == 'dinari_getValidators':
                if blockchain:
                    result = blockchain.validators if hasattr(blockchain, 'validators') else []
                else:
                    result = []
            
            elif method == "dinari_getDualTokenStatus":
                    result = handle_dinari_getDualTokenStatus(params)
                    if result["success"]:
                        return jsonify({
                            "jsonrpc": "2.0",
                            "result": result["data"],
                            "id": request_id
                        })
                    else:
                        return jsonify({
                            "jsonrpc": "2.0", 
                            "error": {"code": -32603, "message": result["error"]},
                            "id": request_id
                        })
                    
            elif method == 'dinari_mineBlock':
                validator = params[0] if params else "default_validator"
                if blockchain:
                    block = blockchain.create_block(validator)
                    if block:
                        result = {
                            "success": True,
                            "block_index": block.index,
                            "block_hash": block.get_hash(),
                            "validator": validator,
                            "transactions": len(block.transactions),
                            "timestamp": block.timestamp
                        }
                    else:
                        result = {"success": False, "error": "No pending transactions"}
                else:
                    result = {"success": False, "error": "Blockchain not available"}
                    
            elif method == 'dinari_getVersion':
                result = {
                    "blockchain_version": "1.0.0",
                    "api_version": "1.0.0", 
                    "rpc_version": "2.0",
                    "network": "dinari_mainnet",
                    "native_token": "DINARI",
                    "stablecoin": "AFC",
                    "address_format": "DT-prefixed addresses",
                    "address_length": 42,
                    "genesis_compatibility": True
                }
            
            elif method == 'dinari_getAfcSupply':
            # New method to get AFC supply specifically
                afc_supply = "0"
                try:
                    if blockchain:
                        afrocoin_contract = blockchain.get_afrocoin_contract()
                        if afrocoin_contract:
                            afc_supply = afrocoin_contract.state.variables.get('total_supply', '0')
                        else:
                            afc_supply = "200000000"  # Default
                    result = {
                        "total_afc_supply": afc_supply,
                        "symbol": "AFC",
                        "name": "Afrocoin",
                        "contract_id": "afrocoin_stablecoin",
                        "backed_by": "DINARI"
                    }
                except Exception as e:
                    result = {"error": str(e)}
                
            elif method == 'dinari_getContractInfo':
                if not params:
                    raise ValueError("Contract ID required")
                contract_id = params[0]
                
                if contract_manager:
                    contract = contract_manager.get_contract(contract_id)
                    if contract:
                        result = {
                            "contract_id": contract.contract_id,
                            "owner": contract.owner,
                            "owner_is_genesis": DinariAddress.is_genesis_address(contract.owner),
                            "contract_type": contract.contract_type,
                            "created_at": contract.created_at,
                            "is_active": contract.state.is_active,
                            "balance": str(contract.state.balance)
                        }
                    else:
                        result = {"error": f"Contract {contract_id} not found"}
                else:
                    result = {"error": "Contract manager not available"}
                    
            elif method == 'dinari_deployContract':
                if len(params) < 2:
                    raise ValueError("Required: contract_code, deployer")
                    
                contract_code = params[0]
                deployer = params[1]
                init_args = params[2] if len(params) > 2 else {}
                
                # Validate deployer address (now supports genesis addresses)
                if not DinariAddress.is_valid_address(deployer):
                    raise ValueError("Invalid deployer address format")
                
                contract_id = f"contract_{int(time.time())}"
                
                if contract_manager:
                    contract = contract_manager.deploy_contract(
                        contract_id=contract_id,
                        code=contract_code,
                        owner=deployer,
                        contract_type="general",
                        initial_state=init_args
                    )
                    
                    result = {
                        "success": True,
                        "contract_id": contract_id,
                        "deployer": deployer,
                        "deployer_is_genesis": DinariAddress.is_genesis_address(deployer),
                        "contract_address": contract_id
                    }
                else:
                    result = {"success": False, "error": "Contract manager not available"}
                    
            else:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": "Method not found"},
                    "id": rpc_id
                }), 404
            
            return jsonify({
                "jsonrpc": "2.0",
                "result": result,
                "id": rpc_id
            })
            
        except Exception as method_error:
            return jsonify({
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(method_error)},
                "id": rpc_id
            }), 500
        
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "error": {"code": -32000, "message": str(e)},
            "id": data.get('id') if 'data' in locals() else None
        }), 500

@app.route('/api/wallet/create', methods=['POST'])
def create_new_wallet():
    """Create a new wallet"""
    try:
        data = request.get_json() if request.get_json() else {}
        wallet_name = data.get('name', f'wallet_{int(time.time())}')
        
        wallet = create_wallet()
        
        # Generate DT-prefixed address
        dt_address = DinariAddress.generate_from_wallet_name(wallet_name)
        
        return jsonify({
            'success': True,
            'wallet_name': wallet_name,
            'address': dt_address,
            'address_format': 'DT-prefixed',
            'is_genesis': False,
            'message': 'Wallet created successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/address/generate', methods=['POST'])
def generate_address():
    """Generate a new DT-prefixed address"""
    try:
        data = request.get_json() if request.get_json() else {}
        seed = data.get('seed', None)
        address_type = data.get('type', 'standard')  # standard, multisig
        
        if address_type == 'multisig':
            public_keys = data.get('public_keys', [])
            threshold = data.get('threshold', 1)
            
            if not public_keys or len(public_keys) < threshold:
                return jsonify({'error': 'Invalid multisig parameters'}), 400
            
            dt_address = DinariAddress.generate_multisig_address(public_keys, threshold)
            
            return jsonify({
                'address': dt_address,
                'address_format': 'DT-prefixed',
                'address_type': 'multisig',
                'threshold': threshold,
                'public_keys_count': len(public_keys),
                'length': len(dt_address),
                'prefix': DinariAddress.PREFIX
            }), 200
        else:
            dt_address = DinariAddress.generate_address(seed)
            
            return jsonify({
                'address': dt_address,
                'address_format': 'DT-prefixed',
                'address_type': 'standard',
                'length': len(dt_address),
                'prefix': DinariAddress.PREFIX
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/address/validate/<address>', methods=['GET'])
def validate_address(address):
    """Validate a DT-prefixed address"""
    try:
        address_info = DinariAddress.get_address_info(address)
        
        return jsonify(address_info), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/address/info/<address>', methods=['GET'])
def get_address_info(address):
    """Get comprehensive address information"""
    try:
        address_info = DinariAddress.get_address_info(address)
        
        # Add balance information if blockchain is available
        if blockchain and address_info['is_valid']:
            try:
                dinari_balance = str(blockchain.get_dinari_balance(address))
                afc_balance = str(blockchain.get_afrocoin_balance(address))
                address_info['balances'] = {
                    'DINARI': dinari_balance,
                    'AFC': afc_balance
                }
            except:
                address_info['balances'] = {'DINARI': '0', 'AFC': '0'}
        
        return jsonify(address_info), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/peers', methods=['GET'])
def get_peers():
    """Get connected peers"""
    try:
        if not blockchain_node:
            return jsonify({
                'connected_peers': 0,
                'peers_info': [],
                'message': 'P2P networking not available'
            }), 200
        
        if hasattr(blockchain_node, 'get_network_info'):
            network_info = blockchain_node.get_network_info()
            return jsonify({
                'connected_peers': network_info.get('connected_peers', 0),
                'peers_info': network_info.get('peers_info', [])
            }), 200
        else:
            return jsonify({
                'connected_peers': 0,
                'peers_info': [],
                'message': 'Network info not available'
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get comprehensive blockchain statistics"""
    try:
        stats = {
            'timestamp': time.time(),
            'node_id': NODE_ID,
            'address_system': {
                'format': 'DT-prefixed',
                'prefix': 'DT',
                'length': 42,
                'hash_length': 40,
                'genesis_compatibility': True,
                'known_genesis_addresses': len(DinariAddress.GENESIS_ADDRESSES)
            }
        }
        
        if blockchain:
            try:
                chain_info = blockchain.get_chain_info()
                stats['blockchain'] = chain_info
            except Exception as e:
                stats['blockchain'] = {'error': str(e)}
        
        if blockchain_node:
            try:
                if hasattr(blockchain_node, 'get_network_info'):
                    network_info = blockchain_node.get_network_info()
                    stats['network'] = network_info
                else:
                    stats['network'] = {'message': 'Network info not available'}
            except Exception as e:
                stats['network'] = {'error': str(e)}
        else:
            stats['network'] = {'message': 'P2P networking not initialized'}
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Updated web interface with current DinariBlockchain information
@app.route('/', methods=['GET'])
def index():
    """Updated web interface with latest blockchain data"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>DinariBlockchain API - Live Network</title>
        <style>
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                margin: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
            }
            .container { 
                max-width: 1200px;
                margin: 0 auto;
                background: white; 
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .header h1 { margin: 0; font-size: 2.5rem; font-weight: 700; }
            .subtitle { margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9; }
            .content { padding: 30px; }
            .status { 
                padding: 20px; 
                margin: 20px 0; 
                border-radius: 10px; 
                font-weight: 600;
            }
            .healthy { 
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                color: white;
            }
            .unhealthy { 
                background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                color: white;
            }
            .live-stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }
            .stat-value {
                font-size: 1.8rem;
                font-weight: 700;
                margin: 5px 0;
            }
            .stat-label {
                font-size: 0.9rem;
                opacity: 0.8;
            }
            .endpoint { 
                background: #2d3748;
                color: #e2e8f0;
                padding: 12px 15px;
                margin: 8px 0;
                border-radius: 6px;
                font-family: 'Courier New', monospace;
                font-size: 0.9rem;
            }
            .section {
                margin: 30px 0;
                background: #f8f9ff;
                padding: 25px;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }
            .section h2 {
                color: #2a5298;
                margin: 0 0 20px 0;
                font-size: 1.4rem;
            }
            .token-info {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 20px 0;
            }
            .token-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 10px;
                text-align: center;
            }
            .token-card h3 { margin: 0 0 15px 0; font-size: 1.4rem; }
            .token-price {
                font-size: 2.2rem;
                font-weight: 700;
                margin: 10px 0;
                color: #32cd32;
            }
            .genesis-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 15px;
                margin: 15px 0;
            }
            .genesis-address {
                background: white;
                border: 2px solid #667eea;
                padding: 15px;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .genesis-address:hover {
                background: #667eea;
                color: white;
                transform: translateY(-2px);
            }
            .method { color: #68d391; font-weight: bold; }
            .endpoint-path { color: #63b3ed; }
            .price-authority {
                background: linear-gradient(135deg, #ffa726 0%, #fb8c00 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
            }
            .refresh-btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: 600;
                margin: 10px;
            }
            .refresh-btn:hover { background: #5a6fd8; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌍 DinariBlockchain API</h1>
                <p class="subtitle">Native DINARI token blockchain with Afrocoin stablecoin support</p>
                <p class="subtitle">🏦 Canonical Price Authority for African Blockchain Economics</p>
            </div>
            
            <div class="content">
                <h2>📊 Live Network Status</h2>
                <div id="status" class="status">Loading live data...</div>
                <button class="refresh-btn" onclick="loadStatus()">🔄 Refresh Status</button>
                
                <div class="live-stats" id="live-stats">
                    <div class="stat-card">
                        <div class="stat-value" id="block-height">-</div>
                        <div class="stat-label">Block Height</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="dinari-supply">-</div>
                        <div class="stat-label">DINARI Supply</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="afc-supply">-</div>
                        <div class="stat-label">AFC Supply</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="validator-count">-</div>
                        <div class="stat-label">Active Validators</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="contract-count">-</div>
                        <div class="stat-label">Smart Contracts</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="tx-count">-</div>
                        <div class="stat-label">Total Transactions</div>
                    </div>
                </div>

                <div class="price-authority">
                    <h3>💰 Canonical Price Authority</h3>
                    <p><strong>DINARI:</strong> $1.00 USD | <strong>AFC:</strong> $1.00 USD</p>
                    <p>DinariBlockchain Protocol sets official prices - External markets follow our oracle</p>
                </div>

                <div class="token-info">
                    <div class="token-card">
                        <h3>🪙 DINARI Token</h3>
                        <div class="token-price">$1.00</div>
                        <p>Native gas token</p>
                        <p>Current: <span id="dinari-circ">1.93M</span> circulating</p>
                        <p>Max: 100M total supply</p>
                    </div>
                    <div class="token-card">
                        <h3>🏦 AFC Stablecoin</h3>
                        <div class="token-price">$1.00</div>
                        <p>USD-pegged stablecoin</p>
                        <p>Current: <span id="afc-circ">200M</span> supply</p>
                        <p>Backed by DINARI collateral</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📍 Address Format</h2>
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 4px;">
                        <strong>DT-prefixed addresses:</strong> DT + 40 hex characters (42 total length)<br>
                        <strong>Example:</strong> DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu<br>
                        <strong>Validation:</strong> Must start with "DT" followed by exactly 40 hexadecimal characters
                    </div>
                </div>
                
                <div class="section">
                    <h2>🔑 Genesis Addresses (Click to Check Balance)</h2>
                    <div class="genesis-grid">
                        <div class="genesis-address" onclick="checkAddress('DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu')">
                            <div style="font-weight: 600;">Main Treasury (30M DINARI)</div>
                            <div style="font-size: 0.85rem; color: #666;">DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu</div>
                        </div>
                        <div class="genesis-address" onclick="checkAddress('DT1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx')">
                            <div style="font-weight: 600;">Validators Fund (25M DINARI)</div>
                            <div style="font-size: 0.85rem; color: #666;">DT1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx</div>
                        </div>
                        <div class="genesis-address" onclick="checkAddress('DT1cqgze3fqpw0dqh9j8l2dqqyr89c0q5c2jdpg8x')">
                            <div style="font-weight: 600;">Development Fund (20M DINARI)</div>
                            <div style="font-size: 0.85rem; color: #666;">DT1cqgze3fqpw0dqh9j8l2dqqyr89c0q5c2jdpg8x</div>
                        </div>
                        <div class="genesis-address" onclick="checkAddress('DT1xz2f8l8lh8vqw3r6n4s2k7j9p1d5g8h3m6c4v7')">
                            <div style="font-weight: 600;">Community Treasury (15M DINARI)</div>
                            <div style="font-size: 0.85rem; color: #666;">DT1xz2f8l8lh8vqw3r6n4s2k7j9p1d5g8h3m6c4v7</div>
                        </div>
                        <div class="genesis-address" onclick="checkAddress('DT1a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5')">
                            <div style="font-weight: 600;">Reserve Fund (10M DINARI)</div>
                            <div style="font-size: 0.85rem; color: #666;">DT1a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🔗 REST API Endpoints</h2>
                    <div class="endpoint"><span class="method">GET</span> <span class="endpoint-path">/health</span> - Health check</div>
                    <div class="endpoint"><span class="method">GET</span> <span class="endpoint-path">/api/blockchain/info</span> - Blockchain information</div>
                    <div class="endpoint"><span class="method">GET</span> <span class="endpoint-path">/api/blockchain/balance/{address}</span> - Get DINARI & AFC balance</div>
                    <div class="endpoint"><span class="method">POST</span> <span class="endpoint-path">/api/blockchain/transaction</span> - Submit transaction</div>
                    <div class="endpoint"><span class="method">GET</span> <span class="endpoint-path">/api/blockchain/block/{index}</span> - Get block</div>
                    <div class="endpoint"><span class="method">POST</span> <span class="endpoint-path">/api/contracts/deploy</span> - Deploy contract</div>
                    <div class="endpoint"><span class="method">POST</span> <span class="endpoint-path">/api/contracts/call</span> - Call contract</div>
                    <div class="endpoint"><span class="method">GET</span> <span class="endpoint-path">/api/contracts/afrocoin</span> - Afrocoin contract info</div>
                    <div class="endpoint"><span class="method">POST</span> <span class="endpoint-path">/api/wallet/create</span> - Create wallet</div>
                    <div class="endpoint"><span class="method">POST</span> <span class="endpoint-path">/api/address/generate</span> - Generate DT address</div>
                    <div class="endpoint"><span class="method">GET</span> <span class="endpoint-path">/api/address/validate/{address}</span> - Validate DT address</div>
                    <div class="endpoint"><span class="method">GET</span> <span class="endpoint-path">/api/address/info/{address}</span> - Get address info & balance</div>
                    <div class="endpoint"><span class="method">GET</span> <span class="endpoint-path">/api/genesis/addresses</span> - Get all genesis addresses</div>
                    <div class="endpoint"><span class="method">POST</span> <span class="endpoint-path">/api/genesis/fund/{address}</span> - Fund address from genesis</div>
                    <div class="endpoint"><span class="method">GET</span> <span class="endpoint-path">/api/network/peers</span> - Get peers</div>
                    <div class="endpoint"><span class="method">GET</span> <span class="endpoint-path">/api/stats</span> - Get statistics</div>
                    <div class="endpoint"><span class="method">POST</span> <span class="endpoint-path">/rpc</span> - JSON-RPC 2.0 endpoint</div>
                </div>
                
                <div class="section">
                    <h2>🔧 JSON-RPC Methods</h2>
                    <div class="endpoint">dinari_createWallet - Create new wallet with DT address</div>
                    <div class="endpoint">dinari_generateAddress - Generate new DT address</div>
                    <div class="endpoint">dinari_validateAddress - Validate DT address format</div>
                    <div class="endpoint">dinari_getBalance - Get balance for DT address</div>
                    <div class="endpoint">dinari_sendTransaction - Send transaction between DT addresses</div>
                    <div class="endpoint">dinari_getBlockchainInfo - Get blockchain information</div>
                    <div class="endpoint">dinari_getGenesisAddresses - Get all genesis addresses</div>
                    <div class="endpoint">dinari_fundFromGenesis - Fund address from genesis (testing)</div>
                    <div class="endpoint">dinari_callContract - Call smart contract</div>
                    <div class="endpoint">dinari_deployContract - Deploy smart contract</div>
                    <div class="endpoint">dinari_getAfcSupply - Get AFC (Afrocoin) supply information</div>
                    <div class="endpoint">dinari_getCanonicalPrice - Get canonical DINARI price ($1.00)</div>
                    <div class="endpoint">dinari_getAfcPrice - Get canonical AFC price ($1.00)</div>
                    <div class="endpoint">dinari_getDualTokenStatus - Get both token price feeds</div>
                </div>
            </div>
        </div>
        
        <script>
            // Load live blockchain status
            async function loadStatus() {
                try {
                    const [healthResponse, infoResponse] = await Promise.all([
                        fetch('/health'),
                        fetch('/api/blockchain/info')
                    ]);
                    
                    const health = await healthResponse.json();
                    const info = await infoResponse.json();
                    
                    const statusEl = document.getElementById('status');
                    
                    if (health.status === 'healthy') {
                        statusEl.className = 'status healthy';
                        statusEl.innerHTML = `
                            ✅ <strong>Network Healthy</strong><br>
                            Node: ${health.node_id} | API: Port ${health.api_port} | 
                            P2P: ${health.network?.status || 'Active'} | 
                            Mining: ${info.mining_active ? 'Active' : 'Inactive'} | 
                            Address Format: ${health.address_format}
                        `;
                        
                        // Update live stats
                        if (info) {
                            document.getElementById('block-height').textContent = info.height || 0;
                            document.getElementById('dinari-supply').textContent = formatSupply(info.total_dinari_supply || 0);
                            document.getElementById('afc-supply').textContent = '200M'; // AFC total supply
                            document.getElementById('validator-count').textContent = info.validators || 0;
                            document.getElementById('contract-count').textContent = info.contracts || 0;
                            document.getElementById('tx-count').textContent = info.total_transactions || 0;
                            
                            // Update circulating supplies
                            document.getElementById('dinari-circ').textContent = formatSupply(info.total_dinari_supply || 0);
                        }
                    } else {
                        statusEl.className = 'status unhealthy';
                        statusEl.innerHTML = `❌ <strong>Network Error:</strong> ${health.error || 'Unknown error'}`;
                    }
                } catch (error) {
                    document.getElementById('status').innerHTML = `❌ <strong>Connection Error:</strong> ${error.message}`;
                    document.getElementById('status').className = 'status unhealthy';
                }
            }
            
            // Format supply numbers
            function formatSupply(supply) {
                const num = parseFloat(supply);
                if (num >= 1000000) {
                    return (num / 1000000).toFixed(1) + 'M';
                } else if (num >= 1000) {
                    return (num / 1000).toFixed(1) + 'K';
                } else {
                    return num.toLocaleString();
                }
            }
            
            // Check address balance
            async function checkAddress(address) {
                try {
                    const response = await fetch(`/api/address/info/${address}`);
                    const data = await response.json();
                    
                    if (response.ok) {
                        alert(`Address: ${address.substring(0, 20)}...
DINARI Balance: ${parseFloat(data.balances?.DINARI || 0).toLocaleString()}
AFC Balance: ${parseFloat(data.balances?.AFC || 0).toLocaleString()}
Genesis Address: ${data.is_genesis ? 'Yes' : 'No'}`);
                    } else {
                        alert(`Error checking address: ${data.error}`);
                    }
                } catch (error) {
                    alert(`Connection error: ${error.message}`);
                }
            }
            
            // Load status on page load
            loadStatus();
            
            // Auto-refresh every 30 seconds
            setInterval(loadStatus, 30000);
        </script>
    </body>
    </html>
    '''

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        # Initialize blockchain
        initialize_blockchain()
        
        # Start Flask app
        logger.info(f"🚀 Starting DinariBlockchain API server on port {PORT}")
        logger.info(f"📍 Using DT-prefixed address format with genesis compatibility")
        logger.info(f"🔑 Supporting {len(DinariAddress.GENESIS_ADDRESSES)} known genesis addresses")
        app.run(
            host='0.0.0.0',
            port=PORT,
            debug=os.getenv('DEBUG', 'false').lower() == 'true'
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        raise
else:
    # For production deployment (gunicorn)
    try:
        initialize_blockchain()
    except Exception as e:
        logger.error(f"❌ Failed to initialize for production: {e}")
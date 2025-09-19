#!/usr/bin/env python3
"""
DinariBlockchain - API Server
app.py - Fixed Flask API server for Render.com deployment
"""

import os
import json
import time
import hashlib
import time
import logging
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
P2P_PORT = int(os.getenv('P2P_PORT', 8333))

def initialize_blockchain():
    """Initialize blockchain and node"""
    global blockchain_node, blockchain, contract_manager
    
    try:
        logger.info(f"🚀 Initializing DinariBlockchain API Server")
        logger.info(f"   Node ID: {NODE_ID}")
        logger.info(f"   P2P Port: {P2P_PORT}")
        logger.info(f"   API Port: {PORT}")
        
        # Create blockchain instance first
        blockchain = DinariBlockchain()
        
        # Create blockchain node with correct parameters
        blockchain_node = DinariNode(
            host="0.0.0.0",
            port=P2P_PORT,
            node_id=NODE_ID
        )
        
        # Set blockchain reference on node
        if hasattr(blockchain_node, 'set_blockchain'):
            blockchain_node.set_blockchain(blockchain)
        
        # Create contract manager
        contract_manager = ContractManager(blockchain)
        
        # Start node in background thread
        def start_node():
            try:
                if hasattr(blockchain_node, 'start'):
                    blockchain_node.start()
                logger.info("✅ Node started successfully")
            except Exception as e:
                logger.error(f"Failed to start node: {e}")
        
        # Start node in background
        node_thread = threading.Thread(target=start_node, daemon=True)
        node_thread.start()
        
        logger.info("✅ Blockchain initialized successfully")
        
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
            'p2p_port': P2P_PORT
        }
        
        if blockchain:
            try:
                chain_info = blockchain.get_chain_info()
                status.update({
                    'blockchain': {
                        'height': chain_info.get('height', 0),
                        'transactions': chain_info.get('total_transactions', 0),
                        'pending': chain_info.get('pending_transactions', 0),
                        'contracts': chain_info.get('contracts', 0)
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
            except Exception as e:
                logger.warning(f"Could not get network info: {e}")
        
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
        
        info = {
            'network_id': 'dinari_mainnet',
            'native_token': 'DINARI',
            'stablecoin': 'AFC (Afrocoin)',
            'chain_height': chain_info.get('height', 0),
            'total_transactions': chain_info.get('total_transactions', 0),
            'pending_transactions': chain_info.get('pending_transactions', 0),
            'validators': chain_info.get('validators', 0),
            'contracts': chain_info.get('contracts', 0),
            'total_dinari_supply': chain_info.get('total_dinari_supply', '0'),
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
        
        # Get DINARI balance
        dinari_balance = "0"
        afc_balance = "0"
        
        if hasattr(blockchain, 'get_dinari_balance'):
            dinari_balance = str(blockchain.get_dinari_balance(address))
        
        if hasattr(blockchain, 'get_afrocoin_balance'):
            afc_balance = str(blockchain.get_afrocoin_balance(address))
        
        return jsonify({
            'address': address,
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
                'message': 'Transaction submitted successfully'
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
            'error': result.get('error', None)
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
                'owner': afrocoin_contract.owner
            })
        else:
            return jsonify({
                'contract_id': 'afrocoin_stablecoin',
                'status': 'not_found'
            })
            
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
                    result = {
                        "network_id": "dinari_mainnet",
                        "native_token": "DINARI", 
                        "stablecoin": "AFC",
                        "height": chain_info.get('height', 0),
                        "total_transactions": chain_info.get('total_transactions', 0),
                        "pending_transactions": chain_info.get('pending_transactions', 0),
                        "validators": chain_info.get('validators', 0),
                        "contracts": chain_info.get('contracts', 0),
                        "total_dinari_supply": chain_info.get('total_dinari_supply', '0')
                    }
                else:
                    result = {"error": "Blockchain not initialized"}
                    
            elif method == 'dinari_getBalance':
                if not params:
                    raise ValueError("Address parameter required")
                address = params[0]
                if blockchain:
                    dinari_bal = str(blockchain.get_dinari_balance(address))
                    afc_bal = str(blockchain.get_afrocoin_balance(address))
                    result = {
                        "address": address,
                        "DINARI": dinari_bal, 
                        "AFC": afc_bal
                    }
                else:
                    result = {"DINARI": "0", "AFC": "0"}
                    
            elif method == 'dinari_createWallet':
                wallet_name = params[0] if params else f"wallet_{int(time.time())}"
                wallet = create_wallet()
                result = {
                    "success": True,
                    "wallet_name": wallet_name,
                    "message": "Wallet created successfully",
                    "address": f"dinari1{hashlib.sha256(wallet_name.encode()).hexdigest()[:40]}"
                }
                
            elif method == 'dinari_sendTransaction':
                if len(params) < 3:
                    raise ValueError("Required: from_address, to_address, amount")
                
                from_addr = params[0]
                to_addr = params[1] 
                amount = params[2]
                gas_price = params[3] if len(params) > 3 else "0.001"
                data_field = params[4] if len(params) > 4 else ""
                
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
                            "gas_price": gas_price
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
                        "error": contract_result.get('error', None)
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
                        "api_port": PORT
                    }
                else:
                    result = {
                        "node_id": NODE_ID,
                        "connected_peers": 0,
                        "is_validator": False,
                        "p2p_port": P2P_PORT,
                        "api_port": PORT
                    }
                    
            elif method == 'dinari_getValidators':
                if blockchain:
                    result = blockchain.validators if hasattr(blockchain, 'validators') else []
                else:
                    result = []
                    
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
                    "stablecoin": "AFC"
                }
                
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
        
        return jsonify({
            'success': True,
            'wallet_name': wallet_name,
            'message': 'Wallet created successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/network/peers', methods=['GET'])
def get_peers():
    """Get connected peers"""
    try:
        if not blockchain_node:
            return jsonify({'error': 'Node not initialized'}), 503
        
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
            'node_id': NODE_ID
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
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Simple web interface
@app.route('/', methods=['GET'])
def index():
    """Simple web interface"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>DinariBlockchain API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 8px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
            .healthy { background: #d4edda; border: 1px solid #c3e6cb; }
            .unhealthy { background: #f8d7da; border: 1px solid #f5c6cb; }
            .endpoint { background: #e9ecef; padding: 10px; margin: 5px 0; font-family: monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌍 DinariBlockchain API</h1>
            <p>Native DINARI token blockchain with Afrocoin stablecoin support</p>
            
            <h2>📊 Status</h2>
            <div id="status" class="status">Loading...</div>
            
            <h2>🔗 API Endpoints</h2>
            <div class="endpoint">GET /health - Health check</div>
            <div class="endpoint">GET /api/blockchain/info - Blockchain information</div>
            <div class="endpoint">GET /api/blockchain/balance/{address} - Get DINARI & AFC balance</div>
            <div class="endpoint">POST /api/blockchain/transaction - Submit transaction</div>
            <div class="endpoint">GET /api/blockchain/block/{index} - Get block</div>
            <div class="endpoint">POST /api/contracts/deploy - Deploy contract</div>
            <div class="endpoint">POST /api/contracts/call - Call contract</div>
            <div class="endpoint">GET /api/contracts/afrocoin - Afrocoin contract info</div>
            <div class="endpoint">POST /api/wallet/create - Create wallet</div>
            <div class="endpoint">GET /api/network/peers - Get peers</div>
            <div class="endpoint">GET /api/stats - Get statistics</div>
            
            <h2>💰 Token Information</h2>
            <div class="endpoint">Native Token: DINARI (gas fees, transactions)</div>
            <div class="endpoint">Stablecoin: AFC (Afrocoin) - USD pegged</div>
            
            <script>
                fetch('/health')
                    .then(r => r.json())
                    .then(data => {
                        const statusEl = document.getElementById('status');
                        if (data.status === 'healthy') {
                            statusEl.className = 'status healthy';
                            statusEl.innerHTML = `✅ Healthy - Node: ${data.node_id} | Port: ${data.api_port}`;
                        } else {
                            statusEl.className = 'status unhealthy';
                            statusEl.innerHTML = `❌ Unhealthy - ${data.error || 'Unknown error'}`;
                        }
                    })
                    .catch(e => {
                        document.getElementById('status').innerHTML = `❌ Connection Error: ${e}`;
                        document.getElementById('status').className = 'status unhealthy';
                    });
            </script>
        </div>
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
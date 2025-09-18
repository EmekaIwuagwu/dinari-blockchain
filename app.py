#!/usr/bin/env python3
"""
DinariBlockchain - API Server
app.py - Simple Flask API server for Render.com deployment
"""

import os
import json
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
GENESIS_FILE = os.getenv('GENESIS_FILE', 'genesis.json')

def initialize_blockchain():
    """Initialize blockchain and node"""
    global blockchain_node, blockchain, contract_manager
    
    try:
        logger.info(f"🚀 Initializing DinariBlockchain API Server")
        logger.info(f"   Node ID: {NODE_ID}")
        logger.info(f"   P2P Port: {P2P_PORT}")
        logger.info(f"   API Port: {PORT}")
        
        # Create blockchain node
        blockchain_node = DinariNode(
            node_id=NODE_ID,
            host="0.0.0.0",
            port=P2P_PORT,
            genesis_file=GENESIS_FILE,
            data_dir=os.getenv('DATA_DIR', 'data')
        )
        
        # Get blockchain instance
        blockchain = blockchain_node.blockchain
        
        # Create contract manager
        contract_manager = ContractManager(blockchain)
        
        # Start node in background thread
        def start_node():
            blockchain_node.start()
            # Try to connect to bootstrap nodes
            bootstrap_nodes = os.getenv('BOOTSTRAP_NODES', '').split(',')
            for node_addr in bootstrap_nodes:
                if node_addr and ':' in node_addr:
                    host, port = node_addr.split(':')
                    blockchain_node.network.connect_to_peer(host, int(port))
        
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
            stats = blockchain.get_stats()
            status.update({
                'blockchain': {
                    'height': stats['total_blocks'],
                    'transactions': stats['total_transactions'],
                    'pending': stats['pending_transactions'],
                    'valid': stats['chain_valid']
                }
            })
        
        if blockchain_node:
            node_status = blockchain_node.get_node_status()
            status.update({
                'network': {
                    'peers': node_status['peers_connected'],
                    'running': node_status['running'],
                    'is_validator': node_status['is_validator']
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
        
        stats = blockchain.get_stats()
        latest_block = blockchain.get_latest_block()
        
        info = {
            'network_id': blockchain.genesis_config.get('network_id', 'unknown'),
            'token_symbol': blockchain.genesis_config.get('token_symbol', 'DINARI'),
            'total_supply': blockchain.genesis_config.get('total_supply', '0'),
            'chain_height': stats['total_blocks'],
            'total_transactions': stats['total_transactions'],
            'pending_transactions': stats['pending_transactions'],
            'validators': len(blockchain.validators),
            'contracts': stats['total_contracts'],
            'latest_block': {
                'index': latest_block.index,
                'hash': latest_block.hash[:16] + '...',
                'validator': latest_block.validator,
                'timestamp': latest_block.timestamp,
                'tx_count': len(latest_block.transactions)
            },
            'chain_valid': stats['chain_valid']
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
        
        balance = blockchain.get_balance(address)
        
        return jsonify({
            'address': address,
            'balance': str(balance),
            'symbol': blockchain.genesis_config.get('token_symbol', 'DINARI')
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/blockchain/transaction', methods=['POST'])
def submit_transaction():
    """Submit a new transaction"""
    try:
        if not blockchain_node:
            return jsonify({'error': 'Node not initialized'}), 503
        
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
            amount=data['amount'],
            fee=data.get('fee', '0.001'),
            data=data.get('data', '')
        )
        
        # Submit to network
        success = blockchain_node.submit_transaction(
            data['from_address'],
            data['to_address'], 
            data['amount'],
            data.get('fee', '0.001')
        )
        
        if success:
            return jsonify({
                'success': True,
                'transaction_hash': tx.calculate_hash(),
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
        
        if block_index >= len(blockchain.chain) or block_index < 0:
            return jsonify({'error': 'Block not found'}), 404
        
        block = blockchain.chain[block_index]
        block_data = block.to_dict()
        
        # Add additional info
        block_data['transaction_count'] = len(block.transactions)
        block_data['size'] = len(json.dumps(block_data))
        
        return jsonify(block_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contracts/deploy', methods=['POST'])
def deploy_contract():
    """Deploy a smart contract"""
    try:
        if not contract_manager:
            return jsonify({'error': 'Contract manager not initialized'}), 503
        
        data = request.get_json()
        
        if 'template' in data:
            # Deploy from template
            deployment = contract_manager.deploy_from_template(
                data['template'],
                data.get('deployer', 'treasury'),
                data.get('args', [])
            )
        elif 'code' in data:
            # Deploy custom contract
            contract_address = contract_manager.deploy_contract(
                data['code'],
                data.get('deployer', 'treasury'),
                data.get('args', [])
            )
            deployment = type('obj', (object,), {'address': contract_address})
        else:
            return jsonify({'error': 'Missing template or code'}), 400
        
        return jsonify({
            'success': True,
            'contract_address': deployment.address,
            'deployer': data.get('deployer', 'treasury')
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
        
        required_fields = ['contract_address', 'function_name', 'caller']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        result = contract_manager.call_contract(
            data['contract_address'],
            data['function_name'],
            data.get('args', []),
            data['caller']
        )
        
        return jsonify({
            'success': result.success,
            'result': result.result,
            'gas_used': result.gas_used,
            'events': result.events,
            'error': result.error if not result.success else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wallet/create', methods=['POST'])
def create_new_wallet():
    """Create a new wallet"""
    try:
        data = request.get_json()
        wallet_name = data.get('name', f'wallet_{int(time.time())}')
        
        wallet = create_wallet(wallet_name)
        addresses = wallet.get_all_addresses()
        
        return jsonify({
            'success': True,
            'wallet_name': wallet_name,
            'addresses': addresses,
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
        
        peers = blockchain_node.network.get_connected_peers()
        peer_list = []
        
        for peer in peers:
            peer_list.append({
                'peer_id': peer.peer_id,
                'address': peer.address,
                'connected_at': peer.connected_at,
                'last_seen': peer.last_seen,
                'is_validator': peer.is_validator
            })
        
        return jsonify({
            'connected_peers': len(peer_list),
            'peers': peer_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get comprehensive blockchain statistics"""
    try:
        stats = {}
        
        if blockchain:
            blockchain_stats = blockchain.get_stats()
            stats['blockchain'] = blockchain_stats
        
        if blockchain_node:
            node_stats = blockchain_node.get_node_status()
            stats['node'] = node_stats
            
            network_stats = blockchain_node.network.get_network_stats()
            stats['network'] = network_stats
        
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
            <p>A blockchain-based stablecoin for Africa</p>
            
            <h2>📊 Status</h2>
            <div id="status" class="status">Loading...</div>
            
            <h2>🔗 API Endpoints</h2>
            <div class="endpoint">GET /health - Health check</div>
            <div class="endpoint">GET /api/blockchain/info - Blockchain information</div>
            <div class="endpoint">GET /api/blockchain/balance/{address} - Get balance</div>
            <div class="endpoint">POST /api/blockchain/transaction - Submit transaction</div>
            <div class="endpoint">GET /api/blockchain/block/{index} - Get block</div>
            <div class="endpoint">POST /api/contracts/deploy - Deploy contract</div>
            <div class="endpoint">POST /api/contracts/call - Call contract</div>
            <div class="endpoint">POST /api/wallet/create - Create wallet</div>
            <div class="endpoint">GET /api/network/peers - Get peers</div>
            <div class="endpoint">GET /api/stats - Get statistics</div>
            
            <script>
                fetch('/health')
                    .then(r => r.json())
                    .then(data => {
                        const statusEl = document.getElementById('status');
                        if (data.status === 'healthy') {
                            statusEl.className = 'status healthy';
                            statusEl.innerHTML = `✅ Healthy - Node: ${data.node_id}`;
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

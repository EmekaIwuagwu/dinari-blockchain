#!/usr/bin/env python3
"""
DinariBlockchain RPC Server
rpc/rpc_server.py - JSON-RPC server for blockchain operations
"""

import json
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from typing import Dict, Any, List, Optional

# Import DinariBlockchain components
from Dinari import (
    DinariBlockchain,
    DinariNode,
    Transaction,
    ContractManager,
    create_wallet,
    setup_logging
)

# Import Dinari Stablecoin endpoints
try:
    from dinari_endpoints import register_dinari_endpoints
    DINARI_STABLECOIN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Dinari Stablecoin endpoints not available: {e}")
    DINARI_STABLECOIN_AVAILABLE = False

class DinariRPCServer:
    """JSON-RPC server for DinariBlockchain"""
    
    def __init__(self, node: DinariNode = None, host: str = "127.0.0.1", port: int = 8545):
        self.host = host
        self.port = port
        self.node = node
        self.blockchain = node.blockchain if node else None
        self.contract_manager = ContractManager(self.blockchain) if self.blockchain else None
        
        # Check if Dinari Stablecoin is available
        self.dinari_stablecoin_available = DINARI_STABLECOIN_AVAILABLE
        
        # Setup Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger("DinariRPC")
        
        # Setup routes
        self._setup_routes()
        
        # RPC method mapping
        self.rpc_methods = {
            # Blockchain methods
            'dinari_getBlockchainInfo': self._get_blockchain_info,
            'dinari_getBalance': self._get_balance,
            'dinari_getBlock': self._get_block,
            'dinari_sendTransaction': self._send_transaction,
            'dinari_createWallet': self._create_wallet,
            
            # Contract methods
            'dinari_deployContract': self._deploy_contract,
            'dinari_callContract': self._call_contract,
            'dinari_getContractInfo': self._get_contract_info,
            
            # Network methods
            'dinari_getNetworkInfo': self._get_network_info,
            'dinari_getPeers': self._get_peers,
            
            # Mining/Validation methods
            'dinari_getValidators': self._get_validators,
            'dinari_mineBlock': self._mine_block,
            
            # Utility methods
            'dinari_ping': self._ping,
            'dinari_getVersion': self._get_version,
        }
        
        self.logger.info(f"DinariBlockchain RPC Server initialized on {host}:{port}")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/rpc', methods=['POST'])
        def handle_rpc():
            return self._handle_rpc_request()
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'service': 'DinariBlockchain RPC',
                'version': '1.0.0',
                'timestamp': time.time()
            })
        
        @self.app.route('/', methods=['GET'])
        def index():
            stablecoin_status = "✅ Available" if self.dinari_stablecoin_available else "❌ Not Available"
            stablecoin_endpoints = """
                    <h3>🌍 Dinari Stablecoin Endpoints:</h3>
                    <ul>
                        <li><code>POST /rpc/dinari/balance</code> - Check Dinari balance</li>
                        <li><code>POST /rpc/dinari/transfer</code> - Transfer Dinari</li>
                        <li><code>POST /rpc/dinari/deposit</code> - Deposit collateral</li>
                        <li><code>POST /rpc/dinari/mint</code> - Mint Dinari</li>
                        <li><code>POST /rpc/dinari/burn</code> - Burn Dinari</li>
                        <li><code>POST /rpc/dinari/withdraw</code> - Withdraw collateral</li>
                        <li><code>POST /rpc/dinari/mobile-deposit</code> - Mobile money deposit</li>
                        <li><code>POST /rpc/dinari/remittance</code> - Send remittance</li>
                        <li><code>POST /rpc/dinari/vault-info</code> - Get vault information</li>
                        <li><code>GET /rpc/dinari/protocol-stats</code> - Get protocol stats</li>
                        <li><code>GET /rpc/dinari/collateral-assets</code> - Get collateral assets</li>
                        <li><code>GET /rpc/dinari/mobile-gateways</code> - Get mobile gateways</li>
                    </ul>
            """ if self.dinari_stablecoin_available else """
                    <p>⚠️  Dinari Stablecoin endpoints not available. Please ensure contracts/dinari_stablecoin.py exists.</p>
            """
            
            return f"""
            <html>
            <head><title>DinariBlockchain RPC Server</title></head>
            <body>
                <h1>🌍 DinariBlockchain RPC Server</h1>
                <p>JSON-RPC endpoint: <code>POST /rpc</code></p>
                <p>Health check: <code>GET /health</code></p>
                <p>Dinari Stablecoin: <strong>{stablecoin_status}</strong></p>
                
                <h2>Available Core RPC Methods:</h2>
                <ul>
                    <li><code>dinari_ping</code> - Test connectivity</li>
                    <li><code>dinari_getVersion</code> - Get version</li>
                    <li><code>dinari_getBlockchainInfo</code> - Get blockchain info</li>
                    <li><code>dinari_getBalance</code> - Get account balance</li>
                    <li><code>dinari_getBlock</code> - Get block by index</li>
                    <li><code>dinari_sendTransaction</code> - Send transaction</li>
                    <li><code>dinari_createWallet</code> - Create wallet</li>
                    <li><code>dinari_deployContract</code> - Deploy contract</li>
                    <li><code>dinari_callContract</code> - Call contract</li>
                    <li><code>dinari_getValidators</code> - Get validators</li>
                    <li><code>dinari_mineBlock</code> - Mine block</li>
                </ul>
                
                {stablecoin_endpoints}
                
                <h3>🧪 Web Interface:</h3>
                <p><a href="/web/dinari_stablecoin_interface.html" target="_blank">Dinari Stablecoin Testing Interface</a></p>
            </body>
            </html>
            """
        
        # ✅ ADD DINARI STABLECOIN ENDPOINTS HERE
        if self.dinari_stablecoin_available:
            try:
                register_dinari_endpoints(self.app)
                self.logger.info("✅ Dinari Stablecoin endpoints registered successfully")
            except Exception as e:
                self.logger.error(f"❌ Failed to register Dinari endpoints: {e}")
                self.dinari_stablecoin_available = False
        
        # Serve static web files
        @self.app.route('/web/<path:filename>')
        def serve_web_files(filename):
            from flask import send_from_directory
            web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web')
            if os.path.exists(os.path.join(web_dir, filename)):
                return send_from_directory(web_dir, filename)
            else:
                return f"File not found: {filename}<br>Looking in: {web_dir}", 404
    
    def _handle_rpc_request(self):
        """Handle JSON-RPC requests"""
        try:
            request_data = request.get_json()
            if not request_data:
                return self._create_error_response(None, -32700, "Parse error")
            
            # Validate JSON-RPC format
            if not all(key in request_data for key in ['jsonrpc', 'method', 'id']):
                return self._create_error_response(
                    request_data.get('id'), -32600, "Invalid Request"
                )
            
            method = request_data['method']
            params = request_data.get('params', [])
            request_id = request_data['id']
            
            # Execute method
            if method in self.rpc_methods:
                try:
                    result = self.rpc_methods[method](params)
                    return self._create_success_response(request_id, result)
                except Exception as e:
                    self.logger.error(f"RPC method error: {e}")
                    return self._create_error_response(request_id, -32603, str(e))
            else:
                return self._create_error_response(request_id, -32601, "Method not found")
        
        except Exception as e:
            self.logger.error(f"RPC request error: {e}")
            return self._create_error_response(None, -32700, "Parse error")
    
    def _create_success_response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        return jsonify({
            'jsonrpc': '2.0',
            'id': request_id,
            'result': result
        })
    
    def _create_error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        return jsonify({
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {'code': code, 'message': message}
        })
    
    # RPC Methods (keeping all your existing methods unchanged)
    def _get_blockchain_info(self, params: List) -> Dict[str, Any]:
        if not self.blockchain:
            raise Exception("Blockchain not available")
        
        stats = self.blockchain.get_stats()
        latest_block = self.blockchain.get_latest_block()
        
        return {
            'chain_height': stats['total_blocks'],
            'total_transactions': stats['total_transactions'],
            'pending_transactions': stats['pending_transactions'],
            'total_validators': stats['total_validators'],
            'latest_block': {
                'index': latest_block.index,
                'hash': latest_block.hash[:16] + '...',
                'timestamp': latest_block.timestamp,
                'validator': latest_block.validator
            }
        }
    
    def _get_balance(self, params: List) -> str:
        if len(params) < 1:
            raise Exception("Missing address parameter")
        
        address = params[0]
        balance = self.blockchain.get_balance(address)
        return str(balance)
    
    def _get_block(self, params: List) -> Dict[str, Any]:
        if len(params) < 1:
            raise Exception("Missing block_index parameter")
        
        block_index = int(params[0])
        if block_index >= len(self.blockchain.chain) or block_index < 0:
            raise Exception("Block not found")
        
        block = self.blockchain.chain[block_index]
        return block.to_dict()
    
    def _send_transaction(self, params: List) -> Dict[str, Any]:
        if len(params) < 3:
            raise Exception("Missing parameters: from_address, to_address, amount")
        
        from_address = params[0]
        to_address = params[1]
        amount = params[2]
        fee = params[3] if len(params) > 3 else "0.001"

        if not self._validate_address(from_address):
            raise Exception("Invalid from_address")
        if not self._validate_address(to_address):
            raise Exception("Invalid to_address")  
        if not self._validate_amount(amount):
            raise Exception("Invalid amount")
        
        tx = Transaction(from_address, to_address, amount, fee)
        
        if self.blockchain.add_transaction(tx):
            return {
                'transaction_hash': tx.calculate_hash(),
                'status': 'pending'
            }
        else:
            raise Exception("Failed to add transaction")
    
    def _create_wallet(self, params: List) -> Dict[str, Any]:
        wallet_name = params[0] if params else f"wallet_{int(time.time())}"
        
        try:
            wallet = create_wallet(wallet_name)
            addresses = wallet.get_all_addresses()
            
            return {
                'wallet_name': wallet_name,
                'addresses': addresses
            }
        except Exception as e:
            raise Exception(f"Failed to create wallet: {e}")
    
    def _deploy_contract(self, params: List) -> Dict[str, Any]:
        if not self.contract_manager or len(params) < 2:
            raise Exception("Missing parameters: contract_code, deployer")
        
        contract_code = params[0]
        deployer = params[1]
        init_args = params[2] if len(params) > 2 else []
        
        try:
            deployment = self.contract_manager.deploy_contract(contract_code, deployer, init_args)
            return {
                'contract_address': deployment.address,
                'deployer': deployment.deployer,
                'gas_used': deployment.gas_used
            }
        except Exception as e:
            raise Exception(f"Contract deployment failed: {e}")
    
    def _call_contract(self, params: List) -> Dict[str, Any]:
        if not self.contract_manager or len(params) < 3:
            raise Exception("Missing parameters: contract_address, function_name, caller")
        
        contract_address = params[0]
        function_name = params[1]
        caller = params[2]
        args = params[3] if len(params) > 3 else []
        
        result = self.contract_manager.call_contract(contract_address, function_name, args, caller)
        
        return {
            'success': result.success,
            'result': result.result,
            'gas_used': result.gas_used,
            'error': result.error if not result.success else None
        }
    
    def _validate_address(self, address: str) -> bool:
    """Validate Dinari address format"""
    if not address or not isinstance(address, str):
        return False
    if not address.startswith('DINARI') and address not in ['treasury', 'genesis']:
        return False
    return True

    def _validate_amount(self, amount: str) -> bool:
    """Validate amount format"""
    try:
        value = float(amount)
        return 0 < value <= 1e18
    except (ValueError, TypeError):
        return False
    
    def _get_contract_info(self, params: List) -> Dict[str, Any]:
        if not self.contract_manager or len(params) < 1:
            raise Exception("Missing contract_address parameter")
        
        contract_address = params[0]
        contract = self.contract_manager.get_contract(contract_address)
        
        if not contract:
            raise Exception("Contract not found")
        
        return {
            'address': contract.address,
            'deployer': contract.deployer,
            'created_at': contract.created_at
        }
    
    def _get_network_info(self, params: List) -> Dict[str, Any]:
        if not self.node:
            raise Exception("Node not available")
        
        status = self.node.get_node_status()
        
        return {
            'node_id': status['node_id'],
            'is_validator': status['is_validator'],
            'peers_connected': status['peers_connected'],
            'running': status['running']
        }
    
    def _get_peers(self, params: List) -> List[Dict[str, Any]]:
        if not self.node or not hasattr(self.node, 'network'):
            return []
        
        peers = self.node.network.get_connected_peers()
        return [
            {
                'peer_id': peer.peer_id,
                'address': peer.address,
                'connected_at': peer.connected_at
            }
            for peer in peers
        ]
    
    def _get_validators(self, params: List) -> List[str]:
        return self.blockchain.validators if self.blockchain else []
    
    def _mine_block(self, params: List) -> Dict[str, Any]:
        validator = params[0] if params else self.blockchain.validators[0]
        
        block = self.blockchain.mine_block(validator)
        if block:
            return {
                'success': True,
                'block_index': block.index,
                'block_hash': block.hash[:16] + '...',
                'transactions': len(block.transactions)
            }
        else:
            return {
                'success': False,
                'message': 'No transactions to mine'
            }
    
    def _ping(self, params: List) -> str:
        return "pong"
    
    def _get_version(self, params: List) -> Dict[str, str]:
        return {
            'version': '1.0.0',
            'name': 'DinariBlockchain',
            'description': 'A blockchain-based stablecoin for Africa'
        }
    
    def start(self):
        """Start the RPC server"""
        self.logger.info(f"Starting RPC Server on {self.host}:{self.port}")
        
        # Print startup information
        print("=" * 60)
        print("🌍 DinariBlockchain RPC Server")
        print("=" * 60)
        print(f"🌐 RPC URL: http://{self.host}:{self.port}/rpc")
        print(f"🏥 Health Check: http://{self.host}:{self.port}/health")
        print(f"🖥️  Web Interface: http://{self.host}:{self.port}/")
        
        if self.dinari_stablecoin_available:
            print("✅ Dinari Stablecoin: ENABLED")
            print(f"🎯 Stablecoin Interface: http://{self.host}:{self.port}/web/dinari_stablecoin_interface.html")
        else:
            print("❌ Dinari Stablecoin: DISABLED")
        
        print("=" * 60)
        print("Press Ctrl+C to stop the server")
        print()
        
        self.app.run(host=self.host, port=self.port, debug=False)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DinariBlockchain RPC Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8545, help="Port number")
    parser.add_argument("--node-id", default="rpc_node", help="Node ID")
    
    args = parser.parse_args()
    
    # Create blockchain node
    node = DinariNode(
        node_id=args.node_id,
        host=args.host,
        port=8333,
        genesis_file="genesis.json"
    )
    
    node.start()
    
    # Create and start RPC server
    rpc_server = DinariRPCServer(node, args.host, args.port)
    
    try:
        rpc_server.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down RPC server...")
        node.stop()
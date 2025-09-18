#!/usr/bin/env python3
"""
DinariBlockchain Node Implementation
Dinari/node.py - Complete blockchain node with P2P networking and consensus
"""

import json
import time
import threading
import socket
import pickle
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import signal
import sys

# Import our blockchain components
from .blockchain import DinariBlockchain, Transaction, Block

@dataclass
class NetworkMessage:
    """P2P network message structure"""
    message_type: str
    sender_id: str
    data: Any
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_bytes(self) -> bytes:
        """Serialize message for network transmission"""
        return pickle.dumps(self.__dict__)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'NetworkMessage':
        """Deserialize message from network data"""
        msg_dict = pickle.loads(data)
        return cls(**msg_dict)

class P2PNetworkManager:
    """Handles P2P networking for blockchain nodes"""
    
    def __init__(self, node_id: str, host: str = "127.0.0.1", port: int = 8333):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.peers: Dict[str, Tuple[str, int]] = {}
        self.server_socket = None
        self.running = False
        self.message_handlers = {}
        
        # Setup logging
        self.logger = logging.getLogger(f"P2P-{node_id}")
    
    def set_message_handler(self, message_type: str, handler):
        """Set handler for specific message type"""
        self.message_handlers[message_type] = handler
    
    def start_server(self):
        """Start P2P server to accept incoming connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.running = True
            
            self.logger.info(f"P2P server started on {self.host}:{self.port}")
            
            # Accept connections in background thread
            threading.Thread(target=self._accept_connections, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Failed to start P2P server: {e}")
            self.running = False
    
    def _accept_connections(self):
        """Accept incoming peer connections"""
        while self.running:
            try:
                if self.server_socket:
                    client_socket, address = self.server_socket.accept()
                    self.logger.info(f"New peer connection from {address}")
                    
                    # Handle peer in separate thread
                    threading.Thread(
                        target=self._handle_peer_connection,
                        args=(client_socket, address),
                        daemon=True
                    ).start()
                    
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error accepting connection: {e}")
    
    def _handle_peer_connection(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle communication with a connected peer"""
        try:
            while self.running:
                data = client_socket.recv(8192)
                if not data:
                    break
                
                try:
                    message = NetworkMessage.from_bytes(data)
                    self._process_message(message, client_socket, address)
                except Exception as e:
                    self.logger.error(f"Error processing message from {address}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error handling peer {address}: {e}")
        finally:
            client_socket.close()
    
    def _process_message(self, message: NetworkMessage, sender_socket: socket.socket, sender_address: Tuple[str, int]):
        """Process received network message"""
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                handler(message, sender_socket, sender_address)
            except Exception as e:
                self.logger.error(f"Error in message handler for {message.message_type}: {e}")
        else:
            self.logger.warning(f"No handler for message type: {message.message_type}")
    
    def connect_to_peer(self, host: str, port: int) -> bool:
        """Connect to a peer node"""
        peer_id = f"{host}:{port}"
        
        if peer_id in self.peers:
            return True  # Already connected
        
        try:
            # Test connection
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            test_socket.connect((host, port))
            test_socket.close()
            
            # Add to peers list
            self.peers[peer_id] = (host, port)
            self.logger.info(f"Connected to peer: {peer_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to peer {host}:{port}: {e}")
            return False
    
    def _send_message_to_peer(self, host: str, port: int, message: NetworkMessage):
        """Send message to specific peer"""
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.settimeout(5)
            peer_socket.connect((host, port))
            peer_socket.send(message.to_bytes())
            peer_socket.close()
        except Exception as e:
            self.logger.error(f"Failed to send message to {host}:{port}: {e}")
    
    def broadcast_message(self, message: NetworkMessage):
        """Broadcast message to all connected peers"""
        for peer_id, (host, port) in self.peers.items():
            self._send_message_to_peer(host, port, message)
    
    def stop(self):
        """Stop P2P networking"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.logger.info("P2P network stopped")

class DinariNode:
    """Complete Dinari blockchain node"""
    
    def __init__(self, node_id: str, host: str = "127.0.0.1", port: int = 8333, 
                 genesis_file: str = "genesis.json", data_dir: str = "data"):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.data_dir = os.path.join(data_dir, node_id)
        self.genesis_file = genesis_file
        self.running = False
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize components
        self.genesis_config = self._load_genesis_config()
        self.blockchain = DinariBlockchain(self.genesis_config)
        self.network = P2PNetworkManager(node_id, host, port)
        
        # Setup network message handlers
        self._setup_message_handlers()
        
        # Mining thread
        self.mining_thread = None
        self.is_validator = node_id in self.blockchain.validators
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f"DinariNode-{node_id}")
        
        self.logger.info(f"Node {node_id} initialized as {'validator' if self.is_validator else 'regular node'}")
    
    def _load_genesis_config(self) -> Dict[str, Any]:
        """Load genesis configuration"""
        try:
            with open(self.genesis_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Genesis file {self.genesis_file} not found, using defaults")
            return {}
    
    def _setup_message_handlers(self):
        """Setup handlers for different network message types"""
        self.network.set_message_handler("hello", self._handle_hello_message)
        self.network.set_message_handler("transaction", self._handle_transaction_message)
        self.network.set_message_handler("block", self._handle_block_message)
        self.network.set_message_handler("sync_request", self._handle_sync_request)
        self.network.set_message_handler("sync_response", self._handle_sync_response)
        self.network.set_message_handler("ping", self._handle_ping_message)
        self.network.set_message_handler("pong", self._handle_pong_message)
    
    def _handle_hello_message(self, message: NetworkMessage, sender_socket, sender_address):
        """Handle hello message from new peer"""
        self.logger.info(f"Received hello from {message.sender_id}")
        
        # Send hello back
        hello_response = NetworkMessage("hello", self.node_id, {
            "node_info": {
                "id": self.node_id,
                "host": self.host,
                "port": self.port,
                "is_validator": self.is_validator
            }
        })
        sender_socket.send(hello_response.to_bytes())
    
    def _handle_transaction_message(self, message: NetworkMessage, sender_socket, sender_address):
        """Handle transaction broadcast from peer"""
        tx_data = message.data
        transaction = Transaction.from_dict(tx_data)
        
        if self.blockchain.add_transaction(transaction):
            self.logger.info(f"Received valid transaction from {message.sender_id}")
            
            # Rebroadcast to other peers (except sender)
            self._rebroadcast_message(message, exclude_sender=message.sender_id)
        else:
            self.logger.warning(f"Rejected invalid transaction from {message.sender_id}")
    
    def _handle_block_message(self, message: NetworkMessage, sender_socket, sender_address):
        """Handle new block broadcast from peer"""
        block_data = message.data
        block = Block.from_dict(block_data)
        
        # Validate block
        if block.is_valid(self.blockchain.get_latest_block()):
            # Add block to chain
            self.blockchain.chain.append(block)
            
            # Remove processed transactions from pool
            block_tx_hashes = {tx.calculate_hash() for tx in block.transactions}
            self.blockchain.transaction_pool = [
                tx for tx in self.blockchain.transaction_pool 
                if tx.calculate_hash() not in block_tx_hashes
            ]
            
            # Update balances
            self.blockchain._process_block_transactions(block.transactions)
            
            self.logger.info(f"Accepted new block {block.index} from {message.sender_id}")
            
            # Rebroadcast to other peers
            self._rebroadcast_message(message, exclude_sender=message.sender_id)
        else:
            self.logger.warning(f"Rejected invalid block from {message.sender_id}")
    
    def _handle_sync_request(self, message: NetworkMessage, sender_socket, sender_address):
        """Handle blockchain sync request"""
        peer_chain_length = message.data.get("chain_length", 0)
        
        if len(self.blockchain.chain) > peer_chain_length:
            # Send our chain
            sync_response = NetworkMessage("sync_response", self.node_id, {
                "chain": [block.to_dict() for block in self.blockchain.chain],
                "chain_length": len(self.blockchain.chain)
            })
            sender_socket.send(sync_response.to_bytes())
    
    def _handle_sync_response(self, message: NetworkMessage, sender_socket, sender_address):
        """Handle blockchain sync response"""
        peer_chain_data = message.data.get("chain", [])
        peer_chain_length = message.data.get("chain_length", 0)
        
        if peer_chain_length > len(self.blockchain.chain):
            # Validate peer chain
            peer_chain = [Block.from_dict(block_data) for block_data in peer_chain_data]
            
            if self._validate_chain(peer_chain):
                self.blockchain.chain = peer_chain
                self._recalculate_balances()
                self.logger.info(f"Synchronized blockchain from {message.sender_id}")
    
    def _handle_ping_message(self, message: NetworkMessage, sender_socket, sender_address):
        """Handle ping message"""
        pong_msg = NetworkMessage("pong", self.node_id, {"timestamp": time.time()})
        sender_socket.send(pong_msg.to_bytes())
    
    def _handle_pong_message(self, message: NetworkMessage, sender_socket, sender_address):
        """Handle pong message"""
        self.logger.debug(f"Received pong from {message.sender_id}")
    
    def _rebroadcast_message(self, message: NetworkMessage, exclude_sender: str):
        """Rebroadcast message to peers except the sender"""
        for peer_id, (host, port) in self.network.peers.items():
            if peer_id != f"{host}:{port}" or message.sender_id != exclude_sender:
                self.network._send_message_to_peer(host, port, message)
    
    def _validate_chain(self, chain: List[Block]) -> bool:
        """Validate a blockchain"""
        for i in range(1, len(chain)):
            if not chain[i].is_valid(chain[i-1]):
                return False
        return True
    
    def _recalculate_balances(self):
        """Recalculate all balances from blockchain"""
        self.blockchain.balances = {}
        
        for block in self.blockchain.chain:
            self.blockchain._process_block_transactions(block.transactions)
    
    def start(self):
        """Start the blockchain node"""
        self.running = True
        
        # Start P2P networking
        self.network.start_server()
        
        # Start mining if validator
        if self.is_validator:
            self.mining_thread = threading.Thread(target=self._mining_loop, daemon=True)
            self.mining_thread.start()
        
        self.logger.info(f"DinariNode {self.node_id} started successfully")
    
    def stop(self):
        """Stop the blockchain node"""
        self.running = False
        self.network.stop()
        
        # Save blockchain state
        self.save_blockchain()
        
        self.logger.info(f"DinariNode {self.node_id} stopped")
    
    def _mining_loop(self):
        """Main mining loop for validator nodes"""
        self.logger.info(f"Mining started for validator {self.node_id}")
        
        while self.running:
            try:
                # Mine block if transactions are available
                if len(self.blockchain.transaction_pool) > 0:
                    block = self.blockchain.mine_block(self.node_id)
                    
                    if block:
                        # Broadcast new block to network
                        block_msg = NetworkMessage("block", self.node_id, block.to_dict())
                        self.network.broadcast_message(block_msg)
                        
                        self.logger.info(f"Mined and broadcast block {block.index}")
                
                # Wait before next mining attempt
                time.sleep(self.blockchain.block_time)
                
            except Exception as e:
                self.logger.error(f"Error in mining loop: {e}")
    
    def connect_to_peers(self, peer_addresses: List[Tuple[str, int]]):
        """Connect to multiple peers"""
        for host, port in peer_addresses:
            if f"{host}:{port}" != f"{self.host}:{self.port}":  # Don't connect to self
                self.network.connect_to_peer(host, port)
    
    def submit_transaction(self, from_address: str, to_address: str, amount: str, fee: str = "0.001"):
        """Submit a transaction to the network"""
        transaction = Transaction(from_address, to_address, amount, fee)
        
        if self.blockchain.add_transaction(transaction):
            # Broadcast transaction to network
            tx_msg = NetworkMessage("transaction", self.node_id, transaction.to_dict())
            self.network.broadcast_message(tx_msg)
            
            self.logger.info(f"Transaction submitted and broadcast: {transaction.calculate_hash()[:8]}")
            return True
        return False
    
    def get_node_status(self) -> Dict[str, Any]:
        """Get current node status"""
        return {
            "node_id": self.node_id,
            "host": self.host,
            "port": self.port,
            "is_validator": self.is_validator,
            "running": self.running,
            "peers_connected": len(self.network.peers),
            "blockchain_stats": self.blockchain.get_stats()
        }
    
    def save_blockchain(self):
        """Save blockchain to file"""
        filename = os.path.join(self.data_dir, "blockchain.json")
        self.blockchain.save_to_file(filename)
    
    def load_blockchain(self):
        """Load blockchain from file"""
        filename = os.path.join(self.data_dir, "blockchain.json")
        if os.path.exists(filename):
            self.blockchain = DinariBlockchain.load_from_file(filename)
            self.logger.info("Blockchain loaded from file")


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DinariBlockchain Node")
    parser.add_argument("--node-id", required=True, help="Node identifier")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8333, help="Port number")
    parser.add_argument("--genesis", default="genesis.json", help="Genesis file")
    parser.add_argument("--data-dir", default="data", help="Data directory")
    
    args = parser.parse_args()
    
    # Create and start node
    node = DinariNode(args.node_id, args.host, args.port, args.genesis, args.data_dir)
    
    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        print(f"\nShutting down node {args.node_id}...")
        node.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start node
    node.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        node.stop()
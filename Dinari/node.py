"""
Dinari Node with LevelDB Storage
File: dinari/node.py (REPLACE existing file)
"""

import json
import logging
import threading
import time
from typing import Dict, List, Optional, Any
from .blockchain import DinariBlockchain, Transaction, Block
from .consensus import ProofOfAuthority
from .network import P2PNetworkManager
from .database import DinariLevelDB

class DinariNode:
    """Dinari blockchain node with LevelDB storage"""
    
    def __init__(self, node_id: str, host: str = "127.0.0.1", port: int = 8333,
                 db_path: str = None, is_validator: bool = False):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.is_validator = is_validator
        self.is_running = False
        
        # Setup logging
        self.logger = logging.getLogger(f"DinariNode-{node_id}")
        
        # Initialize LevelDB path
        if db_path is None:
            db_path = f"./dinari_data_{node_id}"
        
        # Initialize components
        self.blockchain = DinariBlockchain(db_path)
        self.consensus = ProofOfAuthority()
        self.network = P2PNetworkManager(self.node_id, host, port)
        
        # Node state (also stored in LevelDB)
        self.db = self.blockchain.db  # Reuse blockchain's LevelDB instance
        self._load_node_state()
        
        # Networking
        self.peers = {}
        self.peer_lock = threading.Lock()
        
        # Mining/Validation
        self.mining_thread = None
        self.mining_enabled = False
        
        self.logger.info(f"Node {node_id} initialized as {'validator' if is_validator else 'regular'} node")

    def _load_node_state(self):
        """Load node state from LevelDB"""
        node_state = self.db.get(f"node_state:{self.node_id}")
        if node_state:
            self.peers = node_state.get('peers', {})
            self.is_validator = node_state.get('is_validator', self.is_validator)
            self.logger.info(f"Loaded node state from LevelDB")
        else:
            self._save_node_state()

    def _save_node_state(self):
        """Save node state to LevelDB"""
        node_state = {
            'node_id': self.node_id,
            'host': self.host,
            'port': self.port,
            'is_validator': self.is_validator,
            'peers': self.peers,
            'last_updated': time.time()
        }
        self.db.put(f"node_state:{self.node_id}", node_state)

    def start(self):
        """Start the Dinari node"""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start P2P server
        try:
            self.p2p.start()
            self.logger.info(f"P2P server started on {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start P2P server: {e}")
            self.is_running = False
            return
        
        # Start mining if validator
        if self.is_validator:
            self._start_mining()
        
        # Save initial state
        self._save_node_state()
        
        self.logger.info(f"DinariNode {self.node_id} started successfully")

    def stop(self):
        """Stop the Dinari node"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Stop mining
        if self.mining_thread and self.mining_thread.is_alive():
            self.mining_enabled = False
            self.mining_thread.join(timeout=5)
        
        # Stop P2P server
        self.p2p.stop()
        
        # Close blockchain and database
        self.blockchain.close()
        
        self.logger.info(f"DinariNode {self.node_id} stopped")

    def _start_mining(self):
        """Start mining/validation thread"""
        if not self.is_validator:
            return
            
        self.mining_enabled = True
        self.mining_thread = threading.Thread(target=self._mining_loop, daemon=True)
        self.mining_thread.start()
        self.logger.info("Mining/validation started")

    def _mining_loop(self):
        """Main mining/validation loop"""
        while self.mining_enabled and self.is_running:
            try:
                # Check if we should create a new block
                if len(self.blockchain.pending_transactions) >= 1:  # Create block with at least 1 transaction
                    self._create_and_propose_block()
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in mining loop: {e}")
                time.sleep(1)

    def _create_and_propose_block(self):
        """Create and propose new block"""
        try:
            # Create new block
            new_block = self.blockchain.create_block(self.node_id)
            if not new_block:
                return
            
            # Validate block
            if self.blockchain.add_block(new_block):
                self.logger.info(f"New block created: {new_block.hash[:16]}... (Height: {new_block.index})")
                
                # Broadcast to peers
                self._broadcast_block(new_block)
                
                # Update node state
                self._save_node_state()
            else:
                self.logger.warning("Failed to add created block")
                
        except Exception as e:
            self.logger.error(f"Error creating block: {e}")

    def _broadcast_block(self, block: Block):
        """Broadcast block to all peers"""
        message = {
            'type': 'new_block',
            'data': block.to_dict(),
            'sender': self.node_id
        }
        self.p2p.broadcast(message)

    def add_transaction(self, sender: str, recipient: str, amount: float, 
                       fee: float = 0.0, data: str = "") -> Optional[str]:
        """Add transaction to blockchain"""
        try:
            transaction = Transaction(sender, recipient, amount, fee, data)
            if self.blockchain.add_transaction(transaction):
                # Broadcast transaction to network
                self._broadcast_transaction(transaction)
                return transaction.hash
            return None
        except Exception as e:
            self.logger.error(f"Error adding transaction: {e}")
            return None

    def _broadcast_transaction(self, transaction: Transaction):
        """Broadcast transaction to all peers"""
        message = {
            'type': 'new_transaction',
            'data': transaction.to_dict(),
            'sender': self.node_id
        }
        self.p2p.broadcast(message)

    def handle_peer_message(self, message: dict, peer_id: str):
        """Handle message from peer"""
        try:
            msg_type = message.get('type')
            sender = message.get('sender')
            
            if msg_type == 'new_transaction':
                self._handle_new_transaction(message['data'], sender)
            elif msg_type == 'new_block':
                self._handle_new_block(message['data'], sender)
            elif msg_type == 'peer_discovery':
                self._handle_peer_discovery(message['data'], sender)
            elif msg_type == 'chain_sync_request':
                self._handle_chain_sync_request(sender, peer_id)
            elif msg_type == 'chain_sync_response':
                self._handle_chain_sync_response(message['data'])
                
        except Exception as e:
            self.logger.error(f"Error handling peer message: {e}")

    def _handle_new_transaction(self, tx_data: dict, sender: str):
        """Handle new transaction from peer"""
        try:
            transaction = Transaction.from_dict(tx_data)
            if self.blockchain.add_transaction(transaction):
                self.logger.info(f"Received transaction from {sender}: {transaction.hash[:16]}...")
        except Exception as e:
            self.logger.error(f"Error handling new transaction: {e}")

    def _handle_new_block(self, block_data: dict, sender: str):
        """Handle new block from peer"""
        try:
            block = Block.from_dict(block_data)
            if self.blockchain.add_block(block):
                self.logger.info(f"Received block from {sender}: {block.hash[:16]}... (Height: {block.index})")
                # Update node state
                self._save_node_state()
        except Exception as e:
            self.logger.error(f"Error handling new block: {e}")

    def _handle_peer_discovery(self, peer_data: dict, sender: str):
        """Handle peer discovery message"""
        with self.peer_lock:
            self.peers[sender] = {
                'host': peer_data.get('host'),
                'port': peer_data.get('port'),
                'last_seen': time.time()
            }
        self.logger.info(f"Discovered peer: {sender}")
        self._save_node_state()

    def _handle_chain_sync_request(self, sender: str, peer_id: str):
        """Handle chain synchronization request"""
        try:
            blockchain_info = self.blockchain.get_blockchain_info()
            latest_block = self.blockchain.get_latest_block()
            
            response = {
                'type': 'chain_sync_response',
                'data': {
                    'blockchain_info': blockchain_info,
                    'latest_block': latest_block.to_dict() if latest_block else None
                },
                'sender': self.node_id
            }
            
            # Send response to specific peer
            self.p2p.send_to_peer(peer_id, response)
            
        except Exception as e:
            self.logger.error(f"Error handling chain sync request: {e}")

    def _handle_chain_sync_response(self, sync_data: dict):
        """Handle chain synchronization response"""
        try:
            remote_info = sync_data.get('blockchain_info', {})
            remote_height = remote_info.get('height', 0)
            
            local_info = self.blockchain.get_blockchain_info()
            local_height = local_info.get('height', 0)
            
            if remote_height > local_height:
                self.logger.info(f"Remote chain longer ({remote_height} vs {local_height}), syncing...")
                # TODO: Implement full chain sync
                
        except Exception as e:
            self.logger.error(f"Error handling chain sync response: {e}")

    def add_peer(self, peer_host: str, peer_port: int, peer_id: str = None):
        """Add a peer to connect to"""
        if peer_id is None:
            peer_id = f"{peer_host}:{peer_port}"
            
        with self.peer_lock:
            self.peers[peer_id] = {
                'host': peer_host,
                'port': peer_port,
                'last_seen': time.time()
            }
        
        # Connect to peer
        self.p2p.connect_to_peer(peer_host, peer_port)
        self._save_node_state()
        
        self.logger.info(f"Added peer: {peer_id}")

    def get_node_info(self) -> dict:
        """Get node information"""
        return {
            'node_id': self.node_id,
            'host': self.host,
            'port': self.port,
            'is_validator': self.is_validator,
            'is_running': self.is_running,
            'peer_count': len(self.peers),
            'blockchain_info': self.blockchain.get_blockchain_info()
        }

    def get_balance(self, address: str) -> float:
        """Get account balance"""
        return self.blockchain.get_balance(address)

    def get_transaction(self, tx_hash: str) -> Optional[dict]:
        """Get transaction by hash"""
        tx_data = self.blockchain.db.get_transaction(tx_hash)
        return tx_data

    def get_block(self, block_hash: str) -> Optional[dict]:
        """Get block by hash"""
        block = self.blockchain.get_block_by_hash(block_hash)
        return block.to_dict() if block else None

    def __del__(self):
        """Cleanup when node is destroyed"""
        if hasattr(self, 'is_running') and self.is_running:
            self.stop()
"""
DinariBlockchain Network Layer
=============================
P2P networking and node communication for DinariBlockchain
"""

import asyncio
import json
import logging
import socket
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class NetworkMessage:
    """Network message structure"""
    message_type: str
    data: Dict[str, Any]
    sender_id: str
    timestamp: int
    signature: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkMessage':
        return cls(**data)

@dataclass
class PeerInfo:
    """Peer information"""
    peer_id: str
    host: str
    port: int
    last_seen: int
    version: str = "1.0.0"
    is_validator: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class P2PNode:
    """
    P2P Node for DinariBlockchain network communication
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8333, node_id: str = None):
        self.host = host
        self.port = port
        self.node_id = node_id or self._generate_node_id()
        self.logger = logging.getLogger(f"P2P-{self.node_id}")
        
        # Network state
        self.is_running = False
        self.peers: Dict[str, PeerInfo] = {}
        self.connections: Dict[str, Any] = {}  # Active connections
        self.message_handlers: Dict[str, Callable] = {}
        
        # Server components
        self.server_socket = None
        self.server_thread = None
        
        # Default message handlers
        self._register_default_handlers()
        
    def _generate_node_id(self) -> str:
        """Generate unique node ID"""
        return hashlib.sha256(f"{self.host}:{self.port}:{time.time()}".encode()).hexdigest()[:16]
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        self.message_handlers.update({
            "ping": self._handle_ping,
            "pong": self._handle_pong,
            "peer_discovery": self._handle_peer_discovery,
            "peer_list": self._handle_peer_list,
            "block_announcement": self._handle_block_announcement,
            "transaction_broadcast": self._handle_transaction_broadcast,
            "sync_request": self._handle_sync_request,
            "sync_response": self._handle_sync_response
        })
    
    def start(self) -> bool:
        """Start the P2P server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            
            self.is_running = True
            self.server_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.server_thread.start()
            
            self.logger.info(f"P2P server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start P2P server: {e}")
            return False
    
    def stop(self):
        """Stop the P2P server"""
        self.is_running = False
        
        # Close all connections
        for conn in self.connections.values():
            try:
                conn.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.logger.info("P2P server stopped")
    
    def _accept_connections(self):
        """Accept incoming connections"""
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                self.logger.info(f"New connection from {address}")
                
                # Handle connection in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Error accepting connection: {e}")
    
    def _handle_client(self, client_socket, address):
        """Handle individual client connection"""
        peer_id = f"{address[0]}:{address[1]}"
        self.connections[peer_id] = client_socket
        
        try:
            while self.is_running:
                # Receive data
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    message_data = json.loads(data.decode())
                    message = NetworkMessage.from_dict(message_data)
                    self._process_message(message, peer_id)
                    
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON from {peer_id}")
                except Exception as e:
                    self.logger.error(f"Error processing message from {peer_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Connection error with {peer_id}: {e}")
        finally:
            # Clean up connection
            client_socket.close()
            if peer_id in self.connections:
                del self.connections[peer_id]
            self.logger.info(f"Connection closed: {peer_id}")
    
    def _process_message(self, message: NetworkMessage, sender_peer: str):
        """Process incoming message"""
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                handler(message, sender_peer)
            except Exception as e:
                self.logger.error(f"Error handling {message.message_type} from {sender_peer}: {e}")
        else:
            self.logger.warning(f"Unknown message type: {message.message_type} from {sender_peer}")
    
    def send_message(self, peer_id: str, message: NetworkMessage) -> bool:
        """Send message to specific peer"""
        if peer_id not in self.connections:
            self.logger.warning(f"No connection to peer {peer_id}")
            return False
        
        try:
            message_json = json.dumps(message.to_dict())
            self.connections[peer_id].send(message_json.encode())
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message to {peer_id}: {e}")
            return False
    
    def broadcast_message(self, message: NetworkMessage) -> int:
        """Broadcast message to all connected peers"""
        success_count = 0
        
        for peer_id in list(self.connections.keys()):
            if self.send_message(peer_id, message):
                success_count += 1
        
        self.logger.info(f"Broadcast {message.message_type} to {success_count} peers")
        return success_count
    
    def connect_to_peer(self, host: str, port: int) -> bool:
        """Connect to a peer"""
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((host, port))
            
            peer_id = f"{host}:{port}"
            self.connections[peer_id] = peer_socket
            
            # Add peer info
            self.peers[peer_id] = PeerInfo(
                peer_id=peer_id,
                host=host,
                port=port,
                last_seen=int(time.time())
            )
            
            # Start handling this connection
            client_thread = threading.Thread(
                target=self._handle_client,
                args=(peer_socket, (host, port)),
                daemon=True
            )
            client_thread.start()
            
            # Send peer discovery message
            discovery_message = NetworkMessage(
                message_type="peer_discovery",
                data={"node_id": self.node_id, "version": "1.0.0"},
                sender_id=self.node_id,
                timestamp=int(time.time())
            )
            self.send_message(peer_id, discovery_message)
            
            self.logger.info(f"Connected to peer {peer_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {host}:{port} - {e}")
            return False
    
    def _safely_serialize(self, data: Any) -> Any:
        """Safely serialize data (only basic types)"""
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        elif isinstance(data, dict):
            return {k: self._safely_serialize(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._safely_serialize(item) for item in data]
        else:
            return str(data)
    
    # Default message handlers
    def _handle_ping(self, message: NetworkMessage, sender_peer: str):
        """Handle ping message"""
        pong_message = NetworkMessage(
            message_type="pong",
            data={"timestamp": int(time.time())},
            sender_id=self.node_id,
            timestamp=int(time.time())
        )
        self.send_message(sender_peer, pong_message)
    
    def _handle_pong(self, message: NetworkMessage, sender_peer: str):
        """Handle pong message"""
        if sender_peer in self.peers:
            self.peers[sender_peer].last_seen = int(time.time())
    
    def _handle_peer_discovery(self, message: NetworkMessage, sender_peer: str):
        """Handle peer discovery"""
        peer_data = message.data
        self.peers[sender_peer] = PeerInfo(
            peer_id=peer_data.get("node_id", sender_peer),
            host=sender_peer.split(":")[0],
            port=int(sender_peer.split(":")[1]),
            last_seen=int(time.time()),
            version=peer_data.get("version", "unknown")
        )
        
        # Send back our peer list
        peer_list_message = NetworkMessage(
            message_type="peer_list",
            data={"peers": [peer.to_dict() for peer in self.peers.values()]},
            sender_id=self.node_id,
            timestamp=int(time.time())
        )
        self.send_message(sender_peer, peer_list_message)
    
    def _handle_peer_list(self, message: NetworkMessage, sender_peer: str):
        """Handle peer list"""
        peers_data = message.data.get("peers", [])
        for peer_data in peers_data:
            peer_info = PeerInfo(**peer_data)
            peer_id = f"{peer_info.host}:{peer_info.port}"
            
            # Don't add ourselves
            if peer_id != f"{self.host}:{self.port}":
                self.peers[peer_id] = peer_info
    
    def _handle_block_announcement(self, message: NetworkMessage, sender_peer: str):
        """Handle block announcement"""
        self.logger.info(f"Block announcement from {sender_peer}: {message.data}")
    
    def _handle_transaction_broadcast(self, message: NetworkMessage, sender_peer: str):
        """Handle transaction broadcast"""
        self.logger.info(f"Transaction broadcast from {sender_peer}: {message.data}")
    
    def _handle_sync_request(self, message: NetworkMessage, sender_peer: str):
        """Handle sync request"""
        self.logger.info(f"Sync request from {sender_peer}")
        # Implementation would depend on blockchain integration
    
    def _handle_sync_response(self, message: NetworkMessage, sender_peer: str):
        """Handle sync response"""
        self.logger.info(f"Sync response from {sender_peer}")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register custom message handler"""
        self.message_handlers[message_type] = handler
    
    def get_peer_count(self) -> int:
        """Get number of connected peers"""
        return len(self.connections)
    
    def get_peers_info(self) -> List[Dict[str, Any]]:
        """Get information about all peers"""
        return [peer.to_dict() for peer in self.peers.values()]

class DinariNode:
    """
    High-level DinariBlockchain node with integrated P2P networking
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8333, node_id: str = None):
        self.node_id = node_id or f"dinari_node_{int(time.time())}"
        self.logger = logging.getLogger(f"DinariNode-{self.node_id}")
        
        # Initialize P2P networking
        self.p2p_node = P2PNode(host, port, self.node_id)
        
        # Node state
        self.is_validator = False
        self.blockchain = None  # Will be set externally
        self.sync_in_progress = False
        
        # Register blockchain-specific message handlers
        self._register_blockchain_handlers()
    
    def _register_blockchain_handlers(self):
        """Register blockchain-specific message handlers"""
        self.p2p_node.register_message_handler("new_block", self._handle_new_block)
        self.p2p_node.register_message_handler("new_transaction", self._handle_new_transaction)
        self.p2p_node.register_message_handler("block_request", self._handle_block_request)
        self.p2p_node.register_message_handler("chain_sync", self._handle_chain_sync)
    
    def start(self, is_validator: bool = False) -> bool:
        """Start the Dinari node"""
        self.is_validator = is_validator
        
        if self.p2p_node.start():
            self.logger.info(f"DinariNode {self.node_id} started as {'validator' if is_validator else 'regular node'}")
            return True
        else:
            self.logger.error("Failed to start DinariNode")
            return False
    
    def stop(self):
        """Stop the Dinari node"""
        self.p2p_node.stop()
        self.logger.info(f"DinariNode {self.node_id} stopped")
    
    def connect_to_network(self, bootstrap_peers: List[tuple]) -> int:
        """Connect to the Dinari network using bootstrap peers"""
        connected_count = 0
        
        for host, port in bootstrap_peers:
            if self.p2p_node.connect_to_peer(host, port):
                connected_count += 1
        
        self.logger.info(f"Connected to {connected_count}/{len(bootstrap_peers)} bootstrap peers")
        return connected_count
    
    def broadcast_block(self, block_data: Dict[str, Any]):
        """Broadcast a new block to the network"""
        message = NetworkMessage(
            message_type="new_block",
            data={"block": block_data},
            sender_id=self.node_id,
            timestamp=int(time.time())
        )
        
        count = self.p2p_node.broadcast_message(message)
        self.logger.info(f"Broadcast block to {count} peers")
    
    def broadcast_transaction(self, tx_data: Dict[str, Any]):
        """Broadcast a new transaction to the network"""
        message = NetworkMessage(
            message_type="new_transaction",
            data={"transaction": tx_data},
            sender_id=self.node_id,
            timestamp=int(time.time())
        )
        
        count = self.p2p_node.broadcast_message(message)
        self.logger.info(f"Broadcast transaction to {count} peers")
    
    def _handle_new_block(self, message: NetworkMessage, sender_peer: str):
        """Handle new block from network"""
        block_data = message.data.get("block")
        if block_data and self.blockchain:
            self.logger.info(f"Received new block from {sender_peer}")
            # Here you would validate and add the block to your blockchain
            # self.blockchain.add_block_from_network(block_data)
    
    def _handle_new_transaction(self, message: NetworkMessage, sender_peer: str):
        """Handle new transaction from network"""
        tx_data = message.data.get("transaction")
        if tx_data and self.blockchain:
            self.logger.info(f"Received new transaction from {sender_peer}")
            # Here you would validate and add the transaction to your mempool
            # self.blockchain.add_transaction_from_network(tx_data)
    
    def _handle_block_request(self, message: NetworkMessage, sender_peer: str):
        """Handle block request from peer"""
        block_hash = message.data.get("block_hash")
        if block_hash and self.blockchain:
            # Get block from blockchain and send back
            block_data = self.blockchain.get_block_by_hash(block_hash)
            if block_data:
                response = NetworkMessage(
                    message_type="block_response",
                    data={"block": block_data},
                    sender_id=self.node_id,
                    timestamp=int(time.time())
                )
                self.p2p_node.send_message(sender_peer, response)
    
    def _handle_chain_sync(self, message: NetworkMessage, sender_peer: str):
        """Handle chain synchronization request"""
        if not self.sync_in_progress and self.blockchain:
            self.sync_in_progress = True
            self.logger.info(f"Starting chain sync with {sender_peer}")
            # Implementation would depend on your blockchain's sync strategy
            self.sync_in_progress = False
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        return {
            "node_id": self.node_id,
            "is_validator": self.is_validator,
            "connected_peers": self.p2p_node.get_peer_count(),
            "peers_info": self.p2p_node.get_peers_info(),
            "sync_in_progress": self.sync_in_progress
        }
    
    def set_blockchain(self, blockchain):
        """Set the blockchain instance"""
        self.blockchain = blockchain
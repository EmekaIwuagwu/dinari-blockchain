#!/usr/bin/env python3
"""
DinariBlockchain P2P Network Implementation
Dinari/network.py - Peer-to-peer networking for blockchain nodes
"""

import socket
import threading
import time
import json
import pickle
import hashlib
from typing import Dict, List, Set, Optional, Tuple, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from queue import Queue, Empty

# Import blockchain components
from .blockchain import Transaction, Block

class MessageType(Enum):
    """Network message types"""
    HELLO = "hello"
    PING = "ping" 
    PONG = "pong"
    PEERS_REQUEST = "peers_request"
    PEERS_RESPONSE = "peers_response"
    TRANSACTION = "transaction"
    BLOCK = "block"
    BLOCK_REQUEST = "block_request"
    BLOCK_RESPONSE = "block_response"
    CHAIN_REQUEST = "chain_request"
    CHAIN_RESPONSE = "chain_response"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    DISCONNECT = "disconnect"

@dataclass
class NetworkMessage:
    """P2P network message structure"""
    message_type: MessageType
    sender_id: str
    data: Any
    timestamp: float = None
    message_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.message_id is None:
            # Generate unique message ID
            content = f"{self.message_type.value}{self.sender_id}{self.timestamp}"
            self.message_id = hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_bytes(self) -> bytes:
        """Serialize message for network transmission"""
        msg_dict = {
            'message_type': self.message_type.value,
            'sender_id': self.sender_id,
            'data': self._safe_serialize(self.data),
            'timestamp': self.timestamp,
            'message_id': self.message_id
        }
        return json.dumps(msg_dict).encode('utf-8')
    
        def _safe_serialize(self, data):
        """Safely serialize data (only basic types)"""
        if isinstance(data, (dict, list, str, int, float, bool, type(None))):
            return data
        elif hasattr(data, 'to_dict'):
            return data.to_dict()
        else:
            return str(data)  # Convert unknown types to string
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'NetworkMessage':
        """Deserialize message from network data"""
        try:
            msg_dict = json.loads(data.decode('utf-8'))
            return cls(
                message_type=MessageType(msg_dict['message_type']),
                sender_id=msg_dict['sender_id'],
                data=msg_dict['data'],
                timestamp=msg_dict.get('timestamp'),
                message_id=msg_dict.get('message_id')
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Invalid message format: {e}")

@dataclass
class PeerInfo:
    """Information about a network peer"""
    peer_id: str
    host: str
    port: int
    connected_at: float
    last_seen: float
    is_validator: bool = False
    version: str = "1.0.0"
    chain_height: int = 0
    latency: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @property
    def address(self) -> str:
        """Get peer network address"""
        return f"{self.host}:{self.port}"

class NetworkStats:
    """Network statistics tracking"""
    
    def __init__(self):
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.connections_made = 0
        self.connections_dropped = 0
        self.start_time = time.time()
        self.message_types = {msg_type: 0 for msg_type in MessageType}
    
    def record_message_sent(self, message: NetworkMessage, size: int):
        """Record sent message statistics"""
        self.messages_sent += 1
        self.bytes_sent += size
        self.message_types[message.message_type] += 1
    
    def record_message_received(self, message: NetworkMessage, size: int):
        """Record received message statistics"""
        self.messages_received += 1
        self.bytes_received += size
        self.message_types[message.message_type] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        uptime = time.time() - self.start_time
        return {
            'uptime_seconds': uptime,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'connections_made': self.connections_made,
            'connections_dropped': self.connections_dropped,
            'messages_per_second': (self.messages_sent + self.messages_received) / max(1, uptime),
            'message_types': {msg_type.value: count for msg_type, count in self.message_types.items()}
        }

class P2PConnection:
    """Manages a single peer connection"""
    
    def __init__(self, socket: socket.socket, peer_info: PeerInfo, network_manager):
        self.socket = socket
        self.peer_info = peer_info
        self.network_manager = network_manager
        self.running = True
        self.message_queue = Queue()
        self.last_ping = time.time()
        
        # Setup logging
        self.logger = logging.getLogger(f"P2PConnection-{peer_info.peer_id}")
        
        # Start connection threads
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        
        self.receive_thread.start()
        self.send_thread.start()
    
    def _receive_loop(self):
        """Main receive loop for this connection"""
        buffer = b''
        
        while self.running:
            try:
                # Receive data
                data = self.socket.recv(8192)
                if not data:
                    break
                
                buffer += data
                
                # Process complete messages
                while len(buffer) >= 4:  # At least message length header
                    try:
                        # Simple length-prefixed protocol
                        msg_length = int.from_bytes(buffer[:4], byteorder='big')
                        
                        if len(buffer) >= 4 + msg_length:
                            # Extract message
                            msg_data = buffer[4:4 + msg_length]
                            buffer = buffer[4 + msg_length:]
                            
                            # Process message
                            self._process_received_message(msg_data)
                        else:
                            break  # Wait for more data
                            
                    except Exception as e:
                        self.logger.error(f"Error processing message: {e}")
                        break
                        
            except Exception as e:
                if self.running:
                    self.logger.error(f"Receive error: {e}")
                break
        
        self._cleanup()
    
    def _send_loop(self):
        """Main send loop for this connection"""
        while self.running:
            try:
                # Get message from queue (with timeout)
                message = self.message_queue.get(timeout=1.0)
                
                if message is None:  # Shutdown signal
                    break
                
                # Serialize message
                msg_data = message.to_bytes()
                msg_length = len(msg_data)
                
                # Send with length prefix
                length_header = msg_length.to_bytes(4, byteorder='big')
                self.socket.send(length_header + msg_data)
                
                # Update stats
                self.network_manager.stats.record_message_sent(message, len(length_header) + len(msg_data))
                
            except Empty:
                continue  # Timeout, check if still running
            except Exception as e:
                if self.running:
                    self.logger.error(f"Send error: {e}")
                break
        
        self._cleanup()
    
    def _process_received_message(self, msg_data: bytes):
        """Process received message"""
        try:
            message = NetworkMessage.from_bytes(msg_data)
            
            # Update peer info
            self.peer_info.last_seen = time.time()
            
            # Update stats
            self.network_manager.stats.record_message_received(message, len(msg_data))
            
            # Handle ping/pong internally
            if message.message_type == MessageType.PING:
                self._send_pong()
                return
            elif message.message_type == MessageType.PONG:
                self.last_ping = time.time()
                return
            
            # Forward to network manager
            self.network_manager._handle_peer_message(message, self)
            
        except Exception as e:
            self.logger.error(f"Error processing received message: {e}")
    
    def send_message(self, message: NetworkMessage):
        """Send message to peer"""
        if self.running:
            self.message_queue.put(message)
    
    def _send_pong(self):
        """Send pong response to ping"""
        pong_msg = NetworkMessage(
            MessageType.PONG,
            self.network_manager.node_id,
            {'timestamp': time.time()}
        )
        self.send_message(pong_msg)
    
    def ping(self):
        """Send ping to peer"""
        ping_msg = NetworkMessage(
            MessageType.PING,
            self.network_manager.node_id,
            {'timestamp': time.time()}
        )
        self.send_message(ping_msg)
        self.last_ping = time.time()
    
    def disconnect(self):
        """Disconnect from peer"""
        self.running = False
        self.message_queue.put(None)  # Shutdown signal
        
        # Send disconnect message
        disconnect_msg = NetworkMessage(
            MessageType.DISCONNECT,
            self.network_manager.node_id,
            {'reason': 'Normal disconnect'}
        )
        try:
            self.send_message(disconnect_msg)
            time.sleep(0.1)  # Give time to send
        except:
            pass
    
    def _cleanup(self):
        """Clean up connection resources"""
        self.running = False
        try:
            self.socket.close()
        except:
            pass
        
        # Notify network manager
        self.network_manager._peer_disconnected(self.peer_info.peer_id)

class P2PNetworkManager:
    """Main P2P network manager for Dinari nodes"""
    
    def __init__(self, node_id: str, host: str = "127.0.0.1", port: int = 8333):
        self.node_id = node_id
        self.host = host
        self.port = port
        
        # Network state
        self.peers: Dict[str, P2PConnection] = {}
        self.peer_info: Dict[str, PeerInfo] = {}
        self.known_peers: Set[str] = set()  # Addresses we've heard about
        self.blacklisted_peers: Set[str] = set()
        
        # Server socket
        self.server_socket = None
        self.running = False
        
        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # Network configuration
        self.max_peers = 50
        self.connection_timeout = 10
        self.ping_interval = 60  # seconds
        self.peer_timeout = 300  # 5 minutes
        
        # Statistics
        self.stats = NetworkStats()
        
        # Setup default message handlers
        self._setup_default_handlers()
        
        # Setup logging
        self.logger = logging.getLogger(f"P2PNetwork-{node_id}")
        
        # Start background tasks
        self.maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self.maintenance_thread.start()
    
    def _setup_default_handlers(self):
        """Setup default message handlers"""
        self.message_handlers[MessageType.HELLO] = self._handle_hello
        self.message_handlers[MessageType.PEERS_REQUEST] = self._handle_peers_request
        self.message_handlers[MessageType.PEERS_RESPONSE] = self._handle_peers_response
    
    def set_message_handler(self, message_type: MessageType, handler: Callable):
        """Set custom message handler"""
        self.message_handlers[message_type] = handler
    
    def start_server(self):
        """Start P2P server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(20)
            self.running = True
            
            self.logger.info(f"P2P server started on {self.host}:{self.port}")
            
            # Start accepting connections
            accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            accept_thread.start()
            
        except Exception as e:
            self.logger.error(f"Failed to start P2P server: {e}")
            raise
    
    def _accept_connections(self):
        """Accept incoming connections"""
        while self.running:
            try:
                if self.server_socket:
                    client_socket, address = self.server_socket.accept()
                    
                    # Check connection limits
                    if len(self.peers) >= self.max_peers:
                        client_socket.close()
                        continue
                    
                    # Check blacklist
                    peer_address = f"{address[0]}:{address[1]}"
                    if peer_address in self.blacklisted_peers:
                        client_socket.close()
                        continue
                    
                    self.logger.info(f"Incoming connection from {address}")
                    
                    # Create peer connection (peer_id will be set after hello)
                    temp_peer_id = f"temp_{address[0]}_{address[1]}_{int(time.time())}"
                    peer_info = PeerInfo(
                        peer_id=temp_peer_id,
                        host=address[0],
                        port=address[1],
                        connected_at=time.time(),
                        last_seen=time.time()
                    )
                    
                    connection = P2PConnection(client_socket, peer_info, self)
                    self.peers[temp_peer_id] = connection
                    self.peer_info[temp_peer_id] = peer_info
                    
                    self.stats.connections_made += 1
                    
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error accepting connection: {e}")
    
    def connect_to_peer(self, host: str, port: int) -> bool:
        """Connect to a peer"""
        peer_address = f"{host}:{port}"
        
        # Check if already connected
        for peer_info in self.peer_info.values():
            if peer_info.address == peer_address:
                return True  # Already connected
        
        # Check blacklist
        if peer_address in self.blacklisted_peers:
            return False
        
        try:
            # Create connection
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.settimeout(self.connection_timeout)
            peer_socket.connect((host, port))
            
            # Create peer info
            peer_id = f"outbound_{host}_{port}_{int(time.time())}"
            peer_info = PeerInfo(
                peer_id=peer_id,
                host=host,
                port=port,
                connected_at=time.time(),
                last_seen=time.time()
            )
            
            # Create connection
            connection = P2PConnection(peer_socket, peer_info, self)
            self.peers[peer_id] = connection
            self.peer_info[peer_id] = peer_info
            
            # Send hello message
            self._send_hello(connection)
            
            self.logger.info(f"Connected to peer: {peer_address}")
            self.stats.connections_made += 1
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {peer_address}: {e}")
            return False
    
    def disconnect_from_peer(self, peer_id: str):
        """Disconnect from a peer"""
        if peer_id in self.peers:
            self.peers[peer_id].disconnect()
    
    def broadcast_message(self, message: NetworkMessage, exclude_peer: str = None):
        """Broadcast message to all connected peers"""
        for peer_id, connection in self.peers.items():
            if peer_id != exclude_peer:
                connection.send_message(message)
    
    def send_to_peer(self, peer_id: str, message: NetworkMessage) -> bool:
        """Send message to specific peer"""
        if peer_id in self.peers:
            self.peers[peer_id].send_message(message)
            return True
        return False
    
    def _handle_peer_message(self, message: NetworkMessage, connection: P2PConnection):
        """Handle message from peer"""
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                handler(message, connection)
            except Exception as e:
                self.logger.error(f"Error in message handler for {message.message_type}: {e}")
        else:
            self.logger.debug(f"No handler for message type: {message.message_type}")
    
    def _send_hello(self, connection: P2PConnection):
        """Send hello message to peer"""
        hello_msg = NetworkMessage(
            MessageType.HELLO,
            self.node_id,
            {
                'node_id': self.node_id,
                'version': '1.0.0',
                'chain_height': 0,  # Should be set by blockchain
                'is_validator': False  # Should be set by node
            }
        )
        connection.send_message(hello_msg)
    
    def _handle_hello(self, message: NetworkMessage, connection: P2PConnection):
        """Handle hello message"""
        # Update peer info with real node ID
        old_peer_id = connection.peer_info.peer_id
        new_peer_id = message.data.get('node_id', old_peer_id)
        
        if old_peer_id != new_peer_id:
            # Update peer mappings
            connection.peer_info.peer_id = new_peer_id
            connection.peer_info.version = message.data.get('version', '1.0.0')
            connection.peer_info.is_validator = message.data.get('is_validator', False)
            connection.peer_info.chain_height = message.data.get('chain_height', 0)
            
            # Update dictionaries
            del self.peers[old_peer_id]
            del self.peer_info[old_peer_id]
            
            self.peers[new_peer_id] = connection
            self.peer_info[new_peer_id] = connection.peer_info
        
        self.logger.info(f"Received hello from {new_peer_id}")
        
        # Send hello back if we initiated the connection
        if old_peer_id.startswith('outbound_'):
            self._send_hello(connection)
    
    def _handle_peers_request(self, message: NetworkMessage, connection: P2PConnection):
        """Handle request for peer list"""
        peer_list = []
        for peer_info in self.peer_info.values():
            if peer_info.peer_id != message.sender_id:  # Don't send requester back to themselves
                peer_list.append({
                    'host': peer_info.host,
                    'port': peer_info.port,
                    'peer_id': peer_info.peer_id
                })
        
        response = NetworkMessage(
            MessageType.PEERS_RESPONSE,
            self.node_id,
            {'peers': peer_list[:20]}  # Limit to 20 peers
        )
        connection.send_message(response)
    
    def _handle_peers_response(self, message: NetworkMessage, connection: P2PConnection):
        """Handle peer list response"""
        peers = message.data.get('peers', [])
        for peer_data in peers:
            peer_address = f"{peer_data['host']}:{peer_data['port']}"
            self.known_peers.add(peer_address)
    
    def request_peers(self):
        """Request peer list from connected peers"""
        request = NetworkMessage(
            MessageType.PEERS_REQUEST,
            self.node_id,
            {}
        )
        self.broadcast_message(request)
    
    def _maintenance_loop(self):
        """Background maintenance tasks"""
        last_ping = 0
        last_cleanup = 0
        
        while True:
            try:
                current_time = time.time()
                
                # Ping peers periodically
                if current_time - last_ping > self.ping_interval:
                    self._ping_all_peers()
                    last_ping = current_time
                
                # Cleanup inactive peers
                if current_time - last_cleanup > 60:  # Every minute
                    self._cleanup_inactive_peers()
                    last_cleanup = current_time
                
                time.sleep(10)  # Run every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Maintenance loop error: {e}")
    
    def _ping_all_peers(self):
        """Send ping to all connected peers"""
        for connection in self.peers.values():
            connection.ping()
    
    def _cleanup_inactive_peers(self):
        """Remove inactive peers"""
        current_time = time.time()
        inactive_peers = []
        
        for peer_id, peer_info in self.peer_info.items():
            if current_time - peer_info.last_seen > self.peer_timeout:
                inactive_peers.append(peer_id)
        
        for peer_id in inactive_peers:
            self.logger.info(f"Removing inactive peer: {peer_id}")
            self.disconnect_from_peer(peer_id)
    
    def _peer_disconnected(self, peer_id: str):
        """Handle peer disconnection"""
        if peer_id in self.peers:
            del self.peers[peer_id]
        if peer_id in self.peer_info:
            del self.peer_info[peer_id]
        
        self.stats.connections_dropped += 1
        self.logger.info(f"Peer disconnected: {peer_id}")
    
    def get_connected_peers(self) -> List[PeerInfo]:
        """Get list of connected peers"""
        return list(self.peer_info.values())
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        stats = self.stats.get_stats()
        stats.update({
            'connected_peers': len(self.peers),
            'known_peers': len(self.known_peers),
            'blacklisted_peers': len(self.blacklisted_peers)
        })
        return stats
    
    def blacklist_peer(self, address: str, reason: str = ""):
        """Blacklist a peer address"""
        self.blacklisted_peers.add(address)
        self.logger.warning(f"Peer blacklisted: {address} - {reason}")
    
    def stop(self):
        """Stop P2P networking"""
        self.running = False
        
        # Disconnect all peers
        for peer_id in list(self.peers.keys()):
            self.disconnect_from_peer(peer_id)
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info("P2P network stopped")

# Example usage
if __name__ == "__main__":
    import argparse
    
    # Simple P2P network test
    parser = argparse.ArgumentParser(description="DinariBlockchain P2P Network Test")
    parser.add_argument("--node-id", required=True, help="Node ID")
    parser.add_argument("--port", type=int, default=8333, help="Port number")
    parser.add_argument("--connect", help="Peer to connect to (host:port)")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create network manager
    network = P2PNetworkManager(args.node_id, port=args.port)
    
    # Start server
    network.start_server()
    
    # Connect to peer if specified
    if args.connect:
        host, port = args.connect.split(':')
        network.connect_to_peer(host, int(port))
    
    # Keep running and show stats
    try:
        while True:
            time.sleep(30)
            stats = network.get_network_stats()
            print(f"Network Stats: {len(network.peers)} peers, "
                  f"{stats['messages_sent']} sent, {stats['messages_received']} received")
    
    except KeyboardInterrupt:
        print("\nStopping network...")
        network.stop()

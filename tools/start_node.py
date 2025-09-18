#!/usr/bin/env python3
"""
DinariBlockchain Node Launcher
tools/start_node.py - Script to start and manage blockchain nodes
"""

import sys
import os
import argparse
import subprocess
import time
import json
import signal
from typing import List, Dict, Any
import threading

# Add parent directory to path to import Dinari modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Dinari.node import DinariNode

class NodeLauncher:
    """Manages multiple blockchain nodes"""
    
    def __init__(self, genesis_file: str = "genesis.json", data_dir: str = "data"):
        self.genesis_file = genesis_file
        self.data_dir = data_dir
        self.running_nodes: Dict[str, DinariNode] = {}
        self.node_threads: Dict[str, threading.Thread] = {}
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        print(f"🚀 DinariBlockchain Node Launcher initialized")
        print(f"   Genesis file: {genesis_file}")
        print(f"   Data directory: {data_dir}")
    
    def start_single_node(self, node_id: str, host: str = "127.0.0.1", 
                         port: int = 8333, connect_to_peers: List[tuple] = None):
        """Start a single blockchain node"""
        
        if node_id in self.running_nodes:
            print(f"❌ Node {node_id} is already running")
            return False
        
        try:
            print(f"🚀 Starting node {node_id} on {host}:{port}...")
            
            # Create node
            node = DinariNode(node_id, host, port, self.genesis_file, self.data_dir)
            
            # Start node
            node.start()
            
            # Connect to peers if specified
            if connect_to_peers:
                print(f"🔗 Connecting to {len(connect_to_peers)} peers...")
                node.connect_to_peers(connect_to_peers)
                time.sleep(2)  # Allow time for connections
            
            # Store node
            self.running_nodes[node_id] = node
            
            print(f"✅ Node {node_id} started successfully")
            print(f"   Status: {'Validator' if node.is_validator else 'Regular Node'}")
            print(f"   Address: {host}:{port}")
            print(f"   Peers: {len(node.network.peers)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start node {node_id}: {e}")
            return False
    
    def stop_node(self, node_id: str):
        """Stop a running node"""
        if node_id not in self.running_nodes:
            print(f"❌ Node {node_id} is not running")
            return False
        
        try:
            print(f"🛑 Stopping node {node_id}...")
            node = self.running_nodes[node_id]
            node.stop()
            del self.running_nodes[node_id]
            print(f"✅ Node {node_id} stopped successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop node {node_id}: {e}")
            return False
    
    def stop_all_nodes(self):
        """Stop all running nodes"""
        print(f"🛑 Stopping all {len(self.running_nodes)} nodes...")
        
        for node_id in list(self.running_nodes.keys()):
            self.stop_node(node_id)
        
        print("✅ All nodes stopped")
    
    def get_node_status(self, node_id: str) -> Dict[str, Any]:
        """Get status of a specific node"""
        if node_id not in self.running_nodes:
            return {"error": f"Node {node_id} not running"}
        
        return self.running_nodes[node_id].get_node_status()
    
    def list_running_nodes(self):
        """List all running nodes with their status"""
        if not self.running_nodes:
            print("📋 No nodes currently running")
            return
        
        print(f"📋 Running Nodes ({len(self.running_nodes)}):")
        print("-" * 80)
        
        for node_id, node in self.running_nodes.items():
            status = node.get_node_status()
            stats = status['blockchain_stats']
            
            print(f"🔹 {node_id}")
            print(f"   Address: {status['host']}:{status['port']}")
            print(f"   Type: {'Validator' if status['is_validator'] else 'Regular Node'}")
            print(f"   Peers: {status['peers_connected']}")
            print(f"   Blocks: {stats['total_blocks']}")
            print(f"   Transactions: {stats['total_transactions']}")
            print(f"   Pending: {stats['pending_transactions']}")
            print()
    
    def start_test_network(self, num_nodes: int = 3):
        """Start a test network with multiple nodes"""
        print(f"🌐 Starting test network with {num_nodes} nodes...")
        
        # Load genesis config to get validators
        try:
            with open(self.genesis_file, 'r') as f:
                genesis_config = json.load(f)
            validators = genesis_config.get('consensus', {}).get('validators', [])
        except:
            validators = [f"node_{8333 + i}" for i in range(num_nodes)]
        
        # Start nodes
        peer_addresses = []
        base_port = 8333
        
        for i in range(num_nodes):
            node_id = f"node_{base_port + i}"
            port = base_port + i
            host = "127.0.0.1"
            
            # Collect peer addresses (exclude self)
            connect_peers = [(h, p) for h, p in peer_addresses if p != port]
            
            # Start node
            if self.start_single_node(node_id, host, port, connect_peers):
                peer_addresses.append((host, port))
                time.sleep(1)  # Stagger node starts
        
        print(f"✅ Test network started with {len(self.running_nodes)} nodes")
        
        # Wait for network to stabilize
        print("⏳ Waiting for network to stabilize...")
        time.sleep(5)
        
        # Show network status
        self.show_network_status()
    
    def show_network_status(self):
        """Show status of the entire network"""
        if not self.running_nodes:
            print("📊 No network active")
            return
        
        print("\n📊 NETWORK STATUS")
        print("=" * 60)
        
        total_blocks = 0
        total_transactions = 0
        total_pending = 0
        
        for node_id, node in self.running_nodes.items():
            stats = node.blockchain.get_stats()
            total_blocks = max(total_blocks, stats['total_blocks'])
            total_transactions = max(total_transactions, stats['total_transactions'])
            total_pending += stats['pending_transactions']
        
        print(f"🌐 Network Overview:")
        print(f"   Total Nodes: {len(self.running_nodes)}")
        print(f"   Blockchain Height: {total_blocks}")
        print(f"   Total Transactions: {total_transactions}")
        print(f"   Pending Transactions: {total_pending}")
        
        # Show individual node details
        self.list_running_nodes()
    
    def send_test_transaction(self, from_addr: str = "treasury", to_addr: str = "alice", 
                             amount: str = "100", fee: str = "0.1"):
        """Send a test transaction through the network"""
        if not self.running_nodes:
            print("❌ No nodes running to send transaction")
            return False
        
        # Use the first available node
        node = next(iter(self.running_nodes.values()))
        
        print(f"💸 Sending transaction: {from_addr} → {to_addr} ({amount} DNMR)")
        
        success = node.submit_transaction(from_addr, to_addr, amount, fee)
        
        if success:
            print("✅ Transaction submitted successfully")
            return True
        else:
            print("❌ Transaction failed")
            return False
    
    def interactive_shell(self):
        """Interactive shell for managing nodes"""
        print("\n🖥️  DinariBlockchain Interactive Shell")
        print("Type 'help' for available commands")
        
        while True:
            try:
                command = input("Dinari> ").strip().lower()
                
                if not command:
                    continue
                elif command == 'help':
                    self._print_help()
                elif command == 'status':
                    self.show_network_status()
                elif command == 'list':
                    self.list_running_nodes()
                elif command.startswith('start '):
                    parts = command.split()
                    if len(parts) >= 2:
                        node_id = parts[1]
                        port = int(parts[2]) if len(parts) > 2 else 8333
                        self.start_single_node(node_id, port=port)
                elif command.startswith('stop '):
                    parts = command.split()
                    if len(parts) >= 2:
                        self.stop_node(parts[1])
                elif command == 'testnet':
                    self.start_test_network()
                elif command == 'stopall':
                    self.stop_all_nodes()
                elif command.startswith('tx'):
                    self.send_test_transaction()
                elif command in ['exit', 'quit']:
                    print("👋 Goodbye!")
                    self.stop_all_nodes()
                    break
                else:
                    print(f"Unknown command: {command}")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                self.stop_all_nodes()
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _print_help(self):
        """Print help message"""
        print("\n📖 Available Commands:")
        print("  help        - Show this help message")
        print("  status      - Show network status")
        print("  list        - List running nodes")
        print("  start <id>  - Start a node with given ID")
        print("  stop <id>   - Stop a node with given ID")
        print("  testnet     - Start 3-node test network")
        print("  stopall     - Stop all running nodes")
        print("  tx          - Send test transaction")
        print("  exit/quit   - Exit the shell")
        print()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DinariBlockchain Node Launcher")
    parser.add_argument("--genesis", default="genesis.json", help="Genesis configuration file")
    parser.add_argument("--data-dir", default="data", help="Data directory for nodes")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single node command
    single_parser = subparsers.add_parser('single', help='Start a single node')
    single_parser.add_argument('node_id', help='Node identifier')
    single_parser.add_argument('--host', default='127.0.0.1', help='Host address')
    single_parser.add_argument('--port', type=int, default=8333, help='Port number')
    single_parser.add_argument('--peers', nargs='*', help='Peer addresses (host:port)')
    
    # Test network command
    testnet_parser = subparsers.add_parser('testnet', help='Start test network')
    testnet_parser.add_argument('--nodes', type=int, default=3, help='Number of nodes')
    
    # Interactive shell command
    shell_parser = subparsers.add_parser('shell', help='Interactive shell')
    
    args = parser.parse_args()
    
    # Create launcher
    launcher = NodeLauncher(args.genesis, args.data_dir)
    
    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        print(f"\n🛑 Shutting down...")
        launcher.stop_all_nodes()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Execute command
    if args.command == 'single':
        # Parse peer addresses
        peer_addresses = []
        if args.peers:
            for peer in args.peers:
                host, port = peer.split(':')
                peer_addresses.append((host, int(port)))
        
        # Start single node
        launcher.start_single_node(args.node_id, args.host, args.port, peer_addresses)
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            launcher.stop_all_nodes()
    
    elif args.command == 'testnet':
        # Start test network
        launcher.start_test_network(args.nodes)
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            launcher.stop_all_nodes()
    
    elif args.command == 'shell':
        # Start interactive shell
        launcher.interactive_shell()
    
    else:
        # Default: show help and start interactive shell
        parser.print_help()
        print("\nStarting interactive shell...")
        launcher.interactive_shell()

if __name__ == "__main__":
    main()
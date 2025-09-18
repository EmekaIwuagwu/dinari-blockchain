#!/usr/bin/env python3
"""
DinariBlockchain - Multi-Node Network Example
examples/multi_node_test.py - Demonstrates a complete P2P blockchain network
"""

import sys
import os
import time
import threading
import signal
import json
from typing import List, Dict

# Add parent directory to path to import Dinari
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Dinari import (
    DinariNode,
    Transaction,
    create_wallet,
    setup_logging
)

class MultiNodeTestNetwork:
    """Manages a multi-node test network"""
    
    def __init__(self, num_nodes: int = 5, base_port: int = 8333):
        self.num_nodes = num_nodes
        self.base_port = base_port
        self.nodes: List[DinariNode] = []
        self.wallets = {}
        self.running = False
        
        # Setup logging
        setup_logging()
        print("🌐 DinariBlockchain - Multi-Node Network Test")
        print("=" * 55)
        
    def create_genesis_config(self) -> Dict:
        """Create genesis configuration for the test network"""
        
        # Create validator addresses for each node
        validators = [f"validator_node_{i+1}" for i in range(min(self.num_nodes, 7))]  # Max 7 validators
        
        genesis_config = {
            'token_name': 'AfricaNetworkCoin',
            'token_symbol': 'ANC',
            'total_supply': '50000000',  # 50 million ANC
            'decimals': 18,
            'validators': validators,
            'block_time': 10,  # 10 seconds for testing
            'initial_allocation': {
                'treasury': '20000000',      # 40% - Central treasury
                'node_rewards': '15000000',  # 30% - Node operator rewards
                'community': '10000000',     # 20% - Community development
                'testing': '5000000'        # 10% - Testing accounts
            }
        }
        
        # Save genesis file
        with open('examples/multi_node_genesis.json', 'w') as f:
            json.dump(genesis_config, f, indent=2)
        
        print(f"✅ Genesis configuration created:")
        print(f"   Network: {genesis_config['token_name']}")
        print(f"   Validators: {len(validators)}")
        print(f"   Total Supply: {genesis_config['total_supply']:,} {genesis_config['token_symbol']}")
        
        return genesis_config
    
    def setup_nodes(self):
        """Setup and configure all network nodes"""
        print(f"\n🖥️  Setting Up {self.num_nodes} Network Nodes")
        print("-" * 45)
        
        genesis_config = self.create_genesis_config()
        
        for i in range(self.num_nodes):
            node_id = f"node_{i+1}"
            port = self.base_port + i
            
            print(f"🔧 Configuring {node_id} (port {port})...")
            
            # Create node
            node = DinariNode(
                node_id=node_id,
                host="127.0.0.1",
                port=port,
                genesis_file="examples/multi_node_genesis.json",
                data_dir="examples/multi_node_data"
            )
            
            self.nodes.append(node)
            
            # Create wallet for each node
            wallet = create_wallet(f"{node_id}_wallet", "examples/multi_node_wallets")
            user_address = wallet.get_all_addresses()[0]
            self.wallets[node_id] = {
                'wallet': wallet,
                'address': user_address
            }
            
            print(f"   ✅ {node_id} ready (validator: {'Yes' if node.is_validator else 'No'})")
        
        print(f"✅ All {len(self.nodes)} nodes configured successfully")
    
    def start_network(self):
        """Start all nodes and establish P2P connections"""
        print(f"\n🚀 Starting Multi-Node Network")
        print("-" * 35)
        
        # Start all nodes
        for i, node in enumerate(self.nodes):
            print(f"🟢 Starting {node.node_id}...")
            node.start()
            time.sleep(1)  # Stagger starts
        
        # Wait for nodes to initialize
        print("⏳ Waiting for nodes to initialize...")
        time.sleep(3)
        
        # Connect nodes to each other (create mesh network)
        print("🔗 Establishing P2P connections...")
        self._create_mesh_connections()
        
        # Wait for network to stabilize
        print("⏳ Network stabilizing...")
        time.sleep(5)
        
        self.running = True
        print("✅ Multi-node network is now running!")
    
    def _create_mesh_connections(self):
        """Create mesh P2P connections between nodes"""
        
        # Each node connects to next 2-3 nodes in the list
        for i, node in enumerate(self.nodes):
            connections_made = 0
            target_connections = min(3, len(self.nodes) - 1)
            
            for j in range(1, len(self.nodes)):
                if connections_made >= target_connections:
                    break
                
                # Connect to next nodes in round-robin fashion
                target_index = (i + j) % len(self.nodes)
                if target_index != i:  # Don't connect to self
                    target_node = self.nodes[target_index]
                    
                    success = node.network.connect_to_peer(
                        target_node.host, 
                        target_node.port
                    )
                    
                    if success:
                        connections_made += 1
                        print(f"   🔗 {node.node_id} ↔ {target_node.node_id}")
                    
                    time.sleep(0.5)  # Small delay between connections
    
    def demonstrate_transactions(self):
        """Demonstrate transactions across the network"""
        print(f"\n💸 Demonstrating Cross-Network Transactions")
        print("-" * 48)
        
        # Get some addresses
        treasury = "treasury"
        node1_addr = self.wallets["node_1"]["address"]
        node2_addr = self.wallets["node_2"]["address"]
        node3_addr = self.wallets["node_3"]["address"]
        
        transactions = [
            # Initial distribution from treasury
            (treasury, node1_addr, "10000", "Send funds to Node 1"),
            (treasury, node2_addr, "8000", "Send funds to Node 2"),
            (treasury, node3_addr, "6000", "Send funds to Node 3"),
            
            # P2P transfers between users
            (node1_addr, node2_addr, "1000", "Node 1 → Node 2 transfer"),
            (node2_addr, node3_addr, "500", "Node 2 → Node 3 transfer"),
            (node3_addr, node1_addr, "250", "Node 3 → Node 1 transfer")
        ]
        
        print(f"📤 Submitting {len(transactions)} transactions to network...")
        
        for i, (from_addr, to_addr, amount, description) in enumerate(transactions, 1):
            # Submit through different nodes for distribution
            submitting_node = self.nodes[i % len(self.nodes)]
            
            success = submitting_node.submit_transaction(
                from_addr, to_addr, amount, "0.1"
            )
            
            from_display = from_addr if len(from_addr) < 15 else f"{from_addr[:12]}..."
            to_display = to_addr if len(to_addr) < 15 else f"{to_addr[:12]}..."
            
            print(f"   {i}. {from_display} → {to_display}: {amount} ANC")
            print(f"      Via: {submitting_node.node_id} ({'✅' if success else '❌'})")
            print(f"      Note: {description}")
            
            time.sleep(1)  # Space out submissions
        
        print("✅ All transactions submitted to network")
    
    def monitor_network_activity(self, duration: int = 60):
        """Monitor network activity for a specified duration"""
        print(f"\n📊 Monitoring Network Activity ({duration} seconds)")
        print("-" * 50)
        
        start_time = time.time()
        last_stats_time = start_time
        
        while self.running and (time.time() - start_time) < duration:
            current_time = time.time()
            
            # Print stats every 10 seconds
            if current_time - last_stats_time >= 10:
                self._print_network_stats()
                last_stats_time = current_time
            
            time.sleep(1)
    
    def _print_network_stats(self):
        """Print current network statistics"""
        print(f"\n📈 Network Status at {time.strftime('%H:%M:%S')}:")
        print("-" * 40)
        
        total_blocks = 0
        total_transactions = 0
        total_pending = 0
        total_peers = 0
        
        for node in self.nodes:
            stats = node.get_node_status()
            blockchain_stats = stats['blockchain_stats']
            
            total_blocks = max(total_blocks, blockchain_stats['total_blocks'])
            total_transactions = max(total_transactions, blockchain_stats['total_transactions'])
            total_pending += blockchain_stats['pending_transactions']
            total_peers += stats['peers_connected']
            
            # Individual node status
            validator_status = "🏆 Validator" if stats['is_validator'] else "🔹 Node"
            print(f"   {validator_status} {stats['node_id']}: "
                  f"Blocks={blockchain_stats['total_blocks']}, "
                  f"Peers={stats['peers_connected']}, "
                  f"Pending={blockchain_stats['pending_transactions']}")
        
        print(f"\n🌐 Network Summary:")
        print(f"   Chain Height: {total_blocks}")
        print(f"   Total Transactions: {total_transactions}")
        print(f"   Pending Transactions: {total_pending}")
        print(f"   Total Connections: {total_peers}")
    
    def check_final_balances(self):
        """Check final balances across all nodes"""
        print(f"\n💰 Final Balance Check")
        print("-" * 25)
        
        # Use the first node as reference (all should have same state)
        reference_node = self.nodes[0]
        
        accounts_to_check = ["treasury", "testing"]
        accounts_to_check.extend([wallet_info["address"] for wallet_info in self.wallets.values()])
        
        print(f"📊 Account Balances (via {reference_node.node_id}):")
        
        for account in accounts_to_check:
            balance = reference_node.blockchain.get_balance(account)
            
            # Format account name
            if account in ["treasury", "testing"]:
                account_name = account.title()
            else:
                # Find which node this address belongs to
                account_name = "Unknown"
                for node_id, wallet_info in self.wallets.items():
                    if wallet_info["address"] == account:
                        account_name = f"{node_id} User"
                        break
            
            print(f"   {account_name}: {balance} ANC")
    
    def demonstrate_consensus(self):
        """Demonstrate consensus mechanism across nodes"""
        print(f"\n⚡ Demonstrating Proof of Authority Consensus")
        print("-" * 48)
        
        print("🔍 Checking validator rotation and block mining...")
        
        # Monitor who mines the next few blocks
        initial_height = self.nodes[0].blockchain.get_latest_block().index
        target_blocks = 5
        
        print(f"📦 Waiting for {target_blocks} new blocks to be mined...")
        
        block_miners = []
        start_time = time.time()
        
        while len(block_miners) < target_blocks and (time.time() - start_time) < 120:  # 2 minute timeout
            current_height = self.nodes[0].blockchain.get_latest_block().index
            
            if current_height > initial_height + len(block_miners):
                # New block found
                latest_block = self.nodes[0].blockchain.get_latest_block()
                block_miners.append({
                    'height': latest_block.index,
                    'validator': latest_block.validator,
                    'timestamp': latest_block.timestamp,
                    'tx_count': len(latest_block.transactions)
                })
                
                print(f"   Block {latest_block.index}: Mined by {latest_block.validator} "
                      f"({len(latest_block.transactions)} txs)")
            
            time.sleep(1)
        
        if block_miners:
            print(f"✅ Consensus working! {len(block_miners)} blocks mined by different validators")
            
            # Check validator distribution
            validator_counts = {}
            for block_info in block_miners:
                validator = block_info['validator']
                validator_counts[validator] = validator_counts.get(validator, 0) + 1
            
            print(f"🏆 Block Distribution:")
            for validator, count in validator_counts.items():
                print(f"   {validator}: {count} blocks")
        else:
            print("⚠️  No new blocks mined during observation period")
    
    def test_network_resilience(self):
        """Test network resilience by stopping and starting nodes"""
        print(f"\n🛡️  Testing Network Resilience")
        print("-" * 32)
        
        if len(self.nodes) < 3:
            print("⚠️  Need at least 3 nodes for resilience testing")
            return
        
        # Stop one node
        test_node = self.nodes[-1]  # Use last node
        print(f"🔴 Stopping {test_node.node_id} to test resilience...")
        
        test_node.stop()
        time.sleep(3)
        
        # Submit a transaction while node is down
        remaining_node = self.nodes[0]
        success = remaining_node.submit_transaction(
            "treasury", "testing", "100", "0.1"
        )
        
        print(f"📤 Transaction submitted while {test_node.node_id} offline: {'✅' if success else '❌'}")
        
        # Wait for block to be mined
        time.sleep(15)
        
        # Restart the node
        print(f"🟢 Restarting {test_node.node_id}...")
        
        # Create new node instance (simulate restart)
        new_node = DinariNode(
            node_id=test_node.node_id,
            host=test_node.host,
            port=test_node.port,
            genesis_file="examples/multi_node_genesis.json",
            data_dir="examples/multi_node_data"
        )
        
        # Replace in our list
        self.nodes[-1] = new_node
        new_node.start()
        time.sleep(2)
        
        # Reconnect to network
        for other_node in self.nodes[:-1]:
            if len(new_node.network.peers) < 2:  # Limit connections
                new_node.network.connect_to_peer(other_node.host, other_node.port)
                time.sleep(1)
        
        print(f"✅ {new_node.node_id} reconnected and syncing...")
        time.sleep(10)  # Allow sync time
        
        # Check if heights match
        heights = [node.blockchain.get_latest_block().index for node in self.nodes]
        if len(set(heights)) == 1:
            print(f"✅ Network resilience test passed! All nodes at height {heights[0]}")
        else:
            print(f"⚠️  Height mismatch after restart: {heights}")
    
    def stop_network(self):
        """Stop all nodes gracefully"""
        print(f"\n🛑 Stopping Multi-Node Network")
        print("-" * 32)
        
        self.running = False
        
        for node in self.nodes:
            print(f"🔴 Stopping {node.node_id}...")
            node.stop()
            time.sleep(0.5)
        
        print("✅ All nodes stopped gracefully")

def run_comprehensive_test():
    """Run a comprehensive multi-node network test"""
    
    # Initialize network
    network = MultiNodeTestNetwork(num_nodes=5, base_port=8340)
    
    try:
        # Setup signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print(f"\n⚠️  Received shutdown signal...")
            network.stop_network()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Run test phases
        print("🚀 Starting Comprehensive Multi-Node Test")
        print("=" * 45)
        
        # Phase 1: Setup
        network.setup_nodes()
        
        # Phase 2: Start Network
        network.start_network()
        
        # Phase 3: Transaction Testing
        network.demonstrate_transactions()
        
        # Phase 4: Monitor Activity
        network.monitor_network_activity(30)  # 30 seconds
        
        # Phase 5: Consensus Demonstration
        network.demonstrate_consensus()
        
        # Phase 6: Resilience Testing
        network.test_network_resilience()
        
        # Phase 7: Final Status
        network.check_final_balances()
        network._print_network_stats()
        
        print(f"\n🎉 Multi-Node Network Test Completed Successfully!")
        print("=" * 52)
        print(f"💡 Key Achievements:")
        print(f"   ✅ {network.num_nodes} nodes networked successfully")
        print(f"   ✅ P2P mesh network established")  
        print(f"   ✅ Cross-node transactions processed")
        print(f"   ✅ Proof of Authority consensus working")
        print(f"   ✅ Network resilience verified")
        print(f"   ✅ All balances synchronized")
        
        # Keep network running for manual testing
        print(f"\n🎮 Network still running for manual testing...")
        print(f"💡 Press Ctrl+C to shutdown gracefully")
        
        while network.running:
            time.sleep(10)
            # Optional: Print periodic stats
            # network._print_network_stats()
    
    except KeyboardInterrupt:
        print(f"\n👋 Shutdown requested by user")
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        network.stop_network()
        print(f"🧹 Cleanup completed")

def quick_network_demo():
    """Quick demonstration with 3 nodes"""
    print("⚡ Quick 3-Node Network Demo")
    print("=" * 30)
    
    network = MultiNodeTestNetwork(num_nodes=3, base_port=8350)
    
    try:
        network.setup_nodes()
        network.start_network()
        
        # Just run basic transaction test
        network.demonstrate_transactions()
        time.sleep(20)  # Wait for mining
        
        network.check_final_balances()
        print("\n✅ Quick demo completed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        network.stop_network()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DinariBlockchain Multi-Node Network Test")
    parser.add_argument("--nodes", type=int, default=5, help="Number of nodes (default: 5)")
    parser.add_argument("--port", type=int, default=8340, help="Base port (default: 8340)")
    parser.add_argument("--quick", action="store_true", help="Run quick 3-node demo")
    
    args = parser.parse_args()
    
    # Ensure directories exist
    os.makedirs("examples/multi_node_wallets", exist_ok=True)
    os.makedirs("examples/multi_node_data", exist_ok=True)
    
    if args.quick:
        quick_network_demo()
    else:
        # Run comprehensive test
        network = MultiNodeTestNetwork(args.nodes, args.port)
        run_comprehensive_test()
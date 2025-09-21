# Create this file: tools/start_multi_nodes.py

import os
import sys
import time
import json
import subprocess
import threading
import requests
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to import blockchain
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def start_node(node_id, api_port, p2p_port, validator=False):
    """Start a single blockchain node"""
    try:
        print(f"🚀 Starting Node {node_id} on API:{api_port}, P2P:{p2p_port}")
        
        # Environment variables for node configuration
        env = os.environ.copy()
        env.update({
            'DINARI_NODE_ID': str(node_id),
            'DINARI_API_PORT': str(api_port),
            'DINARI_P2P_PORT': str(p2p_port),
            'DINARI_IS_VALIDATOR': 'true' if validator else 'false',
            'DINARI_DATA_DIR': f'data/node_{node_id}',
            'DINARI_LOG_LEVEL': 'INFO'
        })
        
        # Create data directory for this node
        data_dir = f'data/node_{node_id}'
        os.makedirs(data_dir, exist_ok=True)
        
        # Start the node process
        cmd = [sys.executable, 'app.py']
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        return {
            'node_id': node_id,
            'api_port': api_port,
            'p2p_port': p2p_port,
            'process': process,
            'validator': validator
        }
        
    except Exception as e:
        print(f"❌ Failed to start node {node_id}: {e}")
        return None


def check_node_health(api_port, timeout=10):
    """Check if a node is healthy and responsive"""
    try:
        response = requests.get(f'http://127.0.0.1:{api_port}/health', timeout=timeout)
        return response.status_code == 200 and response.json().get('status') == 'healthy'
    except:
        return False


def wait_for_nodes(nodes, max_wait=60):
    """Wait for all nodes to become healthy"""
    print("⏳ Waiting for nodes to start...")
    
    start_time = time.time()
    healthy_nodes = set()
    
    while len(healthy_nodes) < len(nodes) and (time.time() - start_time) < max_wait:
        for node in nodes:
            if node and node['node_id'] not in healthy_nodes:
                if check_node_health(node['api_port']):
                    healthy_nodes.add(node['node_id'])
                    print(f"✅ Node {node['node_id']} is healthy (API:{node['api_port']})")
        
        if len(healthy_nodes) < len(nodes):
            time.sleep(2)
    
    return len(healthy_nodes) == len(nodes)


def connect_nodes(nodes):
    """Connect nodes to each other via P2P"""
    print("🔗 Connecting nodes via P2P...")
    
    # Get node addresses
    node_addresses = []
    for node in nodes:
        if node:
            node_addresses.append({
                'id': node['node_id'],
                'address': f"127.0.0.1:{node['p2p_port']}"
            })
    
    # Connect each node to all other nodes
    for node in nodes:
        if not node:
            continue
            
        for peer in node_addresses:
            if peer['id'] != node['node_id']:
                try:
                    # Send peer connection request
                    payload = {
                        "jsonrpc": "2.0",
                        "method": "dinari_addPeer",
                        "params": [peer['address']],
                        "id": 1
                    }
                    
                    response = requests.post(
                        f"http://127.0.0.1:{node['api_port']}/rpc",
                        json=payload,
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        print(f"🔗 Node {node['node_id']} connected to Node {peer['id']}")
                        
                except Exception as e:
                    print(f"⚠️ Failed to connect Node {node['node_id']} to Node {peer['id']}: {e}")


def test_network_sync(nodes):
    """Test blockchain synchronization across nodes"""
    print("🔄 Testing network synchronization...")
    
    # Get blockchain info from all nodes
    node_infos = []
    for node in nodes:
        if not node:
            continue
            
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "dinari_getBlockchainInfo",
                "params": [],
                "id": 1
            }
            
            response = requests.post(
                f"http://127.0.0.1:{node['api_port']}/rpc",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    info = result['result']
                    node_infos.append({
                        'node_id': node['node_id'],
                        'height': info.get('height', 0),
                        'validators': info.get('validators', 0),
                        'total_dinari_supply': info.get('total_dinari_supply', '0')
                    })
                    
        except Exception as e:
            print(f"⚠️ Failed to get info from Node {node['node_id']}: {e}")
    
    # Check if all nodes have similar blockchain state
    if len(node_infos) > 1:
        heights = [info['height'] for info in node_infos]
        max_height = max(heights)
        min_height = min(heights)
        
        print(f"📊 Block heights: {heights}")
        
        if max_height - min_height <= 1:  # Allow 1 block difference
            print("✅ Nodes are synchronized!")
            return True
        else:
            print("⚠️ Nodes have different block heights - sync may be needed")
            return False
    
    return len(node_infos) > 0


def run_transaction_test(nodes):
    """Test transactions across the network"""
    print("💰 Testing transactions across network...")
    
    if not nodes or len(nodes) < 2:
        print("⚠️ Need at least 2 nodes for transaction testing")
        return
    
    # Create a wallet on first node
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "dinari_createWallet",
            "params": [],
            "id": 1
        }
        
        response = requests.post(
            f"http://127.0.0.1:{nodes[0]['api_port']}/rpc",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            wallet_result = response.json()
            if 'result' in wallet_result:
                test_address = wallet_result['result']['address']
                print(f"📍 Created test wallet: {test_address}")
                
                # Wait a bit for network propagation
                time.sleep(5)
                
                # Check if address exists on other nodes
                for i, node in enumerate(nodes[1:], 1):
                    if not node:
                        continue
                        
                    balance_payload = {
                        "jsonrpc": "2.0",
                        "method": "dinari_getBalance",
                        "params": [test_address],
                        "id": 2
                    }
                    
                    balance_response = requests.post(
                        f"http://127.0.0.1:{node['api_port']}/rpc",
                        json=balance_payload,
                        timeout=5
                    )
                    
                    if balance_response.status_code == 200:
                        print(f"✅ Node {node['node_id']} can query test address")
                    else:
                        print(f"⚠️ Node {node['node_id']} cannot query test address")
                        
    except Exception as e:
        print(f"❌ Transaction test failed: {e}")


def main():
    """Main multi-node testing function"""
    print("🌐 DinariBlockchain Multi-Node Testing")
    print("=" * 50)
    
    # Node configuration
    node_configs = [
        {'node_id': 1, 'api_port': 8545, 'p2p_port': 8333, 'validator': True},
        {'node_id': 2, 'api_port': 8546, 'p2p_port': 8334, 'validator': True},
        {'node_id': 3, 'api_port': 8547, 'p2p_port': 8335, 'validator': False}
    ]
    
    print(f"🚀 Starting {len(node_configs)} nodes...")
    
    # Start all nodes
    nodes = []
    with ThreadPoolExecutor(max_workers=len(node_configs)) as executor:
        futures = []
        for config in node_configs:
            future = executor.submit(
                start_node, 
                config['node_id'], 
                config['api_port'], 
                config['p2p_port'], 
                config['validator']
            )
            futures.append(future)
        
        # Collect results
        for future in futures:
            node = future.result()
            nodes.append(node)
    
    # Filter out failed nodes
    healthy_nodes = [node for node in nodes if node is not None]
    
    if not healthy_nodes:
        print("❌ No nodes started successfully")
        return
    
    print(f"✅ Started {len(healthy_nodes)} nodes")
    
    # Wait for nodes to become healthy
    if wait_for_nodes(healthy_nodes):
        print("✅ All nodes are healthy")
        
        # Connect nodes
        connect_nodes(healthy_nodes)
        
        # Wait for connections to establish
        time.sleep(10)
        
        # Test synchronization
        test_network_sync(healthy_nodes)
        
        # Test transactions
        run_transaction_test(healthy_nodes)
        
        print("\n🎉 Multi-node testing complete!")
        print("📊 Network Summary:")
        for node in healthy_nodes:
            print(f"   Node {node['node_id']}: API:{node['api_port']}, P2P:{node['p2p_port']}, Validator:{node['validator']}")
        
        print("\n⏹️ Press Ctrl+C to stop all nodes")
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(10)
                # Could add periodic health checks here
        except KeyboardInterrupt:
            print("\n🛑 Stopping all nodes...")
            for node in healthy_nodes:
                if node['process']:
                    node['process'].terminate()
            print("✅ All nodes stopped")
    
    else:
        print("❌ Some nodes failed to start properly")
        # Clean up any started processes
        for node in healthy_nodes:
            if node['process']:
                node['process'].terminate()


if __name__ == "__main__":
    main()
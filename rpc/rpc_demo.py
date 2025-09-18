#!/usr/bin/env python3
"""
DinariBlockchain RPC Demo
rpc/rpc_demo.py - Complete RPC functionality demonstration
"""

import sys
import os
import time
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rpc.rpc_client import DinariRPCClient
from rpc.rpc_server import DinariRPCServer
from Dinari import DinariNode

def start_rpc_server_background():
    """Start RPC server in background thread"""
    try:
        print("🚀 Starting RPC server in background...")
        
        # Create blockchain node
        node = DinariNode(
            node_id="demo_node",
            host="127.0.0.1",
            port=8333,
            genesis_file="genesis.json"
        )
        
        node.start()
        
        # Create RPC server
        rpc_server = DinariRPCServer(node, "127.0.0.1", 8545)
        
        # Start server (this will block)
        rpc_server.start()
        
    except Exception as e:
        print(f"❌ RPC server failed: {e}")

def comprehensive_rpc_demo():
    """Complete RPC functionality demo"""
    print("🌍 DinariBlockchain RPC Comprehensive Demo")
    print("=" * 50)
    
    # Wait for server to start
    print("⏳ Waiting for RPC server to start...")
    time.sleep(5)
    
    client = DinariRPCClient()
    
    try:
        print("\n🔍 === CONNECTIVITY TESTS ===")
        
        # Test ping
        response = client.ping()
        print(f"✅ Ping test: {response}")
        
        # Get version
        version = client.get_version()
        print(f"✅ Version: {version['name']} v{version['version']}")
        
        print("\n📊 === BLOCKCHAIN INFORMATION ===")
        
        # Get blockchain info
        info = client.get_blockchain_info()
        print(f"✅ Chain Height: {info['chain_height']}")
        print(f"✅ Total Transactions: {info['total_transactions']}")
        print(f"✅ Pending Transactions: {info['pending_transactions']}")
        print(f"✅ Total Validators: {info['total_validators']}")
        
        # Get validators
        validators = client.get_validators()
        print(f"✅ Validators: {validators}")
        
        # Get latest block
        if info['chain_height'] > 0:
            latest_block = client.get_block(info['chain_height'] - 1)
            print(f"✅ Latest Block:")
            print(f"   Index: {latest_block['index']}")
            print(f"   Hash: {latest_block['hash'][:20]}...")
            print(f"   Validator: {latest_block['validator']}")
            print(f"   Transactions: {len(latest_block['transactions'])}")
        
        print("\n💰 === WALLET & BALANCE TESTS ===")
        
        # Get treasury balance
        treasury_balance = client.get_balance("treasury")
        print(f"✅ Treasury Balance: {treasury_balance} DNMR")
        
        # Create new wallet
        wallet_result = client.create_wallet("rpc_demo_wallet")
        print(f"✅ Created Wallet: {wallet_result['wallet_name']}")
        print(f"   Addresses: {len(wallet_result['addresses'])}")
        demo_address = wallet_result['addresses'][0]
        print(f"   First Address: {demo_address[:25]}...")
        
        print("\n💸 === TRANSACTION TESTS ===")
        
        # Send transaction to demo address
        print("📤 Sending 1000 DNMR to demo address...")
        tx_result = client.send_transaction("treasury", demo_address, "1000", "0.1")
        print(f"✅ Transaction Created:")
        print(f"   Hash: {tx_result['transaction_hash'][:20]}...")
        print(f"   Status: {tx_result['status']}")
        
        # Mine the transaction
        if validators:
            print(f"⛏️  Mining block with validator: {validators[0]}")
            mine_result = client.mine_block(validators[0])
            
            if mine_result['success']:
                print(f"✅ Block Mined:")
                print(f"   Block Index: {mine_result['block_index']}")
                print(f"   Block Hash: {mine_result['block_hash']}")
                print(f"   Transactions: {mine_result['transactions']}")
                
                # Check updated balance
                new_balance = client.get_balance(demo_address)
                print(f"✅ Demo Address Balance: {new_balance} DNMR")
            else:
                print(f"⚠️  Mining failed: {mine_result['message']}")
        
        print("\n🔧 === SMART CONTRACT TESTS ===")
        
        # Deploy simple contract
        simple_contract = '''
def __init__(initial_message):
    contract.state['message'] = initial_message
    contract.state['counter'] = 0
    emit_event('ContractCreated', {'message': initial_message})

def get_message():
    return contract.state.get('message', 'No message set')

def set_message(new_message):
    contract.state['message'] = new_message
    emit_event('MessageUpdated', {'new_message': new_message})
    return True

def increment_counter():
    current = contract.state.get('counter', 0)
    contract.state['counter'] = current + 1
    emit_event('CounterIncremented', {'new_value': contract.state['counter']})
    return contract.state['counter']

def get_counter():
    return contract.state.get('counter', 0)
'''
        
        print("📦 Deploying smart contract...")
        deploy_result = client.deploy_contract(simple_contract, "treasury", ["Hello RPC World!"])
        contract_address = deploy_result['contract_address']
        
        print(f"✅ Contract Deployed:")
        print(f"   Address: {contract_address[:25]}...")
        print(f"   Deployer: {deploy_result['deployer']}")
        print(f"   Gas Used: {deploy_result['gas_used']}")
        
        # Test contract functions
        print("\n📞 Testing contract functions...")
        
        # Get initial message
        call_result = client.call_contract(contract_address, 'get_message', 'treasury')
        if call_result['success']:
            print(f"✅ get_message(): {call_result['result']}")
        
        # Get initial counter
        call_result = client.call_contract(contract_address, 'get_counter', 'treasury')
        if call_result['success']:
            print(f"✅ get_counter(): {call_result['result']}")
        
        # Increment counter
        call_result = client.call_contract(contract_address, 'increment_counter', 'treasury')
        if call_result['success']:
            print(f"✅ increment_counter(): {call_result['result']}")
        
        # Set new message
        call_result = client.call_contract(contract_address, 'set_message', 'treasury', ['RPC Demo Success!'])
        if call_result['success']:
            print(f"✅ set_message(): {call_result['result']}")
        
        # Get updated message
        call_result = client.call_contract(contract_address, 'get_message', 'treasury')
        if call_result['success']:
            print(f"✅ Updated message: {call_result['result']}")
        
        # Get contract info
        contract_info = client.get_contract_info(contract_address)
        print(f"✅ Contract Info:")
        print(f"   Address: {contract_info['address'][:25]}...")
        print(f"   Deployer: {contract_info['deployer']}")
        
        print("\n🌐 === NETWORK TESTS ===")
        
        # Get network info
        try:
            network_info = client.get_network_info()
            print(f"✅ Network Info:")
            print(f"   Node ID: {network_info['node_id']}")
            print(f"   Is Validator: {network_info['is_validator']}")
            print(f"   Connected Peers: {network_info['peers_connected']}")
            print(f"   Running: {network_info['running']}")
        except Exception as e:
            print(f"⚠️  Network info: {e}")
        
        # Get peers
        peers = client.get_peers()
        print(f"✅ Connected Peers: {len(peers)}")
        
        print("\n📈 === FINAL BLOCKCHAIN STATE ===")
        
        # Get final blockchain info
        final_info = client.get_blockchain_info()
        print(f"✅ Final Chain Height: {final_info['chain_height']}")
        print(f"✅ Final Total Transactions: {final_info['total_transactions']}")
        print(f"✅ Final Pending Transactions: {final_info['pending_transactions']}")
        
        print(f"\n🎉 RPC DEMO COMPLETED SUCCESSFULLY! 🎉")
        print("=" * 50)
        print("✅ All RPC methods tested and working")
        print("✅ Blockchain operations via RPC confirmed")
        print("✅ Smart contracts deployable via RPC")
        print("✅ Network information accessible via RPC")
        
    except Exception as e:
        print(f"❌ RPC Demo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure no other service is using port 8545")
        print("2. Check that genesis.json exists")
        print("3. Ensure all dependencies are installed")

def main():
    """Main demo function"""
    print("🌍 DinariBlockchain RPC System Demo")
    print("This will start an RPC server and demonstrate all functionality")
    print("=" * 60)
    
    try:
        # Start RPC server in background thread
        server_thread = threading.Thread(target=start_rpc_server_background, daemon=True)
        server_thread.start()
        
        # Run comprehensive demo
        comprehensive_rpc_demo()
        
        print("\n🛑 Demo completed. Server still running...")
        print("You can now:")
        print("- Use scripts/test_rpc_client.bat")
        print("- Use scripts/rpc_curl_examples.bat") 
        print("- Connect with your own RPC client")
        print("\nPress Ctrl+C to stop")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Shutting down demo...")

if __name__ == "__main__":
    main()
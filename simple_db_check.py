# simple_db_check.py
# Use this to check your database with your existing code

import sys
import os

# Add your project path if needed
sys.path.append('.')

try:
    # Try to import your blockchain class (adjust the import based on your structure)
    from Dinari import DinariBlockchain  # Adjust this import
    # OR from blockchain import DinariBlockchain
    # OR whatever your actual import path is
    
    print("✅ Successfully imported blockchain")
    
    # Initialize blockchain
    blockchain = DinariBlockchain()
    print("✅ Blockchain initialized")
    
    # Basic checks
    try:
        chain_height = blockchain.get_chain_height()
        print(f"📊 Chain height: {chain_height}")
    except Exception as e:
        print(f"❌ get_chain_height() failed: {e}")
    
    # Check blocks and their transactions
    print("\n🧱 BLOCK ANALYSIS:")
    for i in range(min(5, chain_height if 'chain_height' in locals() else 3)):
        try:
            block = blockchain.get_block_by_index(i)
            if block:
                transactions = block.get('transactions', [])
                print(f"Block {i}: {len(transactions)} transactions")
                
                if transactions:
                    print(f"  📄 First transaction keys: {list(transactions[0].keys()) if transactions[0] else 'None'}")
                    print(f"  📄 First transaction: {transactions[0]}")
                else:
                    print(f"  📄 No transactions in this block")
            else:
                print(f"Block {i}: No data found")
                
        except Exception as e:
            print(f"❌ Error getting block {i}: {e}")
    
    # Check what get_recent_transactions returns
    print("\n💰 TRANSACTION ANALYSIS:")
    try:
        recent_txs = blockchain.get_recent_transactions(3)
        print(f"get_recent_transactions() returned: {len(recent_txs) if recent_txs else 0} transactions")
        
        if recent_txs:
            print(f"First transaction: {recent_txs[0]}")
            print(f"From address: {recent_txs[0].get('from_address', 'not found')}")
            print(f"Is this genesis? {'YES' if recent_txs[0].get('from_address') == 'genesis' else 'NO'}")
        
    except Exception as e:
        print(f"❌ get_recent_transactions() failed: {e}")
        
except ImportError as e:
    print(f"❌ Could not import blockchain: {e}")
    print("\n💡 Please check:")
    print("1. What's your main blockchain file name?")
    print("2. What's your blockchain class name?")
    print("3. Run this from your project directory")
    
    print(f"\n📁 Current directory: {os.getcwd()}")
    print(f"📁 Files in current directory:")
    for item in os.listdir('.'):
        if item.endswith('.py'):
            print(f"   {item}")
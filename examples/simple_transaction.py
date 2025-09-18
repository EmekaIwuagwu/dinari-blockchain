#!/usr/bin/env python3
"""
DinariBlockchain - Simple Transaction Example
examples/simple_transaction.py - Basic example showing blockchain transactions
"""

import sys
import os
import time
import json

# Add parent directory to path to import Dinari
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Dinari import (
    DinariBlockchain,
    Transaction,
    DinariWallet,
    create_wallet,
    setup_logging
)

def main():
    """Main example demonstrating simple transactions"""
    
    # Setup logging
    setup_logging()
    print("🚀 DinariBlockchain - Simple Transaction Example")
    print("=" * 55)
    
    # Step 1: Create a test blockchain
    print("\n📦 Step 1: Creating Test Blockchain")
    print("-" * 40)
    
    genesis_config = {
        'token_name': 'Dinari',
        'token_symbol': 'DNMR',
        'total_supply': '1000000',  # 1 million DNMR
        'decimals': 18,
        'validators': ['validator_alice', 'validator_bob'],
        'block_time': 10,  # Fast blocks for demo
        'initial_allocation': {
            'treasury': '500000',    # 500K to treasury
            'foundation': '300000',  # 300K to foundation
            'community': '200000'    # 200K to community fund
        }
    }
    
    blockchain = DinariBlockchain(genesis_config)
    print(f"✅ Blockchain created with {len(blockchain.chain)} blocks")
    print(f"   Token: {genesis_config['token_name']} ({genesis_config['token_symbol']})")
    print(f"   Total Supply: {genesis_config['total_supply']:,} DNMR")
    
    # Display initial balances
    print(f"\n💰 Initial Balances:")
    for account in ['treasury', 'foundation', 'community']:
        balance = blockchain.get_balance(account)
        print(f"   {account.capitalize()}: {balance:,} DNMR")
    
    # Step 2: Create wallets for users
    print("\n👥 Step 2: Creating User Wallets")
    print("-" * 40)
    
    # Create wallet for Alice
    alice_wallet = create_wallet("alice_wallet", "examples/wallets")
    alice_address = alice_wallet.get_all_addresses()[0]
    print(f"✅ Alice's wallet created")
    print(f"   Address: {alice_address}")
    
    # Create wallet for Bob
    bob_wallet = create_wallet("bob_wallet", "examples/wallets") 
    bob_address = bob_wallet.get_all_addresses()[0]
    print(f"✅ Bob's wallet created")
    print(f"   Address: {bob_address}")
    
    # Step 3: Send DNMR tokens to users
    print("\n💸 Step 3: Distributing DNMR Tokens")
    print("-" * 40)
    
    # Send 1000 DNMR to Alice from treasury
    print("📤 Sending 1,000 DNMR to Alice...")
    tx1 = Transaction(
        from_address="treasury",
        to_address=alice_address,
        amount="1000",
        fee="0.1",
        data="Initial distribution to Alice"
    )
    
    success = blockchain.add_transaction(tx1)
    print(f"   Transaction created: {'✅' if success else '❌'}")
    print(f"   Hash: {tx1.calculate_hash()[:16]}...")
    
    # Send 500 DNMR to Bob from foundation
    print("\n📤 Sending 500 DNMR to Bob...")
    tx2 = Transaction(
        from_address="foundation", 
        to_address=bob_address,
        amount="500",
        fee="0.1",
        data="Initial distribution to Bob"
    )
    
    success = blockchain.add_transaction(tx2)
    print(f"   Transaction created: {'✅' if success else '❌'}")
    print(f"   Hash: {tx2.calculate_hash()[:16]}...")
    
    # Step 4: Mine a block
    print("\n⛏️  Step 4: Mining Block")
    print("-" * 40)
    
    print("🔨 Mining block with pending transactions...")
    block = blockchain.mine_block('validator_alice')
    
    if block:
        print(f"✅ Block {block.index} mined successfully!")
        print(f"   Validator: {block.validator}")
        print(f"   Transactions: {len(block.transactions)}")
        print(f"   Block Hash: {block.hash[:16]}...")
        print(f"   Timestamp: {time.ctime(block.timestamp)}")
    else:
        print("❌ Failed to mine block")
        return
    
    # Step 5: Check balances after mining
    print("\n💰 Step 5: Updated Balances")
    print("-" * 40)
    
    balances = {
        'Treasury': blockchain.get_balance('treasury'),
        'Foundation': blockchain.get_balance('foundation'),
        'Alice': blockchain.get_balance(alice_address),
        'Bob': blockchain.get_balance(bob_address)
    }
    
    for account, balance in balances.items():
        print(f"   {account}: {balance} DNMR")
    
    # Step 6: User-to-user transaction
    print("\n🔄 Step 6: User-to-User Transaction")
    print("-" * 40)
    
    print("📤 Alice sending 100 DNMR to Bob...")
    
    # Alice creates and sends transaction to Bob
    success = alice_wallet.send_transaction(
        from_address=alice_address,
        to_address=bob_address,
        amount="100",
        blockchain=blockchain,
        fee="0.1"
    )
    
    print(f"   Transaction sent: {'✅' if success else '❌'}")
    
    # Mine another block
    print("\n🔨 Mining another block...")
    block2 = blockchain.mine_block('validator_bob')
    
    if block2:
        print(f"✅ Block {block2.index} mined by {block2.validator}")
        print(f"   Transactions: {len(block2.transactions)}")
    
    # Step 7: Final balances
    print("\n💰 Step 7: Final Balances")
    print("-" * 40)
    
    final_balances = {
        'Alice': blockchain.get_balance(alice_address),
        'Bob': blockchain.get_balance(bob_address)
    }
    
    for account, balance in final_balances.items():
        print(f"   {account}: {balance} DNMR")
    
    # Step 8: Transaction history
    print("\n📊 Step 8: Transaction History")
    print("-" * 40)
    
    # Update wallet transaction histories
    alice_wallet.update_transaction_history(blockchain)
    bob_wallet.update_transaction_history(blockchain)
    
    alice_history = alice_wallet.get_transaction_history(alice_address)
    print(f"📈 Alice's transaction history ({len(alice_history)} transactions):")
    
    for i, tx in enumerate(alice_history, 1):
        tx_type = "Received" if tx.to_address == alice_address else "Sent"
        other_party = tx.from_address if tx_type == "Received" else tx.to_address
        print(f"   {i}. {tx_type} {tx.amount} DNMR")
        print(f"      {'From' if tx_type == 'Received' else 'To'}: {other_party[:20]}...")
        print(f"      Fee: {tx.fee} DNMR")
        print(f"      Time: {time.ctime(tx.timestamp)}")
        print()
    
    # Step 9: Blockchain statistics
    print("\n📊 Step 9: Blockchain Statistics")
    print("-" * 40)
    
    stats = blockchain.get_stats()
    print(f"📈 Blockchain Overview:")
    print(f"   Total Blocks: {stats['total_blocks']}")
    print(f"   Total Transactions: {stats['total_transactions']}")
    print(f"   Pending Transactions: {stats['pending_transactions']}")
    print(f"   Total Validators: {stats['total_validators']}")
    print(f"   Chain Valid: {'✅' if stats['chain_valid'] else '❌'}")
    print(f"   Latest Block: {stats['latest_block_hash']}")
    
    # Step 10: Save everything
    print("\n💾 Step 10: Saving Data")
    print("-" * 40)
    
    # Save blockchain
    blockchain.save_to_file("examples/blockchain_demo.json")
    print("✅ Blockchain saved to examples/blockchain_demo.json")
    
    # Save wallets (already auto-saved)
    print("✅ Wallets saved automatically")
    
    print(f"\n🎉 Simple Transaction Example Completed Successfully!")
    print("=" * 55)
    print(f"💡 Key Takeaways:")
    print(f"   • Created blockchain with {genesis_config['total_supply']} DNMR tokens")
    print(f"   • Set up {len(blockchain.validators)} validators for consensus")
    print(f"   • Created wallets for Alice and Bob")
    print(f"   • Processed {stats['total_transactions']} transactions across {stats['total_blocks']} blocks")
    print(f"   • Demonstrated P2P transfers with automatic fee handling")
    print(f"   • All data saved for future use")
    print()
    
    # Optional: Interactive mode
    interactive_mode(blockchain, alice_wallet, bob_wallet, alice_address, bob_address)

def interactive_mode(blockchain, alice_wallet, bob_wallet, alice_address, bob_address):
    """Optional interactive mode to try more transactions"""
    
    while True:
        print("\n🎮 Interactive Mode - Try more transactions!")
        print("Commands:")
        print("  1. Send Alice -> Bob")
        print("  2. Send Bob -> Alice") 
        print("  3. Check balances")
        print("  4. Mine block")
        print("  5. Show blockchain stats")
        print("  6. Exit")
        
        try:
            choice = input("\nEnter command (1-6): ").strip()
            
            if choice == '1':
                amount = input("Amount for Alice to send Bob: ")
                success = alice_wallet.send_transaction(
                    alice_address, bob_address, amount, blockchain
                )
                print(f"Transaction: {'✅ Success' if success else '❌ Failed'}")
                
            elif choice == '2':
                amount = input("Amount for Bob to send Alice: ")
                success = bob_wallet.send_transaction(
                    bob_address, alice_address, amount, blockchain
                )
                print(f"Transaction: {'✅ Success' if success else '❌ Failed'}")
                
            elif choice == '3':
                alice_balance = blockchain.get_balance(alice_address)
                bob_balance = blockchain.get_balance(bob_address)
                print(f"Alice: {alice_balance} DNMR")
                print(f"Bob: {bob_balance} DNMR")
                
            elif choice == '4':
                validator = blockchain.validators[0]  # Use first validator
                block = blockchain.mine_block(validator)
                if block:
                    print(f"✅ Block {block.index} mined with {len(block.transactions)} transactions")
                else:
                    print("❌ No transactions to mine")
                    
            elif choice == '5':
                stats = blockchain.get_stats()
                print(f"Blocks: {stats['total_blocks']}, Transactions: {stats['total_transactions']}")
                print(f"Pending: {stats['pending_transactions']}")
                
            elif choice == '6':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Ensure examples directory exists
    os.makedirs("examples/wallets", exist_ok=True)
    
    # Run the example
    main()
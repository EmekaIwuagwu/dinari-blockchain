#!/usr/bin/env python3
"""
DinariBlockchain - Smart Contract Deployment Example
examples/deploy_contract.py - Comprehensive smart contract demonstration
"""

import sys
import os
import time
import json

# Add parent directory to path to import Dinari
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Dinari import (
    DinariBlockchain,
    ContractManager,
    Transaction,
    create_wallet,
    setup_logging
)

def main():
    """Main example demonstrating smart contract deployment and usage"""
    
    # Setup logging
    setup_logging()
    print("🚀 DinariBlockchain - Smart Contract Deployment Example")
    print("=" * 65)
    
    # Step 1: Create blockchain and contract manager
    print("\n📦 Step 1: Setting Up Blockchain & Contract System")
    print("-" * 50)
    
    genesis_config = {
        'token_name': 'AfricaCoin',
        'token_symbol': 'DNMR',
        'total_supply': '10000000',  # 10 million DNMR
        'decimals': 18,
        'validators': ['validator_ghana', 'validator_nigeria', 'validator_kenya'],
        'block_time': 15,
        'initial_allocation': {
            'treasury': '4000000',      # 40% - Treasury
            'development': '2000000',   # 20% - Development fund
            'community': '2000000',     # 20% - Community programs
            'partnerships': '1000000',  # 10% - Strategic partnerships
            'team': '1000000'          # 10% - Team allocation
        }
    }
    
    blockchain = DinariBlockchain(genesis_config)
    contract_manager = ContractManager(blockchain)
    
    print(f"✅ Blockchain initialized with {len(blockchain.validators)} validators")
    print(f"✅ Contract manager ready for deployments")
    print(f"   Total Supply: {genesis_config['total_supply']:,} {genesis_config['token_symbol']}")
    
    # Step 2: Deploy Token Contract (ERC20-like)
    print("\n🪙 Step 2: Deploying AfroToken Contract")
    print("-" * 45)
    
    print("📦 Deploying AfroToken smart contract...")
    
    try:
        token_deployment = contract_manager.deploy_from_template(
            'token',
            'treasury',  # Deployer
            ['AfroToken', 'ATK', '5000000']  # name, symbol, supply
        )
        
        token_address = token_deployment.address
        print(f"✅ AfroToken deployed successfully!")
        print(f"   Contract Address: {token_address}")
        print(f"   Deployer: {token_deployment.deployer}")
        print(f"   Gas Used: {token_deployment.gas_used:,}")
        
    except Exception as e:
        print(f"❌ Token deployment failed: {e}")
        return
    
    # Test token contract functions
    print("\n💰 Testing AfroToken Functions:")
    print("-" * 35)
    
    # Check initial balance
    result = contract_manager.call_contract(
        token_address, 'balance_of', ['treasury'], 'treasury'
    )
    if result.success:
        print(f"✅ Treasury balance: {result.result:,} ATK")
    else:
        print(f"❌ Balance check failed: {result.error}")
    
    # Create users for testing
    alice_wallet = create_wallet("alice_contract_wallet", "examples/wallets")
    alice_address = alice_wallet.get_all_addresses()[0]
    
    bob_wallet = create_wallet("bob_contract_wallet", "examples/wallets") 
    bob_address = bob_wallet.get_all_addresses()[0]
    
    print(f"👥 Created test users: Alice & Bob")
    
    # Transfer tokens within contract
    print(f"\n📤 Transferring 1000 ATK from Treasury to Alice...")
    result = contract_manager.call_contract(
        token_address, 'transfer', [alice_address, 1000], 'treasury'
    )
    
    if result.success:
        print(f"✅ Transfer successful!")
        print(f"   Events: {len(result.events)} events emitted")
        for event in result.events:
            print(f"   📢 {event['event_name']}: {event['data']}")
    else:
        print(f"❌ Transfer failed: {result.error}")
    
    # Check Alice's token balance
    result = contract_manager.call_contract(
        token_address, 'balance_of', [alice_address], 'alice'
    )
    if result.success:
        print(f"✅ Alice's ATK balance: {result.result}")
    
    # Step 3: Deploy Voting Contract
    print("\n🗳️  Step 3: Deploying Community Voting Contract")
    print("-" * 48)
    
    print("📦 Deploying community voting contract...")
    
    voting_options = [
        "Expand to South Africa",
        "Launch mobile app", 
        "Partner with banks",
        "Increase block rewards"
    ]
    
    try:
        voting_deployment = contract_manager.deploy_from_template(
            'voting',
            'community',  # Community fund deploys it
            [
                'African Blockchain Future 2024',  # Title
                voting_options,                     # Options
                86400 * 7                          # 7 days voting period
            ]
        )
        
        voting_address = voting_deployment.address
        print(f"✅ Voting contract deployed!")
        print(f"   Contract Address: {voting_address}")
        print(f"   Voting Period: 7 days")
        print(f"   Options: {len(voting_options)}")
        
        for i, option in enumerate(voting_options, 1):
            print(f"     {i}. {option}")
            
    except Exception as e:
        print(f"❌ Voting deployment failed: {e}")
        return
    
    # Test voting
    print("\n🗳️  Testing Voting Functions:")
    print("-" * 30)
    
    # Alice votes
    print(f"🗳️  Alice voting for '{voting_options[1]}'...")
    result = contract_manager.call_contract(
        voting_address, 'vote', [voting_options[1]], alice_address
    )
    
    if result.success:
        print(f"✅ Alice's vote recorded!")
        for event in result.events:
            print(f"   📢 Vote Event: {event['data']}")
    else:
        print(f"❌ Voting failed: {result.error}")
    
    # Bob votes  
    print(f"\n🗳️  Bob voting for '{voting_options[0]}'...")
    result = contract_manager.call_contract(
        voting_address, 'vote', [voting_options[0]], bob_address
    )
    
    if result.success:
        print(f"✅ Bob's vote recorded!")
    else:
        print(f"❌ Bob's vote failed: {result.error}")
    
    # Check voting results
    result = contract_manager.call_contract(
        voting_address, 'get_results', [], 'anyone'
    )
    
    if result.success:
        print(f"\n📊 Current Voting Results:")
        for option, votes in result.result.items():
            print(f"   {option}: {votes} votes")
    
    # Step 4: Deploy Multi-signature Wallet
    print("\n🔐 Step 4: Deploying Multi-Signature Wallet")
    print("-" * 46)
    
    print("📦 Deploying multi-sig wallet for team funds...")
    
    multisig_owners = ['treasury', 'team', alice_address]
    required_sigs = 2
    
    try:
        multisig_deployment = contract_manager.deploy_from_template(
            'multisig',
            'team',
            [multisig_owners, required_sigs]
        )
        
        multisig_address = multisig_deployment.address
        print(f"✅ Multi-sig wallet deployed!")
        print(f"   Contract Address: {multisig_address}")
        print(f"   Owners: {len(multisig_owners)}")
        print(f"   Required Signatures: {required_sigs}")
        
        for i, owner in enumerate(multisig_owners, 1):
            display_name = owner if len(owner) < 20 else f"{owner[:15]}..."
            print(f"     {i}. {display_name}")
            
    except Exception as e:
        print(f"❌ Multi-sig deployment failed: {e}")
        return
    
    # Test multi-sig functionality
    print("\n🔐 Testing Multi-Signature Wallet:")
    print("-" * 38)
    
    # Submit transaction proposal
    print(f"📝 Treasury proposing to send 100 DNMR to community...")
    result = contract_manager.call_contract(
        multisig_address, 'submit_transaction', 
        ['community', 100, 'Community funding proposal'], 
        'treasury'
    )
    
    if result.success:
        tx_id = result.result
        print(f"✅ Transaction proposal submitted! ID: {tx_id}")
        
        # Alice confirms the transaction
        print(f"\n✅ Alice confirming transaction {tx_id}...")
        result = contract_manager.call_contract(
            multisig_address, 'confirm_transaction', [tx_id], alice_address
        )
        
        if result.success:
            if result.result:
                print(f"✅ Transaction executed! (2 signatures reached)")
            else:
                print(f"✅ Alice's confirmation recorded (need 1 more signature)")
        else:
            print(f"❌ Confirmation failed: {result.error}")
            
        # Check transaction details
        result = contract_manager.call_contract(
            multisig_address, 'get_transaction', [tx_id], 'anyone'
        )
        if result.success and result.result:
            tx_info = result.result
            print(f"📋 Transaction {tx_id} Details:")
            print(f"   To: {tx_info['to']}")
            print(f"   Amount: {tx_info['amount']} DNMR")
            print(f"   Executed: {tx_info['executed']}")
    
    # Step 5: Mine blocks to include all transactions
    print("\n⛏️  Step 5: Mining Blocks with Contract Transactions")
    print("-" * 53)
    
    print("🔨 Mining blocks to process all contract interactions...")
    
    # Mine multiple blocks to process all transactions
    blocks_mined = 0
    for validator in blockchain.validators:
        if len(blockchain.transaction_pool) > 0:
            block = blockchain.mine_block(validator)
            if block:
                blocks_mined += 1
                print(f"✅ Block {block.index} mined by {validator}")
                print(f"   Transactions processed: {len(block.transactions)}")
    
    if blocks_mined == 0:
        print("ℹ️  No pending transactions to mine")
    
    # Step 6: Contract Analytics
    print("\n📊 Step 6: Smart Contract Analytics")
    print("-" * 40)
    
    all_contracts = contract_manager.get_all_contracts()
    print(f"📈 Contract Deployment Summary:")
    print(f"   Total Contracts: {len(all_contracts)}")
    
    for addr, contract in all_contracts.items():
        print(f"\n   🔹 Contract: {addr[:20]}...")
        print(f"     Deployer: {contract.deployer}")
        print(f"     Events: {len(contract.events)}")
        print(f"     State Size: {len(contract.state)} keys")
        
        # Show recent events
        recent_events = contract.get_events()[-3:]  # Last 3 events
        if recent_events:
            print(f"     Recent Events:")
            for event in recent_events:
                print(f"       📢 {event['event_name']}: {str(event['data'])[:50]}...")
    
    # Step 7: Custom Contract Example
    print("\n🔧 Step 7: Deploying Custom African Savings Contract")
    print("-" * 57)
    
    # Custom savings contract for African communities
    african_savings_contract = '''
# African Community Savings Contract (Tontine-style)
def __init__(group_name, target_amount, duration_days):
    contract.state['group_name'] = group_name
    contract.state['target_amount'] = int(target_amount)
    contract.state['duration_days'] = int(duration_days)
    contract.state['created_at'] = get_timestamp()
    contract.state['members'] = {}
    contract.state['total_saved'] = 0
    contract.state['completed'] = False
    emit_event('GroupCreated', {'name': group_name, 'target': target_amount})

def join_group(member_address):
    require(member_address not in contract.state['members'], "Already a member")
    require(not contract.state['completed'], "Group savings completed")
    
    contract.state['members'][member_address] = {
        'contributions': 0,
        'joined_at': get_timestamp()
    }
    emit_event('MemberJoined', {'member': member_address})
    return True

def contribute(amount):
    require(caller in contract.state['members'], "Must be a group member")
    require(not contract.state['completed'], "Group savings completed")
    require(amount > 0, "Amount must be positive")
    
    # Update member contribution
    contract.state['members'][caller]['contributions'] += amount
    contract.state['total_saved'] += amount
    
    emit_event('Contribution', {'member': caller, 'amount': amount})
    
    # Check if target reached
    if contract.state['total_saved'] >= contract.state['target_amount']:
        contract.state['completed'] = True
        emit_event('TargetReached', {'total': contract.state['total_saved']})
    
    return True

def get_group_status():
    return {
        'name': contract.state['group_name'],
        'target': contract.state['target_amount'], 
        'saved': contract.state['total_saved'],
        'members': len(contract.state['members']),
        'completed': contract.state['completed'],
        'progress_percent': (contract.state['total_saved'] / contract.state['target_amount']) * 100
    }

def get_member_info(member_address):
    if member_address in contract.state['members']:
        return contract.state['members'][member_address]
    return None
'''
    
    print("📦 Deploying African Community Savings contract...")
    
    try:
        savings_address = contract_manager.deploy_contract(
            african_savings_contract,
            'community',  # Deployed by community fund
            ['Lagos Women Cooperative', 50000, 30]  # name, target, days
        )
        
        print(f"✅ African Savings contract deployed!")
        print(f"   Contract Address: {savings_address}")
        print(f"   Group: Lagos Women Cooperative")
        print(f"   Target: 50,000 DNMR")
        print(f"   Duration: 30 days")
        
        # Test the savings contract
        print(f"\n🤝 Testing Community Savings Features:")
        
        # Alice joins the group
        result = contract_manager.call_contract(
            savings_address, 'join_group', [alice_address], alice_address
        )
        if result.success:
            print(f"✅ Alice joined the savings group")
        
        # Bob joins the group
        result = contract_manager.call_contract(
            savings_address, 'join_group', [bob_address], bob_address
        )
        if result.success:
            print(f"✅ Bob joined the savings group")
        
        # Alice makes a contribution
        result = contract_manager.call_contract(
            savings_address, 'contribute', [5000], alice_address
        )
        if result.success:
            print(f"✅ Alice contributed 5,000 DNMR")
        
        # Check group status
        result = contract_manager.call_contract(
            savings_address, 'get_group_status', [], 'anyone'
        )
        if result.success:
            status = result.result
            print(f"\n📊 Group Status:")
            print(f"   Name: {status['name']}")
            print(f"   Progress: {status['saved']:,} / {status['target']:,} DNMR ({status['progress_percent']:.1f}%)")
            print(f"   Members: {status['members']}")
            print(f"   Completed: {'Yes' if status['completed'] else 'No'}")
            
    except Exception as e:
        print(f"❌ Custom contract deployment failed: {e}")
    
    # Step 8: Final Summary
    print("\n🎉 Step 8: Smart Contract Example Summary")
    print("-" * 46)
    
    blockchain_stats = blockchain.get_stats()
    
    print(f"📈 Final Statistics:")
    print(f"   Blockchain Height: {blockchain_stats['total_blocks']} blocks")
    print(f"   Total Transactions: {blockchain_stats['total_transactions']}")
    print(f"   Smart Contracts: {len(all_contracts)}")
    print(f"   Contract Types Deployed:")
    print(f"     • ERC20-like Token (AfroToken)")
    print(f"     • Community Voting System")
    print(f"     • Multi-signature Wallet") 
    print(f"     • African Savings Cooperative")
    
    print(f"\n💡 Key Features Demonstrated:")
    print(f"   ✅ Token creation and transfers")
    print(f"   ✅ Democratic voting mechanisms")
    print(f"   ✅ Multi-signature security")
    print(f"   ✅ Community savings (Tontine-style)")
    print(f"   ✅ Event emission and tracking")
    print(f"   ✅ State management and persistence")
    print(f"   ✅ African-focused financial tools")
    
    # Save everything
    print(f"\n💾 Saving Contract Data...")
    blockchain.save_to_file("examples/contracts_blockchain.json")
    
    # Save contract information
    contract_info = {
        'deployed_contracts': {
            'token': token_address,
            'voting': voting_address, 
            'multisig': multisig_address,
            'savings': savings_address if 'savings_address' in locals() else None
        },
        'deployment_summary': {
            'total_contracts': len(all_contracts),
            'total_events': sum(len(c.events) for c in all_contracts.values()),
            'deployment_time': time.time()
        }
    }
    
    with open("examples/contract_addresses.json", "w") as f:
        json.dump(contract_info, f, indent=2)
    
    print(f"✅ Blockchain saved to examples/contracts_blockchain.json")
    print(f"✅ Contract addresses saved to examples/contract_addresses.json")
    
    print(f"\n🚀 Smart Contract deployment example completed successfully!")
    print("=" * 65)

if __name__ == "__main__":
    # Ensure examples directory exists
    os.makedirs("examples/wallets", exist_ok=True)
    
    # Run the example
    main()
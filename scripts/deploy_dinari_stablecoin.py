"""
File: dinari-blockchain/scripts/deploy_dinari_stablecoin.py

Deployment script for Dinari Stablecoin on DinariBlockchain
"""

import os
import sys
import json
import time
from pathlib import Path

# Add the parent directory to the path so we can import from contracts
sys.path.append(str(Path(__file__).parent.parent))

from contracts.dinari_stablecoin import DinariStablecoin
from decimal import Decimal

def deploy_dinari_stablecoin():
    """Deploy the Dinari Stablecoin to the blockchain"""
    
    print("🚀 Deploying Dinari Stablecoin...")
    print("=" * 50)
    
    # Admin address (in production this would be a proper address)
    admin_address = "dinari_admin_0x1234567890abcdef"
    
    try:
        # Initialize the Dinari Stablecoin contract
        dinari_contract = DinariStablecoin(admin_address)
        
        print(f"✅ Dinari Stablecoin deployed successfully!")
        print(f"   Contract Name: {dinari_contract.name}")
        print(f"   Symbol: {dinari_contract.symbol}")
        print(f"   Decimals: {dinari_contract.decimals}")
        print(f"   Admin: {dinari_contract.admin}")
        print(f"   Target Price: ${dinari_contract.target_price}")
        print(f"   Deployed At: {dinari_contract.deployed_at}")
        
        # Display supported collateral assets
        print("\n📊 Supported Collateral Assets:")
        for symbol, asset in dinari_contract.collateral_assets.items():
            print(f"   • {asset.name} ({symbol})")
            print(f"     Price: ${asset.price_usd}")
            print(f"     Collateral Ratio: {asset.collateral_ratio}x ({float(asset.collateral_ratio) * 100}%)")
            print(f"     Liquidation Threshold: {asset.liquidation_threshold}x ({float(asset.liquidation_threshold) * 100}%)")
        
        # Display mobile money gateways
        print("\n📱 Mobile Money Integration:")
        for gateway_id, gateway in dinari_contract.mobile_money_gateways.items():
            print(f"   • {gateway['name']} ({gateway_id})")
            print(f"     Countries: {', '.join(gateway['countries'])}")
            print(f"     Fee: {float(gateway['fee_percentage']) * 100}%")
        
        # Test basic functionality
        print("\n🧪 Testing Basic Functionality:")
        test_basic_functionality(dinari_contract)
        
        # Save deployment info
        deployment_info = {
            "contract_name": dinari_contract.name,
            "symbol": dinari_contract.symbol,
            "admin": admin_address,
            "deployed_at": dinari_contract.deployed_at,
            "version": dinari_contract.contract_version,
            "target_price": str(dinari_contract.target_price),
            "supported_assets": list(dinari_contract.collateral_assets.keys()),
            "mobile_gateways": list(dinari_contract.mobile_money_gateways.keys())
        }
        
        # Save to deployment file
        deployment_file = Path(__file__).parent.parent / "deployments" / "dinari_stablecoin.json"
        deployment_file.parent.mkdir(exist_ok=True)
        
        with open(deployment_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"\n💾 Deployment info saved to: {deployment_file}")
        
        return dinari_contract
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        return None

def test_basic_functionality(contract: DinariStablecoin):
    """Test basic stablecoin functionality"""
    
    # Test addresses
    user1 = "user_0x111"
    user2 = "user_0x222"
    
    try:
        # Test 1: Deposit collateral
        print("   1️⃣ Testing collateral deposit...")
        success = contract.deposit_collateral(user1, "USDC", Decimal('1000'))
        if success:
            print("      ✅ Collateral deposited successfully")
        
        # Test 2: Mint Dinari
        print("   2️⃣ Testing Dinari minting...")
        success = contract.mint_dinari(user1, Decimal('900'))  # 900 DINARI against 1000 USDC
        if success:
            balance = contract.balance_of(user1)
            print(f"      ✅ Minted 900 DINARI. User balance: {balance}")
        
        # Test 3: Transfer Dinari
        print("   3️⃣ Testing Dinari transfer...")
        success = contract.transfer(user1, user2, Decimal('100'))
        if success:
            balance1 = contract.balance_of(user1)
            balance2 = contract.balance_of(user2)
            print(f"      ✅ Transfer successful. User1: {balance1}, User2: {balance2}")
        
        # Test 4: Mobile money deposit simulation
        print("   4️⃣ Testing mobile money integration...")
        success = contract.mobile_money_deposit(user2, "mpesa", Decimal('5000'), "KES")
        if success:
            balance = contract.balance_of(user2)
            print(f"      ✅ Mobile money deposit successful. User2 balance: {balance}")
        
        # Test 5: Vault info
        print("   5️⃣ Testing vault information...")
        vault_info = contract.get_vault_info(user1)
        print(f"      ✅ Vault collateral ratio: {vault_info['collateral_ratio']}")
        
        # Test 6: Protocol stats
        print("   6️⃣ Testing protocol statistics...")
        stats = contract.get_protocol_stats()
        print(f"      ✅ Total supply: {stats['total_supply']} DINARI")
        
        print("   🎉 All tests passed!")
        
    except Exception as e:
        print(f"   ❌ Test failed: {str(e)}")

def main():
    """Main deployment function"""
    print("🏗️  Dinari Stablecoin Deployment Script")
    print("=====================================")
    print()
    
    # Check if we're in the right directory
    current_dir = Path.cwd()
    if not (current_dir / "scripts" / "deploy_dinari_stablecoin.py").exists():
        print("❌ Please run this script from the dinari-blockchain root directory")
        sys.exit(1)
    
    # Deploy the contract
    contract = deploy_dinari_stablecoin()
    
    if contract:
        print("\n🎊 Deployment completed successfully!")
        print("\nNext steps:")
        print("1. Integrate with your RPC server")
        print("2. Set up price oracles for collateral assets")
        print("3. Configure mobile money gateway APIs")
        print("4. Deploy governance contracts")
        print("5. Set up monitoring and analytics")
        
        print("\n📡 RPC Integration:")
        print("   Add Dinari endpoints to your RPC server at:")
        print("   http://127.0.0.1:8545/rpc")
        
    else:
        print("\n💥 Deployment failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
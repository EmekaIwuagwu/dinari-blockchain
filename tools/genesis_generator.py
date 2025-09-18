#!/usr/bin/env python3
"""
DinariBlockchain Genesis Generator
genesis_generator.py - Creates genesis.json configuration files
"""

import json
import time
import argparse
from typing import Dict, Any, List
from datetime import datetime

class GenesisGenerator:
    """Generates genesis.json files for DinariBlockchain"""
    
    @staticmethod
    def create_genesis_config(
        token_name: str = "Dinari",
        token_symbol: str = "DNMR", 
        total_supply: str = "100000000",
        decimals: int = 18,
        block_time: int = 30,
        validators: List[str] = None,
        initial_allocation: Dict[str, str] = None,
        network_type: str = "mainnet"
    ) -> Dict[str, Any]:
        """Create genesis configuration"""
        
        if validators is None:
            validators = ["validator1", "validator2", "validator3"]
        
        if initial_allocation is None:
            initial_allocation = {
                "treasury": "50000000",      # 50% - Treasury for ecosystem development
                "development": "20000000",   # 20% - Development fund
                "community": "20000000",     # 20% - Community programs and incentives  
                "team": "10000000"          # 10% - Team allocation
            }
        
        # Validate total allocation equals total supply
        total_allocated = sum(int(amount) for amount in initial_allocation.values())
        if total_allocated != int(total_supply):
            raise ValueError(f"Total allocation ({total_allocated}) doesn't match total supply ({total_supply})")
        
        genesis_config = {
            # Network identification
            "network_id": f"Dinari-{network_type}",
            "chain_id": {
                "mainnet": 1001,
                "testnet": 1002, 
                "devnet": 1003
            }.get(network_type, 1001),
            
            # Token configuration
            "token": {
                "name": token_name,
                "symbol": token_symbol,
                "total_supply": total_supply,
                "decimals": decimals,
                "description": "Dinari - A blockchain-based stablecoin for Africa"
            },
            
            # Genesis block configuration
            "genesis_block": {
                "timestamp": int(time.time()),
                "validator": "genesis",
                "previous_hash": "0" * 64,
                "version": "1.0.0",
                "created_by": "DinariBlockchain Genesis Generator"
            },
            
            # Consensus configuration
            "consensus": {
                "type": "proof_of_authority",
                "block_time": block_time,
                "validators": validators,
                "min_validators": max(1, len(validators) // 2 + 1),  # Minimum for consensus
                "validator_rotation": True,
                "epoch_length": 100  # Blocks per epoch
            },
            
            # Initial token allocation
            "initial_allocation": initial_allocation,
            
            # Network configuration
            "network": {
                "p2p_port": 8333,
                "rpc_port": 8334,
                "max_peers": 50,
                "discovery_interval": 30,
                "bootstrap_nodes": [
                    "127.0.0.1:8333",
                    "127.0.0.1:8433",
                    "127.0.0.1:8533"
                ]
            },
            
            # Transaction configuration
            "transaction_config": {
                "min_fee": "0.001",
                "max_tx_per_block": 100,
                "max_tx_size": 1024,  # bytes
                "gas_limit": 10000000
            },
            
            # Smart contract configuration
            "contracts": {
                "enabled": True,
                "max_contract_size": 65536,  # bytes
                "execution_timeout": 5000,   # milliseconds
                "supported_languages": ["python"]
            },
            
            # Economic parameters
            "economics": {
                "target_inflation": "2.0",  # Annual percentage
                "staking_enabled": False,   # Future feature
                "governance_enabled": False # Future feature
            },
            
            # Metadata
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "description": "Dinari genesis configuration for African financial inclusion",
                "website": "https://dinari.xyz",
                "repository": "https://github.com/Dinari/blockchain"
            }
        }
        
        return genesis_config
    
    @staticmethod
    def save_genesis(genesis_config: Dict[str, Any], filename: str = "genesis.json"):
        """Save genesis configuration to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(genesis_config, f, indent=2, sort_keys=True)
            
            print(f"✅ Genesis configuration saved to {filename}")
            print(f"   Network: {genesis_config['network_id']}")
            print(f"   Token: {genesis_config['token']['name']} ({genesis_config['token']['symbol']})")
            print(f"   Total Supply: {genesis_config['token']['total_supply']}")
            print(f"   Validators: {len(genesis_config['consensus']['validators'])}")
            
        except Exception as e:
            print(f"❌ Error saving genesis file: {e}")
    
    @staticmethod
    def load_genesis(filename: str = "genesis.json") -> Dict[str, Any]:
        """Load genesis configuration from file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Genesis file {filename} not found")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in genesis file: {e}")
            return {}
    
    @staticmethod
    def validate_genesis(genesis_config: Dict[str, Any]) -> bool:
        """Validate genesis configuration"""
        try:
            # Required fields
            required_fields = ['network_id', 'token', 'consensus', 'initial_allocation']
            for field in required_fields:
                if field not in genesis_config:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            # Validate token configuration
            token_config = genesis_config['token']
            if not all(key in token_config for key in ['name', 'symbol', 'total_supply']):
                print("❌ Invalid token configuration")
                return False
            
            # Validate initial allocation
            allocation = genesis_config['initial_allocation']
            total_supply = int(genesis_config['token']['total_supply'])
            total_allocated = sum(int(amount) for amount in allocation.values())
            
            if total_allocated != total_supply:
                print(f"❌ Allocation mismatch: {total_allocated} != {total_supply}")
                return False
            
            # Validate validators
            validators = genesis_config['consensus']['validators']
            if len(validators) < 1:
                print("❌ At least one validator required")
                return False
            
            print("✅ Genesis configuration is valid")
            return True
            
        except Exception as e:
            print(f"❌ Genesis validation error: {e}")
            return False
    
    @staticmethod
    def print_genesis_summary(genesis_config: Dict[str, Any]):
        """Print human-readable summary of genesis configuration"""
        print("\n" + "="*60)
        print("Dinari GENESIS CONFIGURATION SUMMARY")
        print("="*60)
        
        # Network info
        print(f"🌍 Network ID: {genesis_config['network_id']}")
        print(f"🔗 Chain ID: {genesis_config['chain_id']}")
        
        # Token info
        token = genesis_config['token']
        print(f"\n💰 Token Information:")
        print(f"   Name: {token['name']}")
        print(f"   Symbol: {token['symbol']}")
        print(f"   Total Supply: {token['total_supply']:,} {token['symbol']}")
        print(f"   Decimals: {token['decimals']}")
        
        # Consensus info
        consensus = genesis_config['consensus']
        print(f"\n⚡ Consensus Configuration:")
        print(f"   Type: {consensus['type'].replace('_', ' ').title()}")
        print(f"   Block Time: {consensus['block_time']} seconds")
        print(f"   Validators: {len(consensus['validators'])}")
        for i, validator in enumerate(consensus['validators'], 1):
            print(f"     {i}. {validator}")
        
        # Initial allocation
        allocation = genesis_config['initial_allocation']
        print(f"\n💸 Initial Token Allocation:")
        total_supply = int(genesis_config['token']['total_supply'])
        for address, amount in allocation.items():
            percentage = (int(amount) / total_supply) * 100
            print(f"   {address.capitalize()}: {int(amount):,} DNMR ({percentage:.1f}%)")
        
        # Network configuration
        network = genesis_config['network']
        print(f"\n🌐 Network Configuration:")
        print(f"   P2P Port: {network['p2p_port']}")
        print(f"   RPC Port: {network['rpc_port']}")
        print(f"   Max Peers: {network['max_peers']}")
        print(f"   Bootstrap Nodes: {len(network['bootstrap_nodes'])}")
        
        print("\n" + "="*60)

def create_mainnet_genesis():
    """Create mainnet genesis configuration"""
    return GenesisGenerator.create_genesis_config(
        network_type="mainnet",
        validators=[
            "0xDinari_Validator_Nigeria",
            "0xDinari_Validator_Kenya", 
            "0xDinari_Validator_SouthAfrica",
            "0xDinari_Validator_Ghana",
            "0xDinari_Validator_Egypt"
        ],
        initial_allocation={
            "treasury": "40000000",         # 40% - Treasury
            "development": "15000000",      # 15% - Development 
            "community": "25000000",        # 25% - Community programs
            "partnerships": "10000000",     # 10% - Strategic partnerships
            "team": "10000000"             # 10% - Team
        }
    )

def create_testnet_genesis():
    """Create testnet genesis configuration"""
    return GenesisGenerator.create_genesis_config(
        network_type="testnet",
        total_supply="50000000",
        validators=["test_validator_1", "test_validator_2", "test_validator_3"],
        block_time=15,  # Faster blocks for testing
        initial_allocation={
            "faucet": "30000000",          # 60% - Test faucet
            "developers": "10000000",       # 20% - Developer testing
            "community": "10000000"        # 20% - Community testing
        }
    )

def create_devnet_genesis():
    """Create development network genesis configuration"""
    return GenesisGenerator.create_genesis_config(
        network_type="devnet", 
        total_supply="10000000",
        validators=["dev_node_1", "dev_node_2"],
        block_time=5,  # Very fast blocks for development
        initial_allocation={
            "developer": "5000000",        # 50% - Single developer
            "testing": "5000000"           # 50% - Testing accounts
        }
    )

def main():
    """Command line interface for genesis generator"""
    parser = argparse.ArgumentParser(description="DinariBlockchain Genesis Generator")
    parser.add_argument('--network', choices=['mainnet', 'testnet', 'devnet'], 
                       default='devnet', help='Network type to generate')
    parser.add_argument('--output', default='genesis.json', 
                       help='Output filename for genesis configuration')
    parser.add_argument('--validate', action='store_true', 
                       help='Validate existing genesis file')
    parser.add_argument('--summary', action='store_true',
                       help='Print summary of genesis configuration')
    
    args = parser.parse_args()
    
    if args.validate:
        # Validate existing genesis file
        genesis_config = GenesisGenerator.load_genesis(args.output)
        if genesis_config:
            GenesisGenerator.validate_genesis(genesis_config)
            if args.summary:
                GenesisGenerator.print_genesis_summary(genesis_config)
    else:
        # Generate new genesis configuration
        print(f"🚀 Generating {args.network} genesis configuration...")
        
        if args.network == 'mainnet':
            genesis_config = create_mainnet_genesis()
        elif args.network == 'testnet': 
            genesis_config = create_testnet_genesis()
        else:  # devnet
            genesis_config = create_devnet_genesis()
        
        # Validate before saving
        if GenesisGenerator.validate_genesis(genesis_config):
            GenesisGenerator.save_genesis(genesis_config, args.output)
            
            if args.summary:
                GenesisGenerator.print_genesis_summary(genesis_config)
        else:
            print("❌ Genesis configuration validation failed")

if __name__ == "__main__":
    main()
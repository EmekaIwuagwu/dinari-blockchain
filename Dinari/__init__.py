#!/usr/bin/env python3
"""
DinariBlockchain Package
Dinari/__init__.py - Package initialization and public API
"""

__version__ = "1.0.0"
__author__ = "DinariBlockchain Team"
__description__ = "A blockchain-based stablecoin for Africa"
__url__ = "https://github.com/Dinari/blockchain"

# Core blockchain components
from .blockchain import (
    Transaction,
    Block, 
    SmartContract,
    DinariBlockchain
)

# Consensus mechanism
from .consensus import (
    ProofOfAuthority,
    ConsensusType,
    ValidatorInfo,
    ConsensusConfig,
    create_default_poa_config,
    create_fast_poa_config
)

# Smart contracts
from .contracts import (
    DinariSmartContract,
    ContractManager,
    ContractExecution,
    ContractDeployment,
    SafePythonExecutor,
    ContractExecutionError
)

# Networking
from .network import (
    P2PNetworkManager,
    P2PConnection,
    NetworkMessage,
    MessageType,
    PeerInfo,
    NetworkStats
)

# Node implementation
from .node import (
    DinariNode
)

# Wallet functionality
from .wallet import (
    DinariWallet,
    KeyPair,
    create_wallet,
    load_wallet
)

# Convenience imports for common use cases
__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__description__',
    '__url__',
    
    # Core blockchain
    'Transaction',
    'Block',
    'SmartContract', 
    'DinariBlockchain',
    
    # Consensus
    'ProofOfAuthority',
    'ConsensusType',
    'ValidatorInfo',
    'ConsensusConfig',
    'create_default_poa_config',
    'create_fast_poa_config',
    
    # Smart contracts
    'DinariSmartContract',
    'ContractManager',
    'ContractExecution',
    'ContractDeployment',
    'SafePythonExecutor',
    'ContractExecutionError',
    
    # Networking
    'P2PNetworkManager',
    'P2PConnection',
    'NetworkMessage',
    'MessageType',
    'PeerInfo',
    'NetworkStats',
    
    # Node
    'DinariNode',
    
    # Wallet
    'DinariWallet',
    'KeyPair',
    'create_wallet',
    'load_wallet',
    
    # Utility functions
    'create_test_blockchain',
    'create_test_network',
    'deploy_example_contract'
]

# Package-level configuration
import logging

# Setup default logging for the package
def setup_logging(level=logging.INFO, format_string=None):
    """Setup logging configuration for DinariBlockchain"""
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set specific loggers
    loggers = [
        'DinariBlockchain',
        'DinariNode',
        'DinariWallet',
        'ProofOfAuthority',
        'ContractManager',
        'P2PNetwork'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

# Utility functions for easy setup
def create_test_blockchain(total_supply: str = "1000000", validators: list = None):
    """Create a test blockchain instance"""
    if validators is None:
        validators = ["test_validator_1", "test_validator_2"]
    
    genesis_config = {
        'token_name': 'TestDinari',
        'token_symbol': 'TDINARI', 
        'total_supply': total_supply,
        'decimals': 18,
        'validators': validators,
        'block_time': 5,  # Fast blocks for testing
        'initial_allocation': {
            'treasury': str(int(int(total_supply) * 0.5)),
            'test_account': str(int(int(total_supply) * 0.3)),
            'dev_fund': str(int(int(total_supply) * 0.2))
        }
    }
    
    return DinariBlockchain(genesis_config)

def create_test_network(num_nodes: int = 3, base_port: int = 8333):
    """Create a test network with multiple nodes"""
    nodes = []
    
    for i in range(num_nodes):
        node_id = f"test_node_{i+1}"
        port = base_port + i
        
        # Create node
        node = DinariNode(
            node_id=node_id,
            host="127.0.0.1",
            port=port,
            genesis_file="genesis.json",
            data_dir="test_data"
        )
        
        nodes.append(node)
    
    return nodes

def deploy_example_contract(blockchain, contract_type: str = "token", deployer: str = "treasury"):
    """Deploy an example smart contract"""
    
    contract_manager = ContractManager(blockchain)
    
    if contract_type == "token":
        # Deploy token contract
        deployment = contract_manager.deploy_from_template(
            'token',
            deployer,
            ['ExampleToken', 'EXT', '1000000']
        )
        return deployment.address
        
    elif contract_type == "voting":
        # Deploy voting contract
        deployment = contract_manager.deploy_from_template(
            'voting', 
            deployer,
            ['Test Vote', ['Option A', 'Option B', 'Option C'], 86400]  # 1 day voting period
        )
        return deployment.address
        
    elif contract_type == "multisig":
        # Deploy multisig contract
        owners = ['treasury', 'admin1', 'admin2']
        deployment = contract_manager.deploy_from_template(
            'multisig',
            deployer, 
            [owners, 2]  # Require 2 signatures
        )
        return deployment.address
    
    else:
        raise ValueError(f"Unknown contract type: {contract_type}")

# Package information
def get_package_info():
    """Get package information"""
    return {
        'name': 'DinariBlockchain',
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'url': __url__,
        'components': {
            'blockchain': 'Core blockchain with transactions and blocks',
            'consensus': 'Proof of Authority consensus mechanism',
            'contracts': 'Python-based smart contract system', 
            'network': 'P2P networking for node communication',
            'wallet': 'Key management and transaction creation',
            'node': 'Complete blockchain node implementation'
        },
        'features': {
            'smart_contracts': True,
            'proof_of_authority': True,
            'p2p_networking': True,
            'wallet_support': True,
            'african_focused': True,
            'low_transaction_costs': True,
            'regulatory_compliance': True
        }
    }

# Development and testing utilities
class DinariTestSuite:
    """Test suite for DinariBlockchain development"""
    
    @staticmethod
    def run_basic_tests():
        """Run basic functionality tests"""
        print("🧪 Running DinariBlockchain Basic Tests")
        print("=" * 50)
        
        try:
            # Test 1: Create blockchain
            print("1️⃣ Creating test blockchain...")
            blockchain = create_test_blockchain()
            assert len(blockchain.chain) == 1  # Genesis block
            print("✅ Blockchain created successfully")
            
            # Test 2: Create transaction
            print("2️⃣ Creating test transaction...")
            tx = Transaction("treasury", "test_account", "100", "0.1")
            assert tx.is_valid()
            print("✅ Transaction created successfully")
            
            # Test 3: Add transaction to blockchain
            print("3️⃣ Adding transaction to blockchain...")
            success = blockchain.add_transaction(tx)
            assert success
            print("✅ Transaction added successfully")
            
            # Test 4: Mine block
            print("4️⃣ Mining block...")
            blockchain.add_validator("test_miner")
            block = blockchain.mine_block("test_miner")
            assert block is not None
            assert len(blockchain.chain) == 2
            print("✅ Block mined successfully")
            
            # Test 5: Check balances
            print("5️⃣ Checking balances...")
            treasury_balance = blockchain.get_balance("treasury")
            test_balance = blockchain.get_balance("test_account")
            assert treasury_balance > 0
            print(f"✅ Balances: Treasury={treasury_balance}, Test={test_balance}")
            
            print("\n🎉 All basic tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    @staticmethod
    def run_contract_tests():
        """Run smart contract tests"""
        print("🧪 Running Smart Contract Tests")
        print("=" * 40)
        
        try:
            # Create blockchain and contract manager
            blockchain = create_test_blockchain()
            contract_manager = ContractManager(blockchain)
            
            # Deploy token contract
            print("📦 Deploying token contract...")
            deployment = contract_manager.deploy_from_template(
                'token', 'treasury', ['TestToken', 'TT', '1000000']
            )
            print(f"✅ Token contract deployed: {deployment.address}")
            
            # Test token functions
            print("💰 Testing token functions...")
            result = contract_manager.call_contract(
                deployment.address, 'balance_of', ['treasury'], 'treasury'
            )
            assert result.success
            print(f"✅ Token balance: {result.result}")
            
            print("\n🎉 Contract tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Contract test failed: {e}")
            return False

# Initialize package
def initialize_Dinari(log_level=logging.INFO):
    """Initialize the DinariBlockchain package"""
    setup_logging(log_level)
    logger = logging.getLogger("DinariBlockchain")
    logger.info(f"DinariBlockchain v{__version__} initialized")
    
    info = get_package_info()
    logger.info(f"Components loaded: {list(info['components'].keys())}")

# Auto-initialize when imported (can be disabled by setting environment variable)
import os
if not os.getenv('Dinari_NO_AUTO_INIT'):
    initialize_Dinari()

# Quick start example
def quick_start_example():
    """Quick start example for new users"""
    print("🚀 DinariBlockchain Quick Start Example")
    print("=" * 45)
    
    # Create blockchain
    blockchain = create_test_blockchain("10000000")  # 10M tokens
    print(f"✅ Created blockchain with {len(blockchain.validators)} validators")
    
    # Create wallet
    wallet = create_wallet("example_wallet")
    alice_addr = wallet.create_new_address("alice")
    print(f"✅ Created wallet with address: {alice_addr[:20]}...")
    
    # Send some tokens to Alice
    tx = Transaction("treasury", alice_addr, "1000", "0.1")
    blockchain.add_transaction(tx)
    
    # Mine block
    block = blockchain.mine_block(blockchain.validators[0])
    print(f"✅ Mined block {block.index} with {len(block.transactions)} transactions")
    
    # Check balance
    alice_balance = blockchain.get_balance(alice_addr)
    print(f"✅ Alice's balance: {alice_balance} DINARI")
    
    # Deploy smart contract
    contract_addr = deploy_example_contract(blockchain, "token", "treasury")
    print(f"✅ Deployed smart contract: {contract_addr[:20]}...")
    
    print("\n🎉 Quick start completed! Check the examples/ folder for more.")

if __name__ == "__main__":
    # Run when called directly
    print(f"DinariBlockchain v{__version__}")
    print(__description__)
    print()
    
    # Show package info
    info = get_package_info()
    print("📦 Package Information:")
    for key, value in info.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"     {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")
    
    # Run quick start
    print()
    quick_start_example()

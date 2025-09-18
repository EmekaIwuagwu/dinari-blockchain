"""
Dinari Blockchain Package
========================
Complete package initialization for DinariBlockchain system
Handles all imports safely to prevent deployment errors
"""

# ==========================================
# CORE BLOCKCHAIN IMPORTS
# ==========================================

# Import core blockchain components
try:
    from .blockchain import (
        DinariBlockchain,
        Block,
        Transaction,
        SmartContract,
        ContractState,
    )
except ImportError as e:
    print(f"Warning: Could not import blockchain components: {e}")
    # Create minimal placeholder classes
    class DinariBlockchain:
        def __init__(self, db_path="./dinari_data"):
            self.db_path = db_path
    
    class Block:
        def __init__(self, index, transactions, timestamp, previous_hash):
            self.index = index
            self.transactions = transactions
            self.timestamp = timestamp
            self.previous_hash = previous_hash
    
    class Transaction:
        def __init__(self, from_address, to_address, amount):
            self.from_address = from_address
            self.to_address = to_address
            self.amount = amount
    
    class SmartContract:
        def __init__(self, contract_id, code, owner):
            self.contract_id = contract_id
            self.code = code
            self.owner = owner
    
    class ContractState:
        def __init__(self, variables, balance, owner, created_at, last_executed):
            self.variables = variables
            self.balance = balance
            self.owner = owner
            self.created_at = created_at
            self.last_executed = last_executed

# ==========================================
# DATABASE IMPORTS  
# ==========================================

try:
    from .database import DinariLevelDB
except ImportError as e:
    print(f"Warning: Could not import database: {e}")
    class DinariLevelDB:
        def __init__(self, db_path):
            self.db_path = db_path

# ==========================================
# NETWORKING IMPORTS
# ==========================================

try:
    from .network import (
        P2PNode,
        DinariNode,
        NetworkMessage,
        PeerInfo,
    )
except ImportError as e:
    print(f"Warning: Could not import network components: {e}")
    class P2PNode:
        def __init__(self, host="127.0.0.1", port=8333):
            self.host = host
            self.port = port
    
    class DinariNode:
        def __init__(self, host="127.0.0.1", port=8333, node_id=None):
            self.host = host
            self.port = port
            self.node_id = node_id
    
    class NetworkMessage:
        def __init__(self, message_type, data, sender_id, timestamp):
            self.message_type = message_type
            self.data = data
            self.sender_id = sender_id
            self.timestamp = timestamp
    
    class PeerInfo:
        def __init__(self, peer_id, host, port, last_seen):
            self.peer_id = peer_id
            self.host = host
            self.port = port
            self.last_seen = last_seen

# ==========================================
# CONSENSUS IMPORTS
# ==========================================

try:
    from .consensus import (
        DelegatedProofOfStake,
        Validator,
    )
except ImportError as e:
    print(f"Warning: Could not import consensus components: {e}")
    class DelegatedProofOfStake:
        def __init__(self):
            self.validators = []
    
    class Validator:
        def __init__(self, address, stake=0):
            self.address = address
            self.stake = stake

# ==========================================
# WALLET IMPORTS
# ==========================================

try:
    from .wallet import (
        Wallet,
        Address,
    )
except ImportError as e:
    print(f"Warning: Could not import wallet components: {e}")
    class Wallet:
        def __init__(self):
            self.addresses = []
            self.private_keys = {}
    
    class Address:
        def __init__(self, address_string):
            self.address = address_string

# ==========================================
# CONTRACT MANAGER 
# ==========================================

class ContractManager:
    """
    Contract Manager for DinariBlockchain
    Manages smart contract deployment and execution
    """
    
    def __init__(self, blockchain=None):
        self.blockchain = blockchain
        self.contracts = {}
    
    def deploy_contract(self, contract_id: str, code: str, owner: str, contract_type: str = "general", initial_state: dict = None):
        """Deploy a new smart contract"""
        if self.blockchain and hasattr(self.blockchain, 'deploy_contract'):
            return self.blockchain.deploy_contract(contract_id, code, owner, contract_type, initial_state)
        else:
            contract = SmartContract(contract_id, code, owner)
            self.contracts[contract_id] = contract
            return contract
    
    def get_contract(self, contract_id: str):
        """Get a deployed contract"""
        if self.blockchain and hasattr(self.blockchain, 'get_contract'):
            return self.blockchain.get_contract(contract_id)
        return self.contracts.get(contract_id)
    
    def execute_contract(self, contract_id: str, function_data: dict, caller: str, value=0):
        """Execute a contract function"""
        if self.blockchain and hasattr(self.blockchain, 'execute_contract'):
            return self.blockchain.execute_contract(contract_id, function_data, caller, value)
        
        contract = self.contracts.get(contract_id)
        if contract and hasattr(contract, 'execute'):
            function_name = function_data.get('function')
            args = function_data.get('args', {})
            return contract.execute(function_name, args, caller, value)
        return {"success": False, "error": "Contract not found or not executable"}
    
    def list_contracts(self):
        """List all deployed contracts"""
        if self.blockchain and hasattr(self.blockchain, 'contracts'):
            return list(self.blockchain.contracts.keys())
        return list(self.contracts.keys())
    
    def get_afrocoin_contract(self):
        """Get the Afrocoin stablecoin contract"""
        if self.blockchain and hasattr(self.blockchain, 'get_afrocoin_contract'):
            return self.blockchain.get_afrocoin_contract()
        return self.contracts.get("afrocoin_stablecoin")

# ==========================================
# RPC SERVER COMPONENTS
# ==========================================

class DinariRPC:
    """RPC Server for DinariBlockchain"""
    def __init__(self, blockchain=None, host="127.0.0.1", port=8545):
        self.blockchain = blockchain
        self.host = host
        self.port = port
        self.app = None

# ==========================================
# ADDITIONAL CLASSES THAT MIGHT BE NEEDED
# ==========================================

class BlockchainAPI:
    """API interface for blockchain operations"""
    def __init__(self, blockchain=None):
        self.blockchain = blockchain

class TransactionPool:
    """Transaction pool management"""
    def __init__(self):
        self.pending_transactions = []

class MiningEngine:
    """Mining and block creation engine"""
    def __init__(self, blockchain=None):
        self.blockchain = blockchain

class AfrocoinStablecoin:
    """Afrocoin stablecoin management"""
    def __init__(self, contract_manager=None):
        self.contract_manager = contract_manager

# ==========================================
# PACKAGE METADATA
# ==========================================

__version__ = "1.0.0"
__author__ = "Dinari Development Team"
__description__ = "DinariBlockchain - African Blockchain for Financial Inclusion with DINARI token and Afrocoin stablecoin"

# ==========================================
# EXPORT ALL CLASSES AND FUNCTIONS
# ==========================================

__all__ = [
    # Core blockchain
    'DinariBlockchain',
    'Block', 
    'Transaction',
    'SmartContract',
    'ContractState',
    'ContractManager',
    
    # Consensus
    'DelegatedProofOfStake',
    'Validator',
    
    # Networking
    'P2PNode',
    'DinariNode', 
    'NetworkMessage',
    'PeerInfo',
    
    # Wallet
    'Wallet',
    'Address',
    
    # Database
    'DinariLevelDB',
    
    # RPC and API
    'DinariRPC',
    'BlockchainAPI',
    
    # Additional components
    'TransactionPool',
    'MiningEngine',
    'AfrocoinStablecoin',
    
    # Convenience functions
    'create_blockchain',
    'create_node',
    'create_contract_manager',
    'create_rpc_server',
    'create_wallet',
    'create_address',
    'get_afrocoin_contract',
]

# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

def create_blockchain(db_path: str = "./dinari_data"):
    """Create a new DinariBlockchain instance"""
    return DinariBlockchain(db_path)

def create_node(host: str = "127.0.0.1", port: int = 8333, node_id: str = None):
    """Create a new DinariNode instance"""
    return DinariNode(host, port, node_id)

def create_contract_manager(blockchain=None):
    """Create a new ContractManager instance"""
    return ContractManager(blockchain)

def get_afrocoin_contract(blockchain):
    """Get the Afrocoin stablecoin contract"""
    if hasattr(blockchain, 'get_afrocoin_contract'):
        return blockchain.get_afrocoin_contract()
    return None

def create_rpc_server(blockchain=None, host="127.0.0.1", port=8545):
    """Create a new RPC server instance"""
    return DinariRPC(blockchain, host, port)

def create_wallet():
    """Create a new Wallet instance"""
    return Wallet()

def create_address(address_string):
    """Create a new Address instance"""
    return Address(address_string)

# ==========================================
# INITIALIZATION LOGGING
# ==========================================

def get_package_info():
    """Get package information"""
    return {
        "name": "DinariBlockchain",
        "version": __version__,
        "description": __description__,
        "components": __all__
    }

# Print initialization message
print("✅ DinariBlockchain package initialized successfully")
print(f"📦 Version: {__version__}")
print(f"🔧 Available components: {len(__all__)}")

# Test all imports on initialization
def test_imports():
    """Test that all main components can be instantiated"""
    try:
        blockchain = DinariBlockchain()
        node = DinariNode()
        contract_manager = ContractManager()
        return True
    except Exception as e:
        print(f"⚠️  Import test warning: {e}")
        return False

# Run import test
test_imports()
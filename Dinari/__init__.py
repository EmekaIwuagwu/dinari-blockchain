"""
Dinari Blockchain Package
========================
Main package initialization for DinariBlockchain system
"""

# Core blockchain components
from .blockchain import (
    DinariBlockchain,
    Block,
    Transaction,
    SmartContract,
    ContractState,
)

# Consensus mechanism
try:
    from .consensus import (
        DelegatedProofOfStake,
        Validator,
    )
except ImportError:
    # Create placeholder classes if consensus module doesn't exist
    class DelegatedProofOfStake:
        def __init__(self):
            pass
    
    class Validator:
        def __init__(self, address: str):
            self.address = address

# Networking (use correct class names)
from .network import (
    P2PNode,
    DinariNode,
    NetworkMessage,
    PeerInfo,
)

# Wallet functionality
try:
    from .wallet import (
        Wallet,
        Address,
    )
except ImportError:
    # Create placeholder classes if wallet module doesn't exist
    class Wallet:
        def __init__(self):
            pass
    
    class Address:
        def __init__(self, address: str):
            self.address = address

# Database
from .database import DinariLevelDB

# Package metadata
__version__ = "1.0.0"
__author__ = "Dinari Development Team"
__description__ = "DinariBlockchain - African Blockchain for Financial Inclusion"

# Export main classes
__all__ = [
    # Core blockchain
    'DinariBlockchain',
    'Block', 
    'Transaction',
    'SmartContract',
    'ContractState',
    
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
]

# Convenience imports for common use cases
def create_blockchain(db_path: str = "./dinari_data"):
    """Create a new DinariBlockchain instance"""
    return DinariBlockchain(db_path)

def create_node(host: str = "127.0.0.1", port: int = 8333, node_id: str = None):
    """Create a new DinariNode instance"""
    return DinariNode(host, port, node_id)

def get_afrocoin_contract(blockchain: DinariBlockchain):
    """Get the Afrocoin stablecoin contract"""
    return blockchain.get_afrocoin_contract()
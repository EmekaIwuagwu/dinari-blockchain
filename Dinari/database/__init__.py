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
    # SmartContract,  # ← Comment out if this class doesn't exist
)

# Consensus mechanism
from .consensus import (
    DelegatedProofOfStake,
    Validator,
)

# Networking
from .network import (
    P2PNode,
    DinariNode,
)

# Wallet functionality
from .wallet import (
    Wallet,
    Address,
)

# Smart contracts (if they exist in a separate file)
try:
    from .contracts import SmartContract, ContractManager
except ImportError:
    # If contracts.py doesn't exist, create a placeholder
    class SmartContract:
        def __init__(self, name: str):
            self.name = name
            
    class ContractManager:
        def __init__(self):
            self.contracts = {}

# Package metadata
__version__ = "1.0.0"
__author__ = "Dinari Development Team"
__description__ = "African Blockchain for Financial Inclusion"

# Export main classes
__all__ = [
    'DinariBlockchain',
    'Block', 
    'Transaction',
    'SmartContract',
    'DelegatedProofOfStake',
    'Validator',
    'P2PNode',
    'DinariNode',
    'Wallet',
    'Address',
    'ContractManager',
]
"""
Dinari Blockchain with LevelDB Storage
File: dinari/blockchain.py
"""

import hashlib
import json
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext
import logging
from .database import DinariLevelDB

# Set precision for financial calculations
getcontext().prec = 18

@dataclass
class Transaction:
    """Dinari blockchain transaction"""
    from_address: str
    to_address: str
    amount: Decimal
    gas_price: Decimal
    gas_limit: int
    nonce: int
    data: str = ""
    signature: str = ""
    timestamp: int = 0
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = int(time.time())
    
    def to_dict(self) -> dict:
        return {
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": str(self.amount),
            "gas_price": str(self.gas_price),
            "gas_limit": self.gas_limit,
            "nonce": self.nonce,
            "data": self.data,
            "signature": self.signature,
            "timestamp": self.timestamp
        }
    
    def get_hash(self) -> str:
        """Calculate transaction hash"""
        tx_string = f"{self.from_address}{self.to_address}{self.amount}{self.nonce}{self.timestamp}"
        return hashlib.sha256(tx_string.encode()).hexdigest()

@dataclass
class Block:
    """Dinari blockchain block"""
    index: int
    transactions: List[Transaction]
    timestamp: int
    previous_hash: str
    nonce: int = 0
    validator: str = ""
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = int(time.time())
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "validator": self.validator,
            "hash": self.get_hash()
        }
    
    def get_hash(self) -> str:
        """Calculate block hash"""
        block_string = json.dumps({
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "validator": self.validator
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class DinariBlockchain:
    """Main Dinari Blockchain with LevelDB storage"""
    
    def __init__(self, db_path: str = "./dinari_data"):
        self.logger = logging.getLogger("Dinari.blockchain")
        
        # Initialize LevelDB
        self.db = DinariLevelDB(db_path)
        
        # Load or create blockchain state
        self.chain_state = self._load_chain_state()
        self.pending_transactions = []
        self.validators = self._load_validators()
        self.balances = self._load_balances()
        
        # Initialize genesis block if needed
        if self.chain_state["height"] == 0:
            self._create_genesis_block()
            
        self.logger.info(f"DinariBlockchain initialized with {len(self.validators)} validators")
    
    def _load_chain_state(self) -> dict:
        """Load blockchain state from LevelDB"""
        default_state = {
            "height": 0,
            "last_block_hash": "",
            "total_supply": "0",
            "total_transactions": 0
        }
        return self.db.get_chain_state() or default_state
    
    def _save_chain_state(self):
        """Save blockchain state to LevelDB"""
        self.db.store_chain_state(self.chain_state)
    
    def _load_validators(self) -> List[str]:
        """Load validators list"""
        return self.db.get("validators") or []
    
    def _save_validators(self):
        """Save validators list"""
        self.db.put("validators", self.validators)
    
    def _load_balances(self) -> dict:
        """Load account balances"""
        return self.db.get("balances") or {}
    
    def _save_balances(self):
        """Save account balances"""
        self.db.put("balances", self.balances)
    
    def _create_genesis_block(self):
        """Create genesis block with initial allocations"""
        genesis_transactions = [
            Transaction(
                from_address="genesis",
                to_address="dinari1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",  # Example address
                amount=Decimal("1000000"),
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=0,
                data="Genesis allocation"
            ),
            Transaction(
                from_address="genesis", 
                to_address="dinari1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx",
                amount=Decimal("500000"),
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=1,
                data="Initial validator allocation"
            ),
            Transaction(
                from_address="genesis",
                to_address="dinari1cqgze3fqpw0dqh9j8l2dqqyr89c0q5c2jdpg8x",
                amount=Decimal("250000"),
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=2,
                data="Development fund"
            ),
            Transaction(
                from_address="genesis",
                to_address="dinari1xz2f8l8lh8vqw3r6n4s2k7j9p1d5g8h3m6c4v7",
                amount=Decimal("100000"),
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=3,
                data="Community treasury"
            ),
            Transaction(
                from_address="genesis",
                to_address="dinari1a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5",
                amount=Decimal("50000"),
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=4,
                data="Reserve fund"
            )
        ]
        
        genesis_block = Block(
            index=0,
            transactions=genesis_transactions,
            timestamp=int(time.time()),
            previous_hash="0" * 64,
            validator="genesis"
        )
        
        # Process genesis transactions
        for tx in genesis_transactions:
            if tx.to_address not in self.balances:
                self.balances[tx.to_address] = "0"
            current_balance = Decimal(self.balances[tx.to_address])
            self.balances[tx.to_address] = str(current_balance + tx.amount)
        
        # Store genesis block
        block_hash = genesis_block.get_hash()
        self.db.store_block(block_hash, genesis_block.to_dict())
        
        # Update chain state
        self.chain_state["height"] = 1
        self.chain_state["last_block_hash"] = block_hash
        self.chain_state["total_supply"] = str(sum(Decimal(balance) for balance in self.balances.values()))
        self.chain_state["total_transactions"] = len(genesis_transactions)
        
        # Save state
        self._save_chain_state()
        self._save_balances()
        
        self.logger.info(f"Genesis block created with {len(genesis_transactions)} initial allocations")
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add transaction to pending pool"""
        try:
            # Basic validation
            if not self._validate_transaction(transaction):
                return False
            
            self.pending_transactions.append(transaction)
            
            # Store transaction in database
            tx_hash = transaction.get_hash()
            self.db.store_transaction(tx_hash, transaction.to_dict())
            
            self.logger.info(f"Transaction added: {tx_hash}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add transaction: {e}")
            return False
    
    def _validate_transaction(self, tx: Transaction) -> bool:
        """Validate transaction"""
        try:
            # Check balance (skip for genesis)
            if tx.from_address != "genesis":
                sender_balance = Decimal(self.balances.get(tx.from_address, "0"))
                if sender_balance < tx.amount:
                    self.logger.warning(f"Insufficient balance: {tx.from_address}")
                    return False
            
            # Basic format validation
            if tx.amount < 0:
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Transaction validation error: {e}")
            return False
    
    def create_block(self, validator_address: str) -> Optional[Block]:
        """Create new block with pending transactions"""
        try:
            if not self.pending_transactions:
                return None
            
            new_block = Block(
                index=self.chain_state["height"],
                transactions=self.pending_transactions.copy(),
                timestamp=int(time.time()),
                previous_hash=self.chain_state["last_block_hash"],
                validator=validator_address
            )
            
            # Process transactions
            self._process_transactions(new_block.transactions)
            
            # Store block
            block_hash = new_block.get_hash()
            self.db.store_block(block_hash, new_block.to_dict())
            
            # Update chain state
            self.chain_state["height"] += 1
            self.chain_state["last_block_hash"] = block_hash
            self.chain_state["total_transactions"] += len(new_block.transactions)
            self.chain_state["total_supply"] = str(sum(Decimal(balance) for balance in self.balances.values()))
            
            # Clear pending transactions
            self.pending_transactions = []
            
            # Save state
            self._save_chain_state()
            self._save_balances()
            
            self.logger.info(f"Block {new_block.index} created with {len(new_block.transactions)} transactions")
            return new_block
            
        except Exception as e:
            self.logger.error(f"Failed to create block: {e}")
            return None
    
    def _process_transactions(self, transactions: List[Transaction]):
        """Process transactions and update balances"""
        for tx in transactions:
            if tx.from_address != "genesis":
                # Debit sender
                sender_balance = Decimal(self.balances.get(tx.from_address, "0"))
                self.balances[tx.from_address] = str(sender_balance - tx.amount)
            
            # Credit recipient
            if tx.to_address not in self.balances:
                self.balances[tx.to_address] = "0"
            recipient_balance = Decimal(self.balances[tx.to_address])
            self.balances[tx.to_address] = str(recipient_balance + tx.amount)
    
    def get_block_by_hash(self, block_hash: str) -> Optional[dict]:
        """Get block by hash"""
        return self.db.get_block(block_hash)
    
    def get_transaction_by_hash(self, tx_hash: str) -> Optional[dict]:
        """Get transaction by hash"""
        return self.db.get_transaction(tx_hash)
    
    def get_balance(self, address: str) -> Decimal:
        """Get account balance"""
        return Decimal(self.balances.get(address, "0"))
    
    def get_chain_info(self) -> dict:
        """Get blockchain information"""
        return {
            "height": self.chain_state["height"],
            "last_block_hash": self.chain_state["last_block_hash"],
            "total_supply": self.chain_state["total_supply"],
            "total_transactions": self.chain_state["total_transactions"],
            "pending_transactions": len(self.pending_transactions),
            "validators": len(self.validators)
        }
    
    def add_validator(self, validator_address: str):
        """Add validator"""
        if validator_address not in self.validators:
            self.validators.append(validator_address)
            self._save_validators()
            self.logger.info(f"Validator added: {validator_address}")
    
    def close(self):
        """Close database connection"""
        self.db.close()
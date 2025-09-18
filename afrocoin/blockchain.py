#!/usr/bin/env python3
"""
DinariBlockchain - Core Implementation
blockchain.py - Contains the fundamental blockchain, transaction, and block classes
"""

import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext
import logging

# Set precision for financial calculations
getcontext().prec = 18

@dataclass
class Transaction:
    """Transaction structure for Dinari blockchain"""
    from_address: str
    to_address: str
    amount: str  # Use string for precise decimal handling
    fee: str = "0.001"
    data: str = ""  # For smart contract calls or additional data
    nonce: int = 0
    timestamp: float = None
    signature: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def calculate_hash(self) -> str:
        """Calculate unique hash for this transaction"""
        tx_string = (f"{self.from_address}{self.to_address}{self.amount}"
                    f"{self.fee}{self.data}{self.nonce}{self.timestamp}")
        return hashlib.sha256(tx_string.encode('utf-8')).hexdigest()
    
    def is_valid(self) -> bool:
        """Basic transaction validation"""
        try:
            # Check amount and fee are valid decimals
            Decimal(self.amount)
            Decimal(self.fee)
            
            # Check addresses are not empty
            if not self.from_address or not self.to_address:
                return False
            
            # Check amount is positive
            if Decimal(self.amount) <= 0:
                return False
                
            return True
        except:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create transaction from dictionary"""
        return cls(**data)

@dataclass
class Block:
    """Block structure for Dinari blockchain"""
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    validator: str  # Address of the validator who created this block
    nonce: int = 0
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate unique hash for this block"""
        # Create hash of all transactions
        tx_hashes = [tx.calculate_hash() for tx in self.transactions]
        transactions_hash = hashlib.sha256(
            json.dumps(tx_hashes, sort_keys=True).encode('utf-8')
        ).hexdigest()
        
        # Combine all block data
        block_string = (f"{self.index}{self.timestamp}{transactions_hash}"
                       f"{self.previous_hash}{self.validator}{self.nonce}")
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()
    
    def is_valid(self, previous_block: Optional['Block'] = None) -> bool:
        """Validate block integrity"""
        # Check hash matches calculated hash
        if self.hash != self.calculate_hash():
            return False
        
        # Check previous hash if previous block provided
        if previous_block and self.previous_hash != previous_block.hash:
            return False
        
        # Validate all transactions
        for tx in self.transactions:
            if not tx.is_valid():
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary for serialization"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'validator': self.validator,
            'nonce': self.nonce,
            'hash': self.hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """Create block from dictionary"""
        transactions = [Transaction.from_dict(tx) for tx in data['transactions']]
        return cls(
            index=data['index'],
            timestamp=data['timestamp'],
            transactions=transactions,
            previous_hash=data['previous_hash'],
            validator=data['validator'],
            nonce=data['nonce'],
            hash=data['hash']
        )

class SmartContract:
    """Simple smart contract system for Dinari"""
    
    def __init__(self, address: str, code: str, owner: str):
        self.address = address
        self.code = code
        self.owner = owner
        self.state = {}  # Contract state storage
        self.created_at = time.time()
    
    def execute(self, function_name: str, args: List[Any], caller: str, blockchain) -> Dict[str, Any]:
        """Execute contract function"""
        try:
            # Create safe execution environment
            safe_globals = {
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'dict': dict,
                    'list': list,
                    'max': max,
                    'min': min,
                    'sum': sum,
                },
                'contract': self,
                'caller': caller,
                'blockchain': blockchain,
                'args': args,
            }
            
            # Execute contract code
            exec(self.code, safe_globals)
            
            # Call the requested function
            if function_name in safe_globals:
                result = safe_globals[function_name](*args)
                return {
                    'success': True,
                    'result': result,
                    'state': self.state,
                    'gas_used': 1000  # Simple gas calculation
                }
            else:
                return {'success': False, 'error': f'Function {function_name} not found'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary"""
        return {
            'address': self.address,
            'code': self.code,
            'owner': self.owner,
            'state': self.state,
            'created_at': self.created_at
        }

class DinariBlockchain:
    """Main DinariBlockchain implementation"""
    
    def __init__(self, genesis_config: Dict[str, Any] = None):
        # Blockchain data
        self.chain: List[Block] = []
        self.transaction_pool: List[Transaction] = []
        self.balances: Dict[str, Decimal] = {}
        self.contracts: Dict[str, SmartContract] = {}
        
        # Network configuration
        self.genesis_config = genesis_config or self._default_genesis_config()
        self.validators: List[str] = self.genesis_config.get('validators', [])
        self.block_time = self.genesis_config.get('block_time', 30)  # seconds
        
        # Initialize blockchain with genesis block
        self._create_genesis_block()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"DinariBlockchain initialized with {len(self.validators)} validators")
    
    def _default_genesis_config(self) -> Dict[str, Any]:
        """Default genesis configuration"""
        return {
            'token_name': 'Dinari',
            'token_symbol': 'DNMR',
            'total_supply': '100000000',
            'decimals': 18,
            'validators': ['genesis_validator'],
            'block_time': 30,
            'initial_allocation': {
                'treasury': '50000000',
                'development': '20000000', 
                'community': '20000000',
                'team': '10000000'
            }
        }
    
    def _create_genesis_block(self):
        """Create the genesis block with initial token distribution"""
        genesis_transactions = []
        
        # Create initial allocation transactions
        for address, amount in self.genesis_config['initial_allocation'].items():
            tx = Transaction(
                from_address='genesis',
                to_address=address,
                amount=amount,
                fee='0',
                data=f'Genesis allocation for {address}'
            )
            genesis_transactions.append(tx)
            
            # Set initial balance
            self.balances[address] = Decimal(amount)
        
        # Create genesis block
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=genesis_transactions,
            previous_hash='0' * 64,  # Genesis has no previous block
            validator='genesis'
        )
        
        self.chain.append(genesis_block)
        self.logger.info(f"Genesis block created with {len(genesis_transactions)} initial allocations")
    
    def get_latest_block(self) -> Block:
        """Get the most recent block"""
        return self.chain[-1]
    
    def get_balance(self, address: str) -> Decimal:
        """Get balance for an address"""
        return self.balances.get(address, Decimal('0'))
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add transaction to the transaction pool"""
        # Validate transaction
        if not transaction.is_valid():
            self.logger.warning(f"Invalid transaction rejected: {transaction.calculate_hash()[:8]}")
            return False
        
        # Check sender balance (except for genesis transactions)
        if transaction.from_address != 'genesis':
            sender_balance = self.get_balance(transaction.from_address)
            total_needed = Decimal(transaction.amount) + Decimal(transaction.fee)
            
            if sender_balance < total_needed:
                self.logger.warning(f"Insufficient balance for {transaction.from_address}")
                return False
        
        # Add to transaction pool
        self.transaction_pool.append(transaction)
        self.logger.info(f"Transaction added to pool: {transaction.calculate_hash()[:8]}")
        return True
    
    def mine_block(self, validator_address: str, max_transactions: int = 10) -> Optional[Block]:
        """Mine a new block using Proof of Authority"""
        # Check if validator is authorized
        if validator_address not in self.validators:
            self.logger.error(f"Unauthorized validator: {validator_address}")
            return None
        
        # Get transactions from pool
        transactions_to_include = self.transaction_pool[:max_transactions]
        if not transactions_to_include:
            self.logger.info("No transactions to include in block")
            return None
        
        # Create new block
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=transactions_to_include,
            previous_hash=self.get_latest_block().hash,
            validator=validator_address
        )
        
        # Validate block
        if not new_block.is_valid(self.get_latest_block()):
            self.logger.error("Failed to create valid block")
            return None
        
        # Add block to chain
        self.chain.append(new_block)
        
        # Remove processed transactions from pool
        self.transaction_pool = self.transaction_pool[len(transactions_to_include):]
        
        # Update balances
        self._process_block_transactions(transactions_to_include)
        
        self.logger.info(f"Block {new_block.index} mined by {validator_address} with {len(transactions_to_include)} transactions")
        return new_block
    
    def _process_block_transactions(self, transactions: List[Transaction]):
        """Process transactions and update balances"""
        for tx in transactions:
            # Handle smart contract calls
            if tx.data.startswith('contract:'):
                self._execute_contract_transaction(tx)
                continue
            
            # Regular transfer
            if tx.from_address != 'genesis':
                # Deduct from sender
                sender_balance = self.get_balance(tx.from_address)
                total_deduction = Decimal(tx.amount) + Decimal(tx.fee)
                self.balances[tx.from_address] = sender_balance - total_deduction
            
            # Add to recipient
            recipient_balance = self.get_balance(tx.to_address)
            self.balances[tx.to_address] = recipient_balance + Decimal(tx.amount)
    
    def deploy_contract(self, code: str, deployer: str) -> str:
        """Deploy a smart contract"""
        # Generate contract address
        contract_data = f"{code}{deployer}{time.time()}"
        contract_address = f"0x{hashlib.sha256(contract_data.encode()).hexdigest()[:40]}"
        
        # Create contract
        contract = SmartContract(contract_address, code, deployer)
        self.contracts[contract_address] = contract
        
        self.logger.info(f"Smart contract deployed at {contract_address}")
        return contract_address
    
    def call_contract(self, contract_address: str, function_name: str, 
                     args: List[Any], caller: str) -> Dict[str, Any]:
        """Call smart contract function"""
        if contract_address not in self.contracts:
            return {'success': False, 'error': 'Contract not found'}
        
        contract = self.contracts[contract_address]
        return contract.execute(function_name, args, caller, self)
    
    def _execute_contract_transaction(self, transaction: Transaction):
        """Execute smart contract transaction"""
        try:
            # Parse contract call: contract:address:function:arg1:arg2:...
            parts = transaction.data.split(':')
            if len(parts) < 3:
                return
            
            contract_address = parts[1]
            function_name = parts[2]
            args = parts[3:] if len(parts) > 3 else []
            
            # Execute contract
            result = self.call_contract(contract_address, function_name, args, transaction.from_address)
            self.logger.info(f"Contract call result: {result}")
            
        except Exception as e:
            self.logger.error(f"Contract execution error: {e}")
    
    def add_validator(self, validator_address: str, authorized_by: str):
        """Add new validator (must be authorized by existing validator)"""
        if authorized_by not in self.validators:
            self.logger.error(f"Unauthorized attempt to add validator by {authorized_by}")
            return False
        
        if validator_address not in self.validators:
            self.validators.append(validator_address)
            self.logger.info(f"Validator added: {validator_address}")
            return True
        return False
    
    def validate_chain(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if not current_block.is_valid(previous_block):
                self.logger.error(f"Invalid block at index {i}")
                return False
        
        return True
    
    def get_transaction_history(self, address: str) -> List[Transaction]:
        """Get transaction history for an address"""
        history = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.from_address == address or tx.to_address == address:
                    history.append(tx)
        return history
    
    def get_stats(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        total_transactions = sum(len(block.transactions) for block in self.chain)
        total_supply = sum(self.balances.values())
        
        return {
            'total_blocks': len(self.chain),
            'total_transactions': total_transactions,
            'pending_transactions': len(self.transaction_pool),
            'total_validators': len(self.validators),
            'total_contracts': len(self.contracts),
            'total_supply': str(total_supply),
            'chain_valid': self.validate_chain(),
            'latest_block_hash': self.get_latest_block().hash[:16]
        }
    
    def to_json(self) -> str:
        """Export blockchain to JSON"""
        data = {
            'genesis_config': self.genesis_config,
            'chain': [block.to_dict() for block in self.chain],
            'balances': {addr: str(balance) for addr, balance in self.balances.items()},
            'validators': self.validators,
            'contracts': {addr: contract.to_dict() for addr, contract in self.contracts.items()}
        }
        return json.dumps(data, indent=2)
    
    def save_to_file(self, filename: str):
        """Save blockchain to file"""
        with open(filename, 'w') as f:
            f.write(self.to_json())
        self.logger.info(f"Blockchain saved to {filename}")


# Example usage and testing
if __name__ == "__main__":
    # Create blockchain
    blockchain = DinariBlockchain()
    
    # Add some test transactions
    tx1 = Transaction("treasury", "alice", "1000", "0.1")
    tx2 = Transaction("treasury", "bob", "500", "0.1") 
    tx3 = Transaction("alice", "bob", "100", "0.1")
    
    blockchain.add_transaction(tx1)
    blockchain.add_transaction(tx2)
    blockchain.add_transaction(tx3)
    
    # Mine a block
    blockchain.add_validator("validator1")
    block = blockchain.mine_block("validator1")
    
    # Print results
    print("=== DinariBlockchain Test ===")
    print(f"Blockchain Stats: {json.dumps(blockchain.get_stats(), indent=2)}")
    print(f"\nBalances:")
    for address in ["treasury", "alice", "bob"]:
        print(f"  {address}: {blockchain.get_balance(address)} DNMR")
    
    print(f"\nLatest Block: {block.index} (Hash: {block.hash[:16]}...)")
    print(f"Transactions in block: {len(block.transactions)}")
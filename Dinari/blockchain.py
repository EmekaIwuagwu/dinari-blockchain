"""
DinariBlockchain with LevelDB Storage & Smart Contracts
File: dinari/blockchain.py
Native DINARI token blockchain with Afrocoin stablecoin support
"""

import hashlib
import json
import time
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext
import logging
from .database import DinariLevelDB

# Set precision for financial calculations
getcontext().prec = 28

@dataclass
class Transaction:
    """DinariBlockchain transaction (paid in DINARI gas)"""
    from_address: str
    to_address: str
    amount: Decimal  # Amount in DINARI
    gas_price: Decimal  # Gas price in DINARI
    gas_limit: int
    nonce: int
    data: str = ""
    signature: str = ""
    timestamp: int = 0
    tx_type: str = "transfer"  # transfer, contract_deploy, contract_call
    contract_address: str = ""
    
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
            "timestamp": self.timestamp,
            "tx_type": self.tx_type,
            "contract_address": self.contract_address
        }
    
    def get_hash(self) -> str:
        """Calculate transaction hash"""
        tx_string = f"{self.from_address}{self.to_address}{self.amount}{self.nonce}{self.timestamp}{self.data}"
        return hashlib.sha256(tx_string.encode()).hexdigest()

@dataclass
class Block:
    """DinariBlockchain block"""
    index: int
    transactions: List[Transaction]
    timestamp: int
    previous_hash: str
    nonce: int = 0
    validator: str = ""
    gas_used: int = 0
    gas_limit: int = 10000000
    
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
            "gas_used": self.gas_used,
            "gas_limit": self.gas_limit,
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

@dataclass
class ContractState:
    """Smart contract state"""
    variables: Dict[str, Any]
    balance: Decimal  # Contract's DINARI balance
    owner: str
    created_at: int
    last_executed: int
    is_active: bool = True

class SmartContract:
    """
    Smart Contract implementation for DinariBlockchain
    Contracts are deployed and executed using DINARI gas
    """
    
    def __init__(self, 
                 contract_id: str,
                 code: str,
                 owner: str,
                 contract_type: str = "general",
                 initial_state: Optional[Dict[str, Any]] = None):
        self.contract_id = contract_id
        self.code = code
        self.owner = owner
        self.contract_type = contract_type
        self.created_at = int(time.time())
        
        # Initialize contract state
        default_state = initial_state or {}
        
        # Special initialization for Afrocoin stablecoin contract
        if contract_type == "afrocoin_stablecoin":
            default_state.update({
                "name": "Afrocoin",
                "symbol": "AFC",
                "decimals": 18,
                "total_supply": "0",
                "balances": {},  # AFC token balances
                "allowances": {},
                "collateral_ratio": "150",  # 150% minimum collateralization
                "price_oracle": "1.00",  # 1 AFC = 1 USD target
                "stability_fee": "0.5",  # 0.5% annual stability fee
                "liquidation_threshold": "120",  # 120% liquidation threshold
                "collateral_assets": {
                    "DINARI": {  # Native DINARI token as primary collateral
                        "active": True,
                        "price": "0.10",  # 1 DINARI = $0.10 (example)
                        "ratio": "150",  # 150% collateral ratio
                        "deposited": "0"
                    },
                    "BTC": {
                        "active": True,
                        "price": "50000.00",
                        "ratio": "200",  # Higher ratio for volatile assets
                        "deposited": "0"
                    },
                    "ETH": {
                        "active": True,
                        "price": "3000.00",
                        "ratio": "180",
                        "deposited": "0"
                    }
                },
                "user_collateral": {},  # Track user collateral positions
                "cdp_counter": 0,  # Collateralized Debt Position counter
                "liquidation_penalty": "13",  # 13% liquidation penalty
                "oracle_addresses": {},
                "backed_by": "DINARI",  # Primary backing asset
                "governance_enabled": True,
                "minting_paused": False
            })
        
        self.state = ContractState(
            variables=default_state,
            balance=Decimal("0"),  # Contract's DINARI balance
            owner=owner,
            created_at=self.created_at,
            last_executed=0
        )
        
        # Execution history
        self.execution_history: List[Dict[str, Any]] = []
        
    def execute(self, function_name: str, args: Dict[str, Any], caller: str, value: Decimal = Decimal("0")) -> Dict[str, Any]:
        """Execute a function in the smart contract"""
        try:
            # Security checks
            if function_name.startswith('_'):
                raise ValueError("Cannot call private functions")
            
            if not self.state.is_active:
                raise ValueError("Contract is not active")
            
            # Update execution timestamp
            self.state.last_executed = int(time.time())
            
            # Route to appropriate function based on contract type
            if self.contract_type == "afrocoin_stablecoin":
                result = self._execute_afrocoin_function(function_name, args, caller, value)
            else:
                result = self._execute_general_function(function_name, args, caller, value)
            
            # Calculate gas usage (simplified)
            gas_used = self._calculate_gas_usage(function_name, args)
            
            # Log execution
            execution_log = {
                'timestamp': self.state.last_executed,
                'function': function_name,
                'caller': caller,
                'args': args,
                'result': result,
                'gas_used': gas_used,
                'success': True
            }
            self.execution_history.append(execution_log)
            
            return {
                'success': True,
                'result': result,
                'gas_used': gas_used,
                'timestamp': self.state.last_executed
            }
            
        except Exception as e:
            error_log = {
                'timestamp': int(time.time()),
                'function': function_name,
                'caller': caller,
                'args': args,
                'error': str(e),
                'success': False
            }
            self.execution_history.append(error_log)
            
            return {
                'success': False,
                'error': str(e),
                'gas_used': 21000,  # Base gas for failed transaction
                'timestamp': int(time.time())
            }
    
    def _execute_afrocoin_function(self, function_name: str, args: Dict[str, Any], caller: str, value: Decimal) -> Any:
        """Execute Afrocoin stablecoin functions on DinariBlockchain"""
        
        if function_name == "mint_afc":
            return self._afrocoin_mint(args, caller, value)
        elif function_name == "burn_afc":
            return self._afrocoin_burn(args, caller)
        elif function_name == "transfer_afc":
            return self._afrocoin_transfer(args, caller)
        elif function_name == "approve_afc":
            return self._afrocoin_approve(args, caller)
        elif function_name == "transfer_from_afc":
            return self._afrocoin_transfer_from(args, caller)
        elif function_name == "deposit_dinari_collateral":
            return self._deposit_dinari_collateral(args, caller, value)
        elif function_name == "withdraw_dinari_collateral":
            return self._withdraw_dinari_collateral(args, caller)
        elif function_name == "liquidate_position":
            return self._liquidate_position(args, caller)
        elif function_name == "update_oracle_price":
            return self._update_oracle_price(args, caller)
        elif function_name == "afc_balance_of":
            return self._afc_balance_of(args)
        elif function_name == "afc_total_supply":
            return self.state.variables["total_supply"]
        elif function_name == "get_collateral_ratio":
            return self._get_collateral_ratio(args)
        elif function_name == "get_dinari_price":
            return self.state.variables["collateral_assets"]["DINARI"]["price"]
        else:
            raise ValueError(f"Unknown Afrocoin function: {function_name}")
    
    def _deposit_dinari_collateral(self, args: Dict[str, Any], caller: str, dinari_amount: Decimal) -> str:
        """Deposit DINARI tokens as collateral to mint AFC"""
        if dinari_amount <= 0:
            raise ValueError("Must deposit positive amount of DINARI")
        
        if self.state.variables.get("minting_paused", False):
            raise ValueError("Minting is currently paused")
        
        # Calculate how much AFC can be minted
        dinari_price = Decimal(self.state.variables["collateral_assets"]["DINARI"]["price"])
        collateral_ratio = Decimal(self.state.variables["collateral_assets"]["DINARI"]["ratio"]) / 100
        
        collateral_value_usd = dinari_amount * dinari_price
        max_afc_mint = collateral_value_usd / collateral_ratio
        
        # Update user collateral tracking
        user_collateral = self.state.variables.get('user_collateral', {})
        if caller not in user_collateral:
            user_collateral[caller] = {"DINARI": "0", "afc_debt": "0"}
        
        current_dinari = Decimal(user_collateral[caller]["DINARI"])
        user_collateral[caller]["DINARI"] = str(current_dinari + dinari_amount)
        
        # Update total deposited DINARI
        total_deposited = Decimal(self.state.variables["collateral_assets"]["DINARI"]["deposited"])
        self.state.variables["collateral_assets"]["DINARI"]["deposited"] = str(total_deposited + dinari_amount)
        
        # Update contract's DINARI balance
        self.state.balance += dinari_amount
        
        self.state.variables['user_collateral'] = user_collateral
        
        return f"Deposited {dinari_amount} DINARI as collateral. Can mint up to {max_afc_mint} AFC"
    
    def _afrocoin_mint(self, args: Dict[str, Any], caller: str, value: Decimal) -> str:
        """Mint AFC tokens against DINARI collateral"""
        afc_amount = Decimal(str(args.get('amount', '0')))
        
        if afc_amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Check if user has enough collateral
        user_collateral = self.state.variables.get('user_collateral', {})
        if caller not in user_collateral:
            raise ValueError("No collateral deposited")
        
        dinari_collateral = Decimal(user_collateral[caller]["DINARI"])
        current_afc_debt = Decimal(user_collateral[caller]["afc_debt"])
        
        # Calculate collateral requirements
        dinari_price = Decimal(self.state.variables["collateral_assets"]["DINARI"]["price"])
        collateral_ratio = Decimal(self.state.variables["collateral_assets"]["DINARI"]["ratio"]) / 100
        
        collateral_value = dinari_collateral * dinari_price
        new_total_debt = current_afc_debt + afc_amount
        required_collateral = new_total_debt * collateral_ratio
        
        if collateral_value < required_collateral:
            raise ValueError(f"Insufficient collateral. Required: ${required_collateral}, Available: ${collateral_value}")
        
        # Update AFC balances
        afc_balances = self.state.variables.get('balances', {})
        current_afc_balance = Decimal(afc_balances.get(caller, '0'))
        afc_balances[caller] = str(current_afc_balance + afc_amount)
        
        # Update user debt
        user_collateral[caller]["afc_debt"] = str(new_total_debt)
        
        # Update total supply
        current_supply = Decimal(self.state.variables.get('total_supply', '0'))
        self.state.variables['total_supply'] = str(current_supply + afc_amount)
        self.state.variables['balances'] = afc_balances
        self.state.variables['user_collateral'] = user_collateral
        
        return f"Minted {afc_amount} AFC against {dinari_collateral} DINARI collateral"
    
    def _afrocoin_burn(self, args: Dict[str, Any], caller: str) -> str:
        """Burn AFC tokens to reduce debt"""
        afc_amount = Decimal(str(args.get('amount', '0')))
        
        afc_balances = self.state.variables.get('balances', {})
        current_afc_balance = Decimal(afc_balances.get(caller, '0'))
        
        if current_afc_balance < afc_amount:
            raise ValueError("Insufficient AFC balance to burn")
        
        # Update AFC balance
        afc_balances[caller] = str(current_afc_balance - afc_amount)
        
        # Reduce debt
        user_collateral = self.state.variables.get('user_collateral', {})
        if caller in user_collateral:
            current_debt = Decimal(user_collateral[caller]["afc_debt"])
            user_collateral[caller]["afc_debt"] = str(max(Decimal("0"), current_debt - afc_amount))
        
        # Update total supply
        current_supply = Decimal(self.state.variables.get('total_supply', '0'))
        self.state.variables['total_supply'] = str(current_supply - afc_amount)
        self.state.variables['balances'] = afc_balances
        self.state.variables['user_collateral'] = user_collateral
        
        return f"Burned {afc_amount} AFC tokens"
    
    def _afrocoin_transfer(self, args: Dict[str, Any], caller: str) -> str:
        """Transfer AFC tokens"""
        to_address = args.get('to')
        amount = Decimal(str(args.get('amount', '0')))
        
        if not to_address:
            raise ValueError("Recipient address required")
        
        afc_balances = self.state.variables.get('balances', {})
        from_balance = Decimal(afc_balances.get(caller, '0'))
        
        if from_balance < amount:
            raise ValueError("Insufficient AFC balance")
        
        # Update balances
        afc_balances[caller] = str(from_balance - amount)
        to_balance = Decimal(afc_balances.get(to_address, '0'))
        afc_balances[to_address] = str(to_balance + amount)
        self.state.variables['balances'] = afc_balances
        
        return f"Transferred {amount} AFC from {caller} to {to_address}"
    
    def _afc_balance_of(self, args: Dict[str, Any]) -> str:
        """Get AFC balance of an address"""
        address = args.get('address')
        if not address:
            raise ValueError("Address required")
        
        afc_balances = self.state.variables.get('balances', {})
        return afc_balances.get(address, '0')
    
    def _get_collateral_ratio(self, args: Dict[str, Any]) -> str:
        """Get collateral ratio for a user"""
        user = args.get('user')
        if not user:
            raise ValueError("User address required")
        
        user_collateral = self.state.variables.get('user_collateral', {})
        if user not in user_collateral:
            return "0"
        
        dinari_amount = Decimal(user_collateral[user]["DINARI"])
        afc_debt = Decimal(user_collateral[user]["afc_debt"])
        
        if afc_debt == 0:
            return "infinite"
        
        dinari_price = Decimal(self.state.variables["collateral_assets"]["DINARI"]["price"])
        collateral_value = dinari_amount * dinari_price
        ratio = (collateral_value / afc_debt) * 100
        
        return str(ratio)
    
    def _execute_general_function(self, function_name: str, args: Dict[str, Any], caller: str, value: Decimal) -> Any:
        """Execute general smart contract functions"""
        
        if function_name == "get_owner":
            return self.state.owner
        elif function_name == "get_dinari_balance":
            return str(self.state.balance)
        elif function_name == "get_state":
            return self.state.variables
        elif function_name == "set_variable":
            if caller != self.state.owner:
                raise ValueError("Only owner can set variables")
            key = args.get('key')
            value_arg = args.get('value')
            self.state.variables[key] = value_arg
            return f"Variable {key} set to {value_arg}"
        elif function_name == "transfer_ownership":
            if caller != self.state.owner:
                raise ValueError("Only owner can transfer ownership")
            new_owner = args.get('new_owner')
            if not new_owner:
                raise ValueError("New owner address required")
            self.state.owner = new_owner
            return f"Ownership transferred to {new_owner}"
        else:
            raise ValueError(f"Unknown function: {function_name}")
    
    def _calculate_gas_usage(self, function_name: str, args: Dict[str, Any]) -> int:
        """Calculate gas usage for function execution (simplified)"""
        base_gas = 21000
        
        if function_name in ['transfer_afc', 'approve_afc']:
            return base_gas + 5000
        elif function_name in ['mint_afc', 'burn_afc']:
            return base_gas + 10000
        elif function_name in ['deposit_dinari_collateral', 'withdraw_dinari_collateral']:
            return base_gas + 15000
        elif function_name == 'liquidate_position':
            return base_gas + 20000
        else:
            return base_gas + len(str(args)) * 10
    
    def get_afc_balance(self, address: str) -> Decimal:
        """Get AFC token balance for an address"""
        if self.contract_type == "afrocoin_stablecoin":
            afc_balances = self.state.variables.get('balances', {})
            return Decimal(afc_balances.get(address, '0'))
        return Decimal('0')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary for storage"""
        return {
            'contract_id': self.contract_id,
            'code': self.code,
            'owner': self.owner,
            'contract_type': self.contract_type,
            'created_at': self.created_at,
            'state': {
                'variables': self.state.variables,
                'balance': str(self.state.balance),
                'owner': self.state.owner,
                'created_at': self.state.created_at,
                'last_executed': self.state.last_executed,
                'is_active': self.state.is_active
            },
            'execution_history': self.execution_history[-20:]  # Keep last 20 executions
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SmartContract':
        """Create contract from dictionary"""
        contract = cls(
            contract_id=data['contract_id'],
            code=data['code'],
            owner=data['owner'],
            contract_type=data.get('contract_type', 'general')
        )
        
        # Restore state
        state_data = data['state']
        contract.state = ContractState(
            variables=state_data['variables'],
            balance=Decimal(state_data['balance']),
            owner=state_data['owner'],
            created_at=state_data['created_at'],
            last_executed=state_data['last_executed'],
            is_active=state_data.get('is_active', True)
        )
        
        # Restore execution history
        contract.execution_history = data.get('execution_history', [])
        
        return contract

class DinariBlockchain:
    """
    DinariBlockchain - Native DINARI token blockchain
    Supports smart contracts including Afrocoin stablecoin
    """
    
    def __init__(self, db_path: str = "./dinari_data"):
        self.logger = logging.getLogger("Dinari.blockchain")
        
        # Initialize LevelDB
        self.db = DinariLevelDB(db_path)
        
        # Load or create blockchain state
        self.chain_state = self._load_chain_state()
        self.pending_transactions = []
        self.validators = self._load_validators()
        self.dinari_balances = self._load_balances()  # Native DINARI balances
        self.contracts = self._load_contracts()
        
        # Initialize genesis block if needed
        if self.chain_state["height"] == 0:
            self._create_genesis_block()
            
        self.logger.info(f"DinariBlockchain initialized with {len(self.validators)} validators")
    
    def _load_chain_state(self) -> dict:
        """Load blockchain state from LevelDB"""
        default_state = {
            "height": 0,
            "last_block_hash": "",
            "total_dinari_supply": "0",
            "total_transactions": 0,
            "contract_count": 0
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
        """Load DINARI token balances"""
        return self.db.get("dinari_balances") or {}
    
    def _save_balances(self):
        """Save DINARI token balances"""
        self.db.put("dinari_balances", self.dinari_balances)
    
    def _load_contracts(self) -> Dict[str, SmartContract]:
        """Load smart contracts"""
        contracts_data = self.db.get("contracts") or {}
        contracts = {}
        
        for contract_id, contract_data in contracts_data.items():
            try:
                contracts[contract_id] = SmartContract.from_dict(contract_data)
            except Exception as e:
                self.logger.error(f"Failed to load contract {contract_id}: {e}")
        
        return contracts
    
    def _save_contracts(self):
        """Save smart contracts"""
        contracts_data = {}
        for contract_id, contract in self.contracts.items():
            contracts_data[contract_id] = contract.to_dict()
        self.db.put("contracts", contracts_data)
    
    def _create_genesis_block(self):
        """Create genesis block with initial DINARI allocations and deploy Afrocoin contract"""
        genesis_transactions = [
            Transaction(
                from_address="genesis",
                to_address="dinari1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
                amount=Decimal("1000000"),  # 1M DINARI
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=0,
                data="Genesis DINARI allocation"
            ),
            Transaction(
                from_address="genesis", 
                to_address="dinari1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx",
                amount=Decimal("500000"),  # 500K DINARI
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=1,
                data="Initial validator DINARI allocation"
            ),
            Transaction(
                from_address="genesis",
                to_address="dinari1cqgze3fqpw0dqh9j8l2dqqyr89c0q5c2jdpg8x",
                amount=Decimal("250000"),  # 250K DINARI
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=2,
                data="Development fund DINARI"
            ),
            Transaction(
                from_address="genesis",
                to_address="dinari1xz2f8l8lh8vqw3r6n4s2k7j9p1d5g8h3m6c4v7",
                amount=Decimal("100000"),  # 100K DINARI
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=3,
                data="Community treasury DINARI"
            ),
            Transaction(
                from_address="genesis",
                to_address="dinari1a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5",
                amount=Decimal("50000"),  # 50K DINARI
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=4,
                data="Reserve fund DINARI"
            )
        ]
        
        genesis_block = Block(
            index=0,
            transactions=genesis_transactions,
            timestamp=int(time.time()),
            previous_hash="0" * 64,
            validator="genesis"
        )
        
        # Process genesis transactions (distribute DINARI)
        for tx in genesis_transactions:
            if tx.to_address not in self.dinari_balances:
                self.dinari_balances[tx.to_address] = "0"
            current_balance = Decimal(self.dinari_balances[tx.to_address])
            self.dinari_balances[tx.to_address] = str(current_balance + tx.amount)
        
        # Deploy Afrocoin stablecoin contract
        afrocoin_contract = SmartContract(
            contract_id="afrocoin_stablecoin",
            code="Afrocoin USD Stablecoin Contract",
            owner="genesis",
            contract_type="afrocoin_stablecoin"
        )
        self.contracts["afrocoin_stablecoin"] = afrocoin_contract
        
        # Store genesis block
        block_hash = genesis_block.get_hash()
        self.db.store_block(block_hash, genesis_block.to_dict())
        
        # Update chain state
        self.chain_state["height"] = 1
        self.chain_state["last_block_hash"] = block_hash
        self.chain_state["total_dinari_supply"] = str(sum(Decimal(balance) for balance in self.dinari_balances.values()))
        self.chain_state["total_transactions"] = len(genesis_transactions)
        self.chain_state["contract_count"] = len(self.contracts)
        
        # Save state
        self._save_chain_state()
        self._save_balances()
        self._save_contracts()
        
        self.logger.info(f"Genesis block created with {len(genesis_transactions)} initial DINARI allocations")
        self.logger.info("Afrocoin stablecoin contract deployed at genesis")
    
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
            # Check DINARI balance (skip for genesis and contract calls)
            if tx.from_address != "genesis" and tx.tx_type != "contract_call":
                sender_balance = Decimal(self.dinari_balances.get(tx.from_address, "0"))
                total_cost = tx.amount + (tx.gas_price * tx.gas_limit)
                if sender_balance < total_cost:
                    self.logger.warning(f"Insufficient DINARI balance: {tx.from_address}")
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
            total_gas_used = self._process_transactions(new_block.transactions)
            new_block.gas_used = total_gas_used
            
            # Store block
            block_hash = new_block.get_hash()
            self.db.store_block(block_hash, new_block.to_dict())
            
            # Update chain state
            self.chain_state["height"] += 1
            self.chain_state["last_block_hash"] = block_hash
            self.chain_state["total_transactions"] += len(new_block.transactions)
            self.chain_state["total_dinari_supply"] = str(sum(Decimal(balance) for balance in self.dinari_balances.values()))
            
            # Clear pending transactions
            self.pending_transactions = []
            
            # Save state
            self._save_chain_state()
            self._save_balances()
            self._save_contracts()
            
            self.logger.info(f"Block {new_block.index} created with {len(new_block.transactions)} transactions")
            return new_block
            
        except Exception as e:
            self.logger.error(f"Failed to create block: {e}")
            return None
    
    def _process_transactions(self, transactions: List[Transaction]) -> int:
        """Process transactions and update DINARI balances"""
        total_gas_used = 0
        
        for tx in transactions:
            try:
                if tx.tx_type == "contract_call":
                    # Execute contract function
                    result = self.execute_contract(
                        tx.contract_address,
                        json.loads(tx.data),
                        tx.from_address,
                        tx.amount
                    )
                    total_gas_used += result.get('gas_used', 21000)
                    
                elif tx.tx_type == "contract_deploy":
                    # Deploy new contract
                    contract_data = json.loads(tx.data)
                    self.deploy_contract(
                        contract_data['contract_id'],
                        contract_data['code'],
                        tx.from_address,
                        contract_data.get('contract_type', 'general'),
                        contract_data.get('initial_state', {})
                    )
                    total_gas_used += 50000  # Contract deployment gas
                    
                else:
                    # Regular DINARI transfer
                    if tx.from_address != "genesis":
                        # Debit sender
                        sender_balance = Decimal(self.dinari_balances.get(tx.from_address, "0"))
                        gas_fee = tx.gas_price * tx.gas_limit
                        self.dinari_balances[tx.from_address] = str(sender_balance - tx.amount - gas_fee)
                    
                    # Credit recipient
                    if tx.to_address not in self.dinari_balances:
                        self.dinari_balances[tx.to_address] = "0"
                    recipient_balance = Decimal(self.dinari_balances[tx.to_address])
                    self.dinari_balances[tx.to_address] = str(recipient_balance + tx.amount)
                    
                    total_gas_used += tx.gas_limit
                    
            except Exception as e:
                self.logger.error(f"Failed to process transaction {tx.get_hash()}: {e}")
                total_gas_used += 21000  # Base gas for failed transaction
        
        return total_gas_used
    
    def deploy_contract(self, contract_id: str, code: str, owner: str, contract_type: str = "general", initial_state: Dict[str, Any] = None) -> SmartContract:
        """Deploy a new smart contract"""
        if contract_id in self.contracts:
            raise ValueError(f"Contract {contract_id} already exists")
        
        contract = SmartContract(
            contract_id=contract_id,
            code=code,
            owner=owner,
            contract_type=contract_type,
            initial_state=initial_state
        )
        
        self.contracts[contract_id] = contract
        self.chain_state["contract_count"] = len(self.contracts)
        
        self.logger.info(f"Contract {contract_id} ({contract_type}) deployed by {owner}")
        return contract
    
    def execute_contract(self, contract_id: str, function_data: Dict[str, Any], caller: str, value: Decimal = Decimal("0")) -> Dict[str, Any]:
        """Execute a smart contract function"""
        if contract_id not in self.contracts:
            raise ValueError(f"Contract {contract_id} not found")
        
        contract = self.contracts[contract_id]
        function_name = function_data.get('function')
        args = function_data.get('args', {})
        
        result = contract.execute(function_name, args, caller, value)
        
        self.logger.info(f"Contract {contract_id} function {function_name} executed by {caller}")
        return result
    
    def get_contract(self, contract_id: str) -> Optional[SmartContract]:
        """Get smart contract by ID"""
        return self.contracts.get(contract_id)
    
    def get_afrocoin_contract(self) -> Optional[SmartContract]:
        """Get the Afrocoin stablecoin contract"""
        return self.contracts.get("afrocoin_stablecoin")
    
    def get_block_by_hash(self, block_hash: str) -> Optional[dict]:
        """Get block by hash"""
        return self.db.get_block(block_hash)
    
    def get_transaction_by_hash(self, tx_hash: str) -> Optional[dict]:
        """Get transaction by hash"""
        return self.db.get_transaction(tx_hash)
    
    def get_dinari_balance(self, address: str) -> Decimal:
        """Get DINARI token balance"""
        return Decimal(self.dinari_balances.get(address, "0"))
    
    def get_afrocoin_balance(self, address: str) -> Decimal:
        """Get Afrocoin (AFC) balance for an address"""
        afrocoin_contract = self.contracts.get("afrocoin_stablecoin")
        if afrocoin_contract:
            return afrocoin_contract.get_afc_balance(address)
        return Decimal("0")
    
    def get_chain_info(self) -> dict:
        """Get blockchain information"""
        return {
            "height": self.chain_state["height"],
            "last_block_hash": self.chain_state["last_block_hash"],
            "total_dinari_supply": self.chain_state["total_dinari_supply"],
            "total_transactions": self.chain_state["total_transactions"],
            "pending_transactions": len(self.pending_transactions),
            "validators": len(self.validators),
            "contracts": len(self.contracts),
            "contract_count": self.chain_state.get("contract_count", 0),
            "native_token": "DINARI",
            "stablecoin": "AFC (Afrocoin)"
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
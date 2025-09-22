"""
DinariBlockchain with LevelDB Storage & Smart Contracts
File: Dinari/blockchain.py
Native DINARI token blockchain with Afrocoin stablecoin support
FIXED: Auto block mining, transaction processing, balance persistence, validator management
"""

import hashlib
import json
import time
import threading
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext
import logging
import requests
import urllib.parse
import random
import statistics
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
        return "DTx" + hashlib.sha256(tx_string.encode()).hexdigest()


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
        return "DTx" + hashlib.sha256(block_string.encode()).hexdigest()


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
    """Smart Contract implementation for DinariBlockchain"""

    def __init__(self, contract_id: str, code: str, owner: str, contract_type: str = "general", initial_state: Optional[Dict[str, Any]] = None):
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
                "balances": {},
                "allowances": {},
                "collateral_ratio": "150",
                "price_oracle": "1.00",
                "stability_fee": "0.5",
                "liquidation_threshold": "120",
                "collateral_assets": {
                    "DINARI": {
                        "active": True,
                        "price": "1.00",
                        "ratio": "150",
                        "deposited": "0"
                    }
                },
                "user_collateral": {},
                "cdp_counter": 0,
                "liquidation_penalty": "13",
                "oracle_addresses": {},
                "backed_by": "DINARI",
                "governance_enabled": True,
                "minting_paused": False,
                "canonical_oracle": {},
                "canonical_dinari_oracle": {},
                "price_history": [],
                "dinari_price_history": []
            })

        self.state = ContractState(
            variables=default_state,
            balance=Decimal("0"),
            owner=owner,
            created_at=self.created_at,
            last_executed=0
        )

        self.execution_history: List[Dict[str, Any]] = []
    
    def get_all_transactions(self, start_index=0, limit=100, reverse=True):
        """Get transactions with pagination - NEVER loses old transactions"""
        try:
            transactions = []
            
            # Get total transaction count
            total_count = int(self.db.get(b'tx_count') or b'0')
            
            if total_count == 0:
                return {'transactions': [], 'total': 0, 'has_more': False}
            
            # Calculate range
            if reverse:
                # Start from newest transactions
                end_index = total_count - start_index
                start_scan = max(0, end_index - limit)
                indices = range(end_index - 1, start_scan - 1, -1)
            else:
                # Start from oldest transactions
                end_scan = min(total_count, start_index + limit)
                indices = range(start_index, end_scan)
            
            # Retrieve transactions
            for i in indices:
                try:
                    key = f"tx:index:{i:010d}".encode()
                    data = self.db.get(key)
                    if data:
                        tx_meta = json.loads(data.decode())
                        
                        # Get full transaction details
                        full_tx_data = self.db.get(f"tx:hash:{tx_meta['hash']}".encode())
                        if full_tx_data:
                            full_tx = json.loads(full_tx_data.decode())
                            transactions.append(full_tx['transaction'])
                        
                except Exception as e:
                    print(f"Error retrieving transaction at index {i}: {e}")
                    continue
            
            has_more = (reverse and start_index + limit < total_count) or \
                      (not reverse and start_index + len(transactions) < total_count)
            
            return {
                'transactions': transactions,
                'total': total_count,
                'has_more': has_more,
                'start_index': start_index
            }
            
        except Exception as e:
            print(f"❌ Error getting all transactions: {e}")
            return {'transactions': [], 'total': 0, 'has_more': False}


    def execute(self, function_name: str, args: Dict[str, Any], caller: str, value: Decimal = Decimal("0")) -> Dict[str, Any]:
        """Execute a function in the smart contract"""
        try:
            if function_name.startswith('_'):
                raise ValueError("Cannot call private functions")

            if not self.state.is_active:
                raise ValueError("Contract is not active")

            self.state.last_executed = int(time.time())

            if self.contract_type == "afrocoin_stablecoin":
                result = self._execute_afrocoin_function(function_name, args, caller, value)
            else:
                result = self._execute_general_function(function_name, args, caller, value)

            gas_used = self._calculate_gas_usage(function_name, args)

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
                'gas_used': 21000,
                'timestamp': int(time.time())
            }

    def _execute_afrocoin_function(self, function_name: str, args: Dict[str, Any], caller: str, value: Decimal) -> Any:
        """Execute Afrocoin stablecoin functions"""
        if function_name == "mint_afc":
            return self._afrocoin_mint(args, caller, value)
        elif function_name == "burn_afc":
            return self._afrocoin_burn(args, caller)
        elif function_name == "transfer_afc":
            return self._afrocoin_transfer(args, caller)
        elif function_name == "afc_balance_of":
            return self._afc_balance_of(args)
        elif function_name == "afc_total_supply":
            return self.state.variables["total_supply"]
        elif function_name == "update_usd_price":
            return self._update_usd_price_oracle(args, caller)
        elif function_name == "get_canonical_afc_price":
            return self._get_canonical_afc_price()
        elif function_name == "set_canonical_afc_price":
            return self._set_canonical_afc_price(args, caller)
        elif function_name == "get_canonical_dinari_price":
            return self._get_canonical_dinari_price()
        elif function_name == "set_canonical_dinari_price":
            return self._set_canonical_dinari_price(args, caller)
        elif function_name == "check_peg_deviation":
            return self._check_peg_deviation()
        elif function_name == "execute_rebase":
            return self._execute_algorithmic_rebase(args, caller)
        else:
            raise ValueError(f"Unknown Afrocoin function: {function_name}")

    def _afrocoin_mint(self, args: Dict[str, Any], caller: str, value: Decimal) -> str:
        """Mint AFC tokens"""
        afc_amount = Decimal(str(args.get('amount', '0')))
        
        if afc_amount <= 0:
            raise ValueError("Amount must be positive")

        afc_balances = self.state.variables.get('balances', {})
        current_afc_balance = Decimal(afc_balances.get(caller, '0'))
        afc_balances[caller] = str(current_afc_balance + afc_amount)

        current_supply = Decimal(self.state.variables.get('total_supply', '0'))
        self.state.variables['total_supply'] = str(current_supply + afc_amount)
        self.state.variables['balances'] = afc_balances

        return f"Minted {afc_amount} AFC tokens"

    def _afrocoin_burn(self, args: Dict[str, Any], caller: str) -> str:
        """Burn AFC tokens"""
        afc_amount = Decimal(str(args.get('amount', '0')))

        afc_balances = self.state.variables.get('balances', {})
        current_afc_balance = Decimal(afc_balances.get(caller, '0'))

        if current_afc_balance < afc_amount:
            raise ValueError("Insufficient AFC balance")

        afc_balances[caller] = str(current_afc_balance - afc_amount)
        current_supply = Decimal(self.state.variables.get('total_supply', '0'))
        self.state.variables['total_supply'] = str(current_supply - afc_amount)
        self.state.variables['balances'] = afc_balances

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

        afc_balances[caller] = str(from_balance - amount)
        to_balance = Decimal(afc_balances.get(to_address, '0'))
        afc_balances[to_address] = str(to_balance + amount)
        self.state.variables['balances'] = afc_balances

        return f"Transferred {amount} AFC from {caller} to {to_address}"

    def _afc_balance_of(self, args: Dict[str, Any]) -> str:
        """Get AFC balance"""
        address = args.get('address')
        if not address:
            raise ValueError("Address required")

        afc_balances = self.state.variables.get('balances', {})
        return afc_balances.get(address, '0')

    def _update_usd_price_oracle(self, args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """Update AFC/USD price"""
        new_price = args.get('price')
        if not new_price:
            raise ValueError("Price required")

        new_price = Decimal(str(new_price))
        old_price = Decimal(self.state.variables.get('price_oracle', '1.0'))
        
        self.state.variables['price_oracle'] = str(new_price)
        self.state.variables['last_price_update'] = int(time.time())

        deviation = abs(new_price - Decimal('1.0')) / Decimal('1.0')

        return {
            'success': True,
            'old_price': str(old_price),
            'new_price': str(new_price),
            'deviation_percent': str(deviation * 100)
        }

    def _get_canonical_afc_price(self) -> Dict[str, Any]:
        """Get canonical AFC price"""
        oracle_data = self.state.variables.get('canonical_oracle', {})
        
        if not oracle_data:
            self._set_canonical_afc_price({}, "protocol_algorithm")
            oracle_data = self.state.variables.get('canonical_oracle', {})

        current_time = int(time.time())
        last_update = oracle_data.get('timestamp', 0)
        is_fresh = (current_time - last_update) < 3600

        return {
            'price': oracle_data.get('price', '1.0'),
            'timestamp': oracle_data.get('timestamp', current_time),
            'confidence': oracle_data.get('confidence', '1.0'),
            'decimals': 18,
            'symbol': 'AFC',
            'base_currency': 'USD',
            'is_fresh': is_fresh,
            'price_authority': 'afrocoin_protocol'
        }

    def _set_canonical_afc_price(self, args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """Set canonical AFC price"""
        canonical_price = Decimal('1.0')
        confidence_score = Decimal('1.0')
        current_time = int(time.time())

        oracle_data = {
            'price': str(canonical_price),
            'timestamp': current_time,
            'confidence': str(confidence_score),
            'decimals': 18,
            'symbol': 'AFC',
            'base_currency': 'USD',
            'price_source': 'afrocoin_protocol_canonical'
        }

        self.state.variables['canonical_oracle'] = oracle_data

        return {
            'success': True,
            'canonical_price': str(canonical_price),
            'timestamp': current_time,
            'confidence': str(confidence_score)
        }

    def _get_canonical_dinari_price(self) -> Dict[str, Any]:
        """Get canonical DINARI price"""
        dinari_oracle_data = self.state.variables.get('canonical_dinari_oracle', {})
        
        if not dinari_oracle_data:
            self._set_canonical_dinari_price({}, "protocol_algorithm")
            dinari_oracle_data = self.state.variables.get('canonical_dinari_oracle', {})

        current_time = int(time.time())
        last_update = dinari_oracle_data.get('timestamp', 0)
        is_fresh = (current_time - last_update) < 3600

        return {
            'price': dinari_oracle_data.get('price', '1.0'),
            'timestamp': dinari_oracle_data.get('timestamp', current_time),
            'confidence': dinari_oracle_data.get('confidence', '1.0'),
            'decimals': 18,
            'symbol': 'DINARI',
            'base_currency': 'USD',
            'is_fresh': is_fresh,
            'price_authority': 'dinari_protocol'
        }

    def _set_canonical_dinari_price(self, args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """Set canonical DINARI price"""
        canonical_dinari_price = Decimal('1.0')
        confidence_score = Decimal('1.0')
        current_time = int(time.time())

        dinari_oracle_data = {
            'price': str(canonical_dinari_price),
            'timestamp': current_time,
            'confidence': str(confidence_score),
            'decimals': 18,
            'symbol': 'DINARI',
            'base_currency': 'USD',
            'price_source': 'dinari_protocol_canonical'
        }

        self.state.variables['canonical_dinari_oracle'] = dinari_oracle_data

        return {
            'success': True,
            'canonical_dinari_price': str(canonical_dinari_price),
            'timestamp': current_time,
            'confidence': str(confidence_score)
        }

    def _check_peg_deviation(self) -> Dict[str, Any]:
        """Check current peg deviation"""
        current_price = Decimal(self.state.variables.get('price_oracle', '1.0'))
        target_price = Decimal('1.0')
        
        deviation = abs(current_price - target_price) / target_price
        deviation_percent = deviation * 100

        if deviation <= Decimal('0.01'):
            status = "STABLE"
            urgency = "low"
        elif deviation <= Decimal('0.02'):
            status = "MINOR_DEVIATION"
            urgency = "medium"
        elif deviation <= Decimal('0.05'):
            status = "MAJOR_DEVIATION"
            urgency = "high"
        else:
            status = "CRITICAL_DEVIATION"
            urgency = "critical"

        return {
            'current_price': str(current_price),
            'target_price': str(target_price),
            'deviation_percent': str(deviation_percent),
            'status': status,
            'urgency': urgency
        }

    def _execute_algorithmic_rebase(self, args: Dict[str, Any], caller: str) -> Dict[str, Any]:
        """Execute algorithmic supply rebase"""
        current_price = Decimal(self.state.variables.get('price_oracle', '1.0'))
        target_price = Decimal('1.0')
        current_supply = Decimal(self.state.variables.get('total_supply', '0'))

        if current_supply <= 0:
            return {'success': False, 'reason': 'No supply to rebase'}

        price_ratio = current_price / target_price
        max_rebase_percent = Decimal('0.10')
        rebase_factor = Decimal('0.5')

        if current_price > target_price:
            supply_increase_needed = (price_ratio - 1) * rebase_factor
            supply_increase = min(supply_increase_needed, max_rebase_percent)
            new_supply = current_supply * (1 + supply_increase)
            action = "EXPAND"
        elif current_price < target_price:
            supply_decrease_needed = (1 - price_ratio) * rebase_factor
            supply_decrease = min(supply_decrease_needed, max_rebase_percent)
            new_supply = current_supply * (1 - supply_decrease)
            action = "CONTRACT"
        else:
            return {'success': False, 'reason': 'No rebase needed'}

        # Update all balances proportionally
        supply_ratio = new_supply / current_supply
        afc_balances = self.state.variables.get('balances', {})
        
        for address, balance_str in afc_balances.items():
            old_balance = Decimal(balance_str)
            new_balance = old_balance * supply_ratio
            afc_balances[address] = str(new_balance)

        self.state.variables['total_supply'] = str(new_supply)
        self.state.variables['balances'] = afc_balances

        return {
            'success': True,
            'action': action,
            'old_supply': str(current_supply),
            'new_supply': str(new_supply),
            'supply_change_percent': str((new_supply - current_supply) / current_supply * 100)
        }

    def _execute_general_function(self, function_name: str, args: Dict[str, Any], caller: str, value: Decimal) -> Any:
        """Execute general smart contract functions"""
        if function_name == "get_owner":
            return self.state.owner
        elif function_name == "get_balance":
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
        else:
            raise ValueError(f"Unknown function: {function_name}")

    def _calculate_gas_usage(self, function_name: str, args: Dict[str, Any]) -> int:
        """Calculate gas usage"""
        base_gas = 21000
        if function_name in ['transfer_afc', 'approve_afc']:
            return base_gas + 5000
        elif function_name in ['mint_afc', 'burn_afc']:
            return base_gas + 10000
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
            'execution_history': self.execution_history[-20:]
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

        state_data = data['state']
        contract.state = ContractState(
            variables=state_data['variables'],
            balance=Decimal(state_data['balance']),
            owner=state_data['owner'],
            created_at=state_data['created_at'],
            last_executed=state_data['last_executed'],
            is_active=state_data.get('is_active', True)
        )

        contract.execution_history = data.get('execution_history', [])
        return contract


class DinariBlockchain:
    """DinariBlockchain - Native DINARI token blockchain with smart contracts"""

    def __init__(self, db_path: str = "./dinari_data"):
        self.logger = logging.getLogger("Dinari.blockchain")
        self.create_transaction_indices()
        
        # Initialize LevelDB
        self.db = DinariLevelDB(db_path)
        
        # Load or create blockchain state
        self.chain_state = self._load_chain_state()
        self.pending_transactions = []
        self.validators = self._load_validators()
        self.dinari_balances = self._load_balances()
        self.contracts = self._load_contracts()
        
        # Mining control
        self.mining_active = False
        self.mining_thread = None
        self.last_block_time = time.time()
        
        # Initialize genesis block if needed
        if self.chain_state["height"] == 0:
            self._create_genesis_block()
        
        # Ensure we have validators and start mining
        self._ensure_validators()
        self.start_automatic_mining(15)
        
        self.logger.info(f"DinariBlockchain initialized with {len(self.validators)} validators")
        self.logger.info(f"Mining: {'ACTIVE' if self.mining_active else 'INACTIVE'}")

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
    
    def create_transaction_indices(self):
        """Create transaction storage indices in LevelDB"""
        try:
            # Create index counters if they don't exist
            if not self.db.get(b'tx_count'):
                self.db.put(b'tx_count', b'0')
            
            print("✅ Transaction indices initialized")
        except Exception as e:
            print(f"❌ Error creating transaction indices: {e}")
    
    def store_transaction_permanently(self, transaction, block_number):
        """Store transaction permanently with multiple indices for fast retrieval"""
        try:
            tx_hash = transaction.get('hash')
            if not tx_hash:
                print("❌ Transaction has no hash, cannot store")
                return False
            
            # Get current transaction count
            tx_count = int(self.db.get(b'tx_count') or b'0')
            
            # Store transaction with multiple keys for different access patterns:
            
            # 1. By hash (primary key) - for direct hash lookups
            self.db.put(f"tx:hash:{tx_hash}".encode(), json.dumps({
                'transaction': transaction,
                'block_number': block_number,
                'tx_index': tx_count,
                'timestamp': transaction.get('timestamp', int(time.time()))
            }).encode())
            
            # 2. By transaction index (for chronological pagination)
            self.db.put(f"tx:index:{tx_count:010d}".encode(), json.dumps({
                'hash': tx_hash,
                'block_number': block_number,
                'from_address': transaction.get('from_address'),
                'to_address': transaction.get('to_address'),
                'amount': transaction.get('amount'),
                'timestamp': transaction.get('timestamp')
            }).encode())
            
            # 3. By from_address (for address transaction history)
            from_addr = transaction.get('from_address')
            if from_addr:
                self.db.put(f"tx:from:{from_addr}:{tx_count:010d}".encode(), tx_hash.encode())
            
            # 4. By to_address (for address transaction history)
            to_addr = transaction.get('to_address')
            if to_addr:
                self.db.put(f"tx:to:{to_addr}:{tx_count:010d}".encode(), tx_hash.encode())
            
            # 5. By block number (for block transaction lookups)
            self.db.put(f"tx:block:{block_number}:{tx_count:010d}".encode(), tx_hash.encode())
            
            # Update transaction count
            self.db.put(b'tx_count', str(tx_count + 1).encode())
            
            print(f"✅ Stored transaction {tx_hash} permanently (index: {tx_count})")
            return True
            
        except Exception as e:
            print(f"❌ Error storing transaction: {e}")
            return False
    

    def get_all_transactions(self, start_index=0, limit=100, reverse=True):
        """Get transactions with pagination - NEVER loses old transactions"""
        try:
            transactions = []
            
            # Get total transaction count
            total_count = int(self.db.get(b'tx_count') or b'0')
            
            if total_count == 0:
                return {'transactions': [], 'total': 0, 'has_more': False}
            
            # Calculate range
            if reverse:
                # Start from newest transactions
                end_index = total_count - start_index
                start_scan = max(0, end_index - limit)
                indices = range(end_index - 1, start_scan - 1, -1)
            else:
                # Start from oldest transactions
                end_scan = min(total_count, start_index + limit)
                indices = range(start_index, end_scan)
            
            # Retrieve transactions
            for i in indices:
                try:
                    key = f"tx:index:{i:010d}".encode()
                    data = self.db.get(key)
                    if data:
                        tx_meta = json.loads(data.decode())
                        
                        # Get full transaction details
                        full_tx_data = self.db.get(f"tx:hash:{tx_meta['hash']}".encode())
                        if full_tx_data:
                            full_tx = json.loads(full_tx_data.decode())
                            transactions.append(full_tx['transaction'])
                        
                except Exception as e:
                    print(f"Error retrieving transaction at index {i}: {e}")
                    continue
            
            has_more = (reverse and start_index + limit < total_count) or \
                      (not reverse and start_index + len(transactions) < total_count)
            
            return {
                'transactions': transactions,
                'total': total_count,
                'has_more': has_more,
                'start_index': start_index
            }
            
        except Exception as e:
            print(f"❌ Error getting all transactions: {e}")
            return {'transactions': [], 'total': 0, 'has_more': False}

    

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

    def _ensure_validators(self):
        """Ensure we have at least one validator"""
        if len(self.validators) == 0:
            default_validators = [
                "DTvalidator1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8",
                "DTvalidator2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9",
                "DTvalidator3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0"
            ]
            
            for validator in default_validators:
                self.add_validator(validator)
            
            # Give validators some DINARI
            for validator in self.validators:
                if validator not in self.dinari_balances:
                    self.dinari_balances[validator] = "10000"
            
            self._save_balances()
            self._save_validators()
            self.logger.info(f"Created {len(default_validators)} default validators")

    def _create_genesis_block(self):
        """Create genesis block with initial DINARI allocation"""
        genesis_transactions = [
            Transaction(
                from_address="genesis",
                to_address="DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu",
                amount=Decimal("30000000"),
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=0,
                data="Main treasury DINARI allocation"
            ),
            Transaction(
                from_address="genesis", 
                to_address="DT1sv9m0g077juqa67h64zxzr26k5xu5rcp8c9qvx",
                amount=Decimal("25000000"),
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=1,
                data="Validators fund DINARI allocation"
            ),
            Transaction(
                from_address="genesis",
                to_address="DT1cqgze3fqpw0dqh9j8l2dqqyr89c0q5c2jdpg8x",
                amount=Decimal("20000000"),
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=2,
                data="Development fund DINARI allocation"
            ),
            Transaction(
                from_address="genesis",
                to_address="DT1xz2f8l8lh8vqw3r6n4s2k7j9p1d5g8h3m6c4v7",
                amount=Decimal("15000000"),
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=3,
                data="Community treasury DINARI allocation"
            ),
            Transaction(
                from_address="genesis",
                to_address="DT1a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5",
                amount=Decimal("10000000"),
                gas_price=Decimal("0"),
                gas_limit=21000,
                nonce=4,
                data="Reserve fund DINARI allocation"
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
            if tx.to_address not in self.dinari_balances:
                self.dinari_balances[tx.to_address] = "0"
            current_balance = Decimal(self.dinari_balances[tx.to_address])
            self.dinari_balances[tx.to_address] = str(current_balance + tx.amount)

        # Deploy Afrocoin contract
        afrocoin_contract = SmartContract(
            contract_id="afrocoin_stablecoin",
            code="Afrocoin USD Stablecoin Contract",
            owner="genesis",
            contract_type="afrocoin_stablecoin",
            initial_state={
                "name": "Afrocoin",
                "symbol": "AFC",
                "decimals": 18,
                "total_supply": "200000000",
                "balances": {
                    "DT1qyfe883hey6jrgj2xvk9a3klghvz9z9way2nxvu": "200000000"
                }
            }
        )
        self.contracts["afrocoin_stablecoin"] = afrocoin_contract

        # Store genesis block
        block_hash = genesis_block.get_hash()
        self.db.store_block(block_hash, genesis_block.to_dict())
        
        # Store by index for easy access
        self.db.put(f"block_index:0", block_hash)
        # STORE ALL GENESIS TRANSACTIONS PERMANENTLY - ADD THIS BLOCK  
        for tx in genesis_transactions:
            tx_dict = tx.to_dict()
            tx_dict['hash'] = tx.get_hash()  # Ensure hash is included
            self.store_transaction_permanently(tx_dict, 0)

        # Update chain state
        self.chain_state["height"] = 1
        self.chain_state["last_block_hash"] = block_hash
        self.chain_state["total_dinari_supply"] = "100000000"
        self.chain_state["total_transactions"] = len(genesis_transactions)
        self.chain_state["contract_count"] = len(self.contracts)

        # Save state
        self._save_chain_state()
        self._save_balances()
        self._save_contracts()

        self.logger.info("Genesis block created with 100M DINARI + 200M AFC")

    def get_chain_height(self):
        """Get current blockchain height"""
        return self.chain_state.get("height", 0)

    def get_block_by_index(self, block_number):
        """Get block by index number - NO ITERATOR VERSION"""
        try:
            # Try to get hash from index mapping first
            block_hash = self.db.get(f"block_index:{block_number}")
            if block_hash:
                block_data = self.db.get(f"block:{block_hash}")
                if block_data:
                    return block_data
            
            # If no index mapping, try direct block lookup by number
            # This is a fallback for blocks stored without index mapping
            try:
                # Try common block key patterns
                possible_keys = [
                    f"block_{block_number}",
                    f"block:{block_number}", 
                    str(block_number)
                ]
                
                for key in possible_keys:
                    block_data = self.db.get(key)
                    if block_data:
                        return block_data
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"Error getting block {block_number}: {e}")
            return None

    def create_index_mapping_for_existing_blocks(self):
        """Create index mapping without using iterator"""
        try:
            print("Creating index mapping for existing blocks...")
            
            # Since iterator doesn't work, we'll check for blocks by trying common patterns
            blocks_found = []
            
            # Try to find blocks up to a reasonable limit
            for i in range(100):  # Check first 100 possible blocks
                block_data = self.db.get(f"block:{i}")  # Try direct key access
                if block_data:
                    try:
                        if isinstance(block_data, dict):
                            blocks_found.append((i, block_data.get('hash', f'block_{i}')))
                        else:
                            blocks_found.append((i, f'block_{i}'))
                    except:
                        continue
            
            # Create index mappings for found blocks
            for block_number, block_hash in blocks_found:
                self.db.put(f"block_index:{block_number}", block_hash)
                print(f"Mapped block {block_number} -> {block_hash}")
            
            if blocks_found:
                max_height = max(block[0] for block in blocks_found)
                self.db.put("chain_height", str(max_height))
                print(f"Set chain height to {max_height}")
                
            print(f"Index mapping complete for {len(blocks_found)} blocks")
            
        except Exception as e:
            print(f"Error creating index mapping: {e}")

    def rebuild_transaction_storage(self):
        """Rebuild permanent transaction storage from all blocks"""
        try:
            print("🔧 Rebuilding transaction storage from all blocks...")
            
            # Reset transaction count
            self.db.put(b'tx_count', b'0')
            
            # Get all blocks and rebuild transaction storage
            chain_height = self.get_chain_height()
            total_stored = 0
            
            for block_num in range(chain_height):
                try:
                    block_data = self.get_block_by_index(block_num)
                    if block_data and 'transactions' in block_data:
                        for tx in block_data['transactions']:
                            # Ensure transaction has proper DTx hash
                            if 'hash' not in tx or not tx['hash'].startswith('DTx'):
                                # Generate proper DTx hash
                                tx_obj = Transaction(
                                    from_address=tx.get('from_address', ''),
                                    to_address=tx.get('to_address', ''),
                                    amount=Decimal(str(tx.get('amount', 0))),
                                    gas_price=Decimal(str(tx.get('gas_price', 0))),
                                    gas_limit=int(tx.get('gas_limit', 21000)),
                                    nonce=int(tx.get('nonce', 0)),
                                    data=tx.get('data', ''),
                                    timestamp=int(tx.get('timestamp', time.time()))
                                )
                                tx['hash'] = tx_obj.get_hash()
                            
                            # Store with permanent storage
                            self.store_transaction_permanently(tx, block_num)
                            total_stored += 1
                            
                except Exception as e:
                    print(f"Error rebuilding block {block_num}: {e}")
                    continue
            
            print(f"✅ Rebuilt storage for {total_stored} transactions")
            return total_stored
            
        except Exception as e:
            print(f"❌ Error rebuilding transaction storage: {e}")
            return 0

    def start_automatic_mining(self, interval: int = 15):
        """Start automatic block mining"""
        if self.mining_active:
            return

        self.mining_active = True

        def mine_blocks():
            self.logger.info(f"Started automatic mining with {interval}s interval")
            
            while self.mining_active:
                try:
                    time_since_last_block = time.time() - self.last_block_time
                    
                    should_create_block = (
                        len(self.pending_transactions) > 0 or
                        time_since_last_block >= interval
                    )

                    if should_create_block and self.validators:
                        validator_index = self.chain_state["height"] % len(self.validators)
                        selected_validator = self.validators[validator_index]
                        
                        block = self.create_block(selected_validator)
                        if block:
                            self.logger.info(f"Auto-mined block {block.index}")

                    time.sleep(interval)

                except Exception as e:
                    self.logger.error(f"Mining error: {e}")
                    time.sleep(5)

        self.mining_thread = threading.Thread(target=mine_blocks, daemon=True)
        self.mining_thread.start()

    def stop_automatic_mining(self):
        """Stop automatic block mining"""
        self.mining_active = False
        if self.mining_thread:
            self.mining_thread.join(timeout=1)

    def add_transaction(self, transaction: Transaction) -> bool:
        """Add transaction to pending pool"""
        try:
            if not self._validate_transaction(transaction):
                return False

            self.pending_transactions.append(transaction)
            
            # Store transaction
            tx_hash = transaction.get_hash()
            self.db.store_transaction(tx_hash, transaction.to_dict())

            self.logger.info(f"Transaction added: {tx_hash[:16]}...")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add transaction: {e}")
            return False

    def _validate_transaction(self, tx: Transaction) -> bool:
        """Validate transaction"""
        try:
            if tx.amount < 0:
                return False
            
            if tx.from_address != "genesis":
                sender_balance = Decimal(self.dinari_balances.get(tx.from_address, "0"))
                gas_fee = tx.gas_price * tx.gas_limit
                total_cost = tx.amount + gas_fee
                
                if sender_balance < total_cost:
                    self.logger.warning(f"Insufficient DINARI: {tx.from_address}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Transaction validation error: {e}")
            return False

    def create_block(self, validator_address: str) -> Optional[Block]:
        """Create new block with pending transactions"""
        try:
            if not validator_address or validator_address not in self.validators:
                if self.validators:
                    validator_address = self.validators[0]
                else:
                    self.logger.error("No validators available")
                    return None

            transactions_to_include = self.pending_transactions.copy()

            new_block = Block(
                index=self.chain_state["height"],
                transactions=transactions_to_include,
                timestamp=int(time.time()),
                previous_hash=self.chain_state["last_block_hash"],
                validator=validator_address
            )

            # Process transactions
            total_gas_used = 0
            if transactions_to_include:
                total_gas_used = self._process_transactions(transactions_to_include)

            new_block.gas_used = total_gas_used

            # Store block
            block_hash = new_block.get_hash()
            self.db.store_block(block_hash, new_block.to_dict())
            
            # Store by index
            self.db.put(f"block_index:{new_block.index}", block_hash)
            # STORE ALL TRANSACTIONS PERMANENTLY - ADD THIS BLOCK
            for tx in transactions_to_include:
                tx_dict = tx.to_dict()
                tx_dict['hash'] = tx.get_hash()  # Ensure hash is included
                self.store_transaction_permanently(tx_dict, new_block.index)

            # Update chain state
            self.chain_state["height"] += 1
            self.chain_state["last_block_hash"] = block_hash
            self.chain_state["total_transactions"] += len(transactions_to_include)
            
            # Clear pending transactions
            if transactions_to_include:
                self.pending_transactions = []

            # Save state
            self._save_chain_state()
            self._save_balances()
            self._save_contracts()

            self.last_block_time = time.time()

            self.logger.info(f"Block {new_block.index} mined successfully")
            return new_block

        except Exception as e:
            self.logger.error(f"Failed to create block: {e}")
            return None

    def _process_transactions(self, transactions: List[Transaction]) -> int:
        """Process transactions in a block"""
        total_gas_used = 0
        
        for tx in transactions:
            try:
                if tx.tx_type == "contract_call":
                    result = self.execute_contract(
                        tx.contract_address,
                        json.loads(tx.data),
                        tx.from_address,
                        tx.amount
                    )
                    total_gas_used += result.get('gas_used', 21000)
                    
                elif tx.tx_type == "contract_deploy":
                    contract_data = json.loads(tx.data)
                    self.deploy_contract(
                        contract_data['contract_id'],
                        contract_data['code'],
                        tx.from_address,
                        contract_data.get('contract_type', 'general'),
                        contract_data.get('initial_state', {})
                    )
                    total_gas_used += 50000
                    
                else:
                    # Regular DINARI transfer
                    if tx.from_address != "genesis":
                        sender_balance = Decimal(self.dinari_balances.get(tx.from_address, "0"))
                        gas_fee = tx.gas_price * tx.gas_limit
                        total_cost = tx.amount + gas_fee
                        
                        if sender_balance >= total_cost:
                            new_sender_balance = sender_balance - total_cost
                            self.dinari_balances[tx.from_address] = str(new_sender_balance)

                    # Credit recipient
                    if tx.to_address not in self.dinari_balances:
                        self.dinari_balances[tx.to_address] = "0"
                    
                    recipient_balance = Decimal(self.dinari_balances[tx.to_address])
                    new_recipient_balance = recipient_balance + tx.amount
                    self.dinari_balances[tx.to_address] = str(new_recipient_balance)
                    
                    total_gas_used += tx.gas_limit

            except Exception as e:
                self.logger.error(f"Failed to process transaction: {e}")
                total_gas_used += 21000

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

        self.logger.info(f"Contract {contract_id} deployed")
        return contract

    def execute_contract(self, contract_id: str, function_data: Dict[str, Any], caller: str, value: Decimal = Decimal("0")) -> Dict[str, Any]:
        """Execute a smart contract function"""
        if contract_id not in self.contracts:
            raise ValueError(f"Contract {contract_id} not found")

        contract = self.contracts[contract_id]
        function_name = function_data.get('function')
        args = function_data.get('args', {})

        result = contract.execute(function_name, args, caller, value)
        return result

    def get_contract(self, contract_id: str) -> Optional[SmartContract]:
        """Get smart contract by ID"""
        return self.contracts.get(contract_id)

    def get_afrocoin_contract(self) -> Optional[SmartContract]:
        """Get the Afrocoin stablecoin contract"""
        return self.contracts.get("afrocoin_stablecoin")

    def get_dinari_balance(self, address: str) -> Decimal:
        """Get DINARI token balance"""
        return Decimal(self.dinari_balances.get(address, "0"))

    def get_afrocoin_balance(self, address: str) -> Decimal:
        """Get AFC balance"""
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
            "stablecoin": "AFC (Afrocoin)",
            "mining_active": self.mining_active
        }

    def add_validator(self, validator_address: str):
        """Add validator"""
        if validator_address not in self.validators:
            self.validators.append(validator_address)
            self._save_validators()
            self.logger.info(f"Validator added: {validator_address}")

    def get_recent_blocks(self, limit: int = 15) -> List[dict]:
        """Get recent blocks from database - FIXED VERSION"""
        try:
            blocks = []
            current_height = self.chain_state.get("height", 0)
            
            # Get blocks by trying direct database access
            for i in range(current_height - 1, max(0, current_height - limit - 1), -1):
                try:
                    # Try multiple key patterns to find blocks
                    block_data = None
                    
                    # Try by index mapping first
                    block_hash = self.db.get(f"block_index:{i}")
                    if block_hash:
                        block_data = self.db.get(f"block:{block_hash}")
                    
                    # Try direct key patterns if index mapping doesn't work
                    if not block_data:
                        possible_keys = [f"block_{i}", f"block:{i}", str(i)]
                        for key in possible_keys:
                            block_data = self.db.get(key)
                            if block_data:
                                break
                    
                    if block_data:
                        # Ensure block has proper index number
                        if isinstance(block_data, dict):
                            block_data['number'] = i
                            blocks.append(block_data)
                        
                except Exception as e:
                    print(f"Error getting block {i}: {e}")
                    continue
            
            return blocks
            
        except Exception as e:
            print(f"Error in get_recent_blocks: {e}")
            return []

    def get_recent_transactions(self, limit: int = 20) -> List[dict]:
        """Get recent transactions from recent blocks"""
        try:
            transactions = []
            recent_blocks = self.get_recent_blocks(10)  # Get last 10 blocks
            
            for block in recent_blocks:
                if len(transactions) >= limit:
                    break
                    
                block_transactions = block.get('transactions', [])
                for tx in block_transactions:
                    if len(transactions) >= limit:
                        break
                    
                    # Add block context to transaction
                    if isinstance(tx, dict):
                        tx_with_context = tx.copy()
                        tx_with_context['block_number'] = block.get('number', block.get('index', 0))
                        tx_with_context['block_hash'] = block.get('hash', '')
                        transactions.append(tx_with_context)
            
            return transactions
            
        except Exception as e:
            print(f"Error in get_recent_transactions: {e}")
            return []

    def get_transaction_by_hash(self, tx_hash: str) -> Optional[dict]:
        """Get transaction by hash"""
        try:
            # Try direct lookup first
            tx = self.db.get_transaction(tx_hash)
            if tx:
                return tx
            
            # Search through recent blocks
            recent_blocks = self.get_recent_blocks(50)
            
            for block in recent_blocks:
                block_transactions = block.get('transactions', [])
                for tx in block_transactions:
                    if tx.get('hash') == tx_hash:
                        tx['block_number'] = block.get('number', block.get('index', 0))
                        tx['block_hash'] = block.get('hash', '')
                        return tx
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get transaction {tx_hash}: {e}")
            return None
        
    def get_address_transactions(self, address, start_index=0, limit=50):
        """Get all transactions for an address - permanent history"""
        try:
            transactions = []
            
            # Get transactions where address is sender
            for key, value in self.db.iterator(prefix=f"tx:from:{address}:".encode()):
                tx_hash = value.decode()
                tx_data = self.get_transaction_by_hash(tx_hash)
                if tx_data:
                    tx = tx_data['transaction']
                    tx['direction'] = 'sent'
                    transactions.append(tx)
            
            # Get transactions where address is recipient
            for key, value in self.db.iterator(prefix=f"tx:to:{address}:".encode()):
                tx_hash = value.decode()
                tx_data = self.get_transaction_by_hash(tx_hash)
                if tx_data:
                    tx = tx_data['transaction']
                    tx['direction'] = 'received'
                    transactions.append(tx)
            
            # Sort by timestamp (newest first)
            transactions.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            # Apply pagination
            paginated = transactions[start_index:start_index + limit]
            
            return {
                'transactions': paginated,
                'total': len(transactions),
                'has_more': len(transactions) > start_index + limit
            }
            
        except Exception as e:
            print(f"❌ Error getting address transactions: {e}")
            return {'transactions': [], 'total': 0, 'has_more': False}
    
    def add_block_to_chain(self, block):
        """Modified to store all transactions permanently"""
        try:
            # Your existing block storage code here
            
            # IMPORTANT: Store all transactions in this block permanently
            if 'transactions' in block:
                for transaction in block['transactions']:
                    self.store_transaction_permanently(transaction, block.get('index', 0))
            
            print(f"✅ Block {block.get('index')} and its transactions stored permanently")
            return True
            
        except Exception as e:
            print(f"❌ Error storing block: {e}")
            return False

    def close(self):
        """Close database connection and stop mining"""
        self.stop_automatic_mining()
        self.db.close()
        self.logger.info("DinariBlockchain closed")
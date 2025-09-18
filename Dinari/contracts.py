#!/usr/bin/env python3
"""
DinariBlockchain Smart Contract System
Dinari/contracts.py - Comprehensive smart contract execution engine
"""

import hashlib
import json
import time
import ast
import sys
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
import logging
from decimal import Decimal

@dataclass
class ContractDeployment:
    """Contract deployment information"""
    address: str
    deployer: str
    code_hash: str
    deployed_at: float
    gas_used: int
    deployment_tx: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ContractExecution:
    """Contract execution result"""
    success: bool
    result: Any = None
    error: str = ""
    gas_used: int = 0
    state_changes: Dict[str, Any] = None
    events: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.state_changes is None:
            self.state_changes = {}
        if self.events is None:
            self.events = []

class SafePythonExecutor:
    """Safe Python code execution environment for smart contracts"""
    
    # Allowed built-in functions for contract execution
    ALLOWED_BUILTINS = {
        'len', 'str', 'int', 'float', 'bool', 'dict', 'list', 'tuple', 'set',
        'max', 'min', 'sum', 'abs', 'round', 'sorted', 'reversed',
        'enumerate', 'zip', 'range', 'any', 'all'
    }
    
    # Prohibited statements and functions
    PROHIBITED_NODES = {
            ast.Import, ast.ImportFrom,  # No imports
            ast.Global, ast.Nonlocal,    # No global access
    }
    
    def __init__(self):
        self.logger = logging.getLogger("SafePythonExecutor")
    
    def validate_code(self, code: str) -> bool:
        """Validate that contract code is safe to execute"""
        try:
            # Parse the code
            tree = ast.parse(code)
            
            # Check for prohibited constructs
            for node in ast.walk(tree):
                if type(node) in self.PROHIBITED_NODES:
                    self.logger.warning(f"Prohibited construct: {type(node).__name__}")
                    return False
                
                # Check for prohibited function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        if func_name.startswith('__') or func_name in ['exec', 'eval', 'open', 'input']:
                            self.logger.warning(f"Prohibited function call: {func_name}")
                            return False
            
            return True
            
        except SyntaxError as e:
            self.logger.error(f"Syntax error in contract code: {e}")
            return False
    
    def create_execution_environment(self, contract, caller: str, blockchain, args: List[Any]) -> Dict[str, Any]:
        """Create safe execution environment for contract"""
        
        # Safe built-ins
        safe_builtins = {name: __builtins__[name] for name in self.ALLOWED_BUILTINS if name in __builtins__}
        
        # Contract API functions
        contract_api = {
            'get_balance': lambda addr: blockchain.get_balance(addr),
            'get_block_height': lambda: len(blockchain.chain),
            'get_timestamp': lambda: time.time(),
            'emit_event': lambda event_name, data: contract.emit_event(event_name, data),
            'require': lambda condition, message="Assertion failed": self._require(condition, message),
            'revert': lambda message="Transaction reverted": self._revert(message)
        }
        
        # Execution environment
        env = {
            '__builtins__': safe_builtins,
            'contract': contract,
            'caller': caller,
            'blockchain': blockchain,
            'args': args,
            'Decimal': Decimal,
            **contract_api
        }
        
        return env
    
    def _require(self, condition: bool, message: str):
        """Contract require function"""
        if not condition:
            raise ContractExecutionError(f"Require failed: {message}")
    
    def _revert(self, message: str):
        """Contract revert function"""
        raise ContractExecutionError(f"Reverted: {message}")

class ContractExecutionError(Exception):
    """Exception raised during contract execution"""
    pass

class DinariSmartContract:
    """Smart contract implementation for Dinari"""
    
    def __init__(self, address: str, code: str, deployer: str, blockchain=None):
        self.address = address
        self.code = code
        self.deployer = deployer
        self.state = {}  # Contract persistent state
        self.events = []  # Contract events log
        self.created_at = time.time()
        self.code_hash = hashlib.sha256(code.encode()).hexdigest()
        
        # Execution environment
        self.executor = SafePythonExecutor()
        self.gas_limit = 1000000  # Default gas limit
        self.gas_used = 0
        
        # Validate code on creation
        if not self.executor.validate_code(code):
            raise ValueError("Contract code validation failed")
        
        # Setup logging
        self.logger = logging.getLogger(f"SmartContract-{address[:8]}")
        
        self.logger.info(f"Smart contract created at {address}")
    
    def execute_function(self, function_name: str, args: List[Any], 
                        caller: str, blockchain) -> ContractExecution:
        """Execute a contract function"""
        start_time = time.time()
        self.gas_used = 0
        execution_events = []
        
        try:
            # Create execution environment
            env = self.executor.create_execution_environment(self, caller, blockchain, args)
            
            # Add event emission capability
            original_emit = self.emit_event
            def tracked_emit_event(event_name: str, data: Dict[str, Any]):
                event = original_emit(event_name, data)
                execution_events.append(event)
                return event
            
            env['emit_event'] = tracked_emit_event
            
            # Execute contract code to define functions
            exec(self.code, env)
            
            # Check if function exists
            if function_name not in env:
                return ContractExecution(
                    success=False,
                    error=f"Function '{function_name}' not found in contract",
                    gas_used=1000
                )
            
            # Execute the function
            result = env[function_name](*args)
            
            # Calculate gas usage (simplified)
            execution_time = time.time() - start_time
            gas_used = max(1000, int(execution_time * 10000))  # Base cost + time-based
            gas_used += len(self.code) // 10  # Code size factor
            gas_used += len(str(self.state)) // 5  # State size factor
            
            self.gas_used = gas_used
            
            return ContractExecution(
                success=True,
                result=result,
                gas_used=gas_used,
                state_changes=self.state.copy(),
                events=execution_events
            )
            
        except ContractExecutionError as e:
            return ContractExecution(
                success=False,
                error=str(e),
                gas_used=max(1000, self.gas_used),
                events=execution_events
            )
        except Exception as e:
            self.logger.error(f"Contract execution error: {e}")
            return ContractExecution(
                success=False,
                error=f"Runtime error: {str(e)}",
                gas_used=max(1000, self.gas_used),
                events=execution_events
            )
    
    def emit_event(self, event_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Emit a contract event"""
        event = {
            'event_name': event_name,
            'data': data,
            'contract_address': self.address,
            'timestamp': time.time(),
            'block_height': None  # Set by blockchain when included in block
        }
        
        self.events.append(event)
        self.logger.info(f"Event emitted: {event_name}")
        return event
    
    def get_state(self) -> Dict[str, Any]:
        """Get contract state"""
        return self.state.copy()
    
    def set_state(self, key: str, value: Any):
        """Set contract state (internal use)"""
        self.state[key] = value
    
    def get_events(self, event_name: str = None) -> List[Dict[str, Any]]:
        """Get contract events"""
        if event_name:
            return [event for event in self.events if event['event_name'] == event_name]
        return self.events.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contract to dictionary"""
        return {
            'address': self.address,
            'code': self.code,
            'deployer': self.deployer,
            'state': self.state,
            'events': self.events,
            'created_at': self.created_at,
            'code_hash': self.code_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], blockchain=None) -> 'DinariSmartContract':
        """Create contract from dictionary"""
        contract = cls(
            address=data['address'],
            code=data['code'],
            deployer=data['deployer'],
            blockchain=blockchain
        )
        contract.state = data.get('state', {})
        contract.events = data.get('events', [])
        contract.created_at = data.get('created_at', time.time())
        return contract

class ContractManager:
    """Manages smart contracts for Dinari blockchain"""
    
    def __init__(self, blockchain=None):
        self.blockchain = blockchain
        self.contracts: Dict[str, DinariSmartContract] = {}
        self.contract_templates = {}
        
        # Load standard contract templates
        self._load_standard_contracts()
        
        # Setup logging
        self.logger = logging.getLogger("ContractManager")
    
    def _load_standard_contracts(self):
        """Load standard contract templates"""
        
        # ERC20-like Token Contract
        self.contract_templates['token'] = '''
# Dinari Token Contract (ERC20-like)
def __init__(name, symbol, total_supply):
    contract.state['name'] = name
    contract.state['symbol'] = symbol
    contract.state['total_supply'] = int(total_supply)
    contract.state['balances'] = {contract.deployer: int(total_supply)}
    contract.state['allowances'] = {}
    emit_event('Transfer', {'from': 'genesis', 'to': contract.deployer, 'value': total_supply})

def name():
    return contract.state.get('name', 'Unknown Token')

def symbol():
    return contract.state.get('symbol', 'UNK')

def total_supply():
    return contract.state.get('total_supply', 0)

def balance_of(account):
    return contract.state.get('balances', {}).get(account, 0)

def transfer(to, amount):
    require(amount > 0, "Amount must be positive")
    
    balances = contract.state.get('balances', {})
    from_balance = balances.get(caller, 0)
    
    require(from_balance >= amount, "Insufficient balance")
    
    balances[caller] = from_balance - amount
    balances[to] = balances.get(to, 0) + amount
    contract.state['balances'] = balances
    
    emit_event('Transfer', {'from': caller, 'to': to, 'value': amount})
    return True

def approve(spender, amount):
    allowances = contract.state.get('allowances', {})
    if caller not in allowances:
        allowances[caller] = {}
    allowances[caller][spender] = amount
    contract.state['allowances'] = allowances
    
    emit_event('Approval', {'owner': caller, 'spender': spender, 'value': amount})
    return True

def allowance(owner, spender):
    allowances = contract.state.get('allowances', {})
    return allowances.get(owner, {}).get(spender, 0)

def transfer_from(from_addr, to, amount):
    require(amount > 0, "Amount must be positive")
    
    allowances = contract.state.get('allowances', {})
    allowed = allowances.get(from_addr, {}).get(caller, 0)
    require(allowed >= amount, "Allowance exceeded")
    
    balances = contract.state.get('balances', {})
    from_balance = balances.get(from_addr, 0)
    require(from_balance >= amount, "Insufficient balance")
    
    # Update balances
    balances[from_addr] = from_balance - amount
    balances[to] = balances.get(to, 0) + amount
    contract.state['balances'] = balances
    
    # Update allowance
    allowances[from_addr][caller] = allowed - amount
    contract.state['allowances'] = allowances
    
    emit_event('Transfer', {'from': from_addr, 'to': to, 'value': amount})
    return True
'''
        
        # Voting Contract
        self.contract_templates['voting'] = '''
# Simple Voting Contract
def __init__(title, options, voting_period):
    contract.state['title'] = title
    contract.state['options'] = options
    contract.state['votes'] = {option: 0 for option in options}
    contract.state['voters'] = set()
    contract.state['voting_period'] = int(voting_period)
    contract.state['created_at'] = get_timestamp()
    contract.state['ended'] = False

def vote(option):
    require(not contract.state['ended'], "Voting has ended")
    require(caller not in contract.state['voters'], "Already voted")
    require(option in contract.state['options'], "Invalid option")
    
    # Check voting period
    if get_timestamp() > contract.state['created_at'] + contract.state['voting_period']:
        contract.state['ended'] = True
        revert("Voting period has expired")
    
    contract.state['votes'][option] += 1
    contract.state['voters'].add(caller)
    
    emit_event('Vote', {'voter': caller, 'option': option})
    return True

def get_results():
    return contract.state['votes']

def get_winner():
    if not contract.state['ended']:
        return None
    
    votes = contract.state['votes']
    winner = max(votes, key=votes.get)
    return {'winner': winner, 'votes': votes[winner]}

def end_voting():
    require(caller == contract.deployer, "Only deployer can end voting")
    contract.state['ended'] = True
    emit_event('VotingEnded', get_winner())
    return True
'''
        
        # Multi-signature Wallet Contract
        self.contract_templates['multisig'] = '''
# Multi-signature Wallet Contract
def __init__(owners, required_signatures):
    require(len(owners) > 0, "Need at least one owner")
    require(required_signatures > 0 and required_signatures <= len(owners), "Invalid required signatures")
    
    contract.state['owners'] = set(owners)
    contract.state['required_signatures'] = int(required_signatures)
    contract.state['transactions'] = []
    contract.state['confirmations'] = {}

def submit_transaction(to, amount, data=""):
    require(caller in contract.state['owners'], "Not an owner")
    
    tx_id = len(contract.state['transactions'])
    transaction = {
        'id': tx_id,
        'to': to,
        'amount': int(amount),
        'data': data,
        'executed': False,
        'created_by': caller,
        'created_at': get_timestamp()
    }
    
    contract.state['transactions'].append(transaction)
    contract.state['confirmations'][tx_id] = set()
    
    emit_event('TransactionSubmitted', {'tx_id': tx_id, 'to': to, 'amount': amount})
    return tx_id

def confirm_transaction(tx_id):
    require(caller in contract.state['owners'], "Not an owner")
    require(tx_id < len(contract.state['transactions']), "Transaction not found")
    require(not contract.state['transactions'][tx_id]['executed'], "Already executed")
    
    contract.state['confirmations'][tx_id].add(caller)
    
    emit_event('TransactionConfirmed', {'tx_id': tx_id, 'owner': caller})
    
    # Check if enough confirmations
    if len(contract.state['confirmations'][tx_id]) >= contract.state['required_signatures']:
        return execute_transaction(tx_id)
    
    return False

def execute_transaction(tx_id):
    require(tx_id < len(contract.state['transactions']), "Transaction not found")
    
    transaction = contract.state['transactions'][tx_id]
    require(not transaction['executed'], "Already executed")
    require(len(contract.state['confirmations'][tx_id]) >= contract.state['required_signatures'], "Not enough confirmations")
    
    # Mark as executed
    contract.state['transactions'][tx_id]['executed'] = True
    
    emit_event('TransactionExecuted', {'tx_id': tx_id})
    return True

def get_transaction(tx_id):
    if tx_id >= len(contract.state['transactions']):
        return None
    return contract.state['transactions'][tx_id]

def get_confirmations(tx_id):
    return list(contract.state['confirmations'].get(tx_id, set()))
'''
    
    def generate_contract_address(self, deployer: str, code: str) -> str:
        """Generate unique contract address"""
        contract_data = f"{deployer}{code}{time.time()}"
        address_hash = hashlib.sha256(contract_data.encode()).hexdigest()
        return f"0xDINARI{address_hash[:37]}"  # Dinari contract prefix
    
    def deploy_contract(self, code: str, deployer: str, 
                       init_args: List[Any] = None) -> ContractDeployment:
        """Deploy a new smart contract"""
        
        # Generate contract address
        contract_address = self.generate_contract_address(deployer, code)
        
        try:
            # Create contract instance
            contract = DinariSmartContract(contract_address, code, deployer, self.blockchain)
            
            # Execute constructor if init_args provided
            if init_args:
                result = contract.execute_function('__init__', init_args, deployer, self.blockchain)
                if not result.success:
                    raise ValueError(f"Contract initialization failed: {result.error}")
            
            # Store contract
            self.contracts[contract_address] = contract
            
            # Create deployment record
            deployment = ContractDeployment(
                address=contract_address,
                deployer=deployer,
                code_hash=contract.code_hash,
                deployed_at=time.time(),
                gas_used=result.gas_used if init_args else 1000,
                deployment_tx=""  # Set by blockchain
            )
            
            self.logger.info(f"Contract deployed: {contract_address}")
            
            return deployment
            
        except Exception as e:
            self.logger.error(f"Contract deployment failed: {e}")
            raise ValueError(f"Deployment failed: {str(e)}")
    
    def deploy_from_template(self, template_name: str, deployer: str, 
                           init_args: List[Any]) -> ContractDeployment:
        """Deploy contract from template"""
        if template_name not in self.contract_templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        code = self.contract_templates[template_name]
        return self.deploy_contract(code, deployer, init_args)
    
    def call_contract(self, contract_address: str, function_name: str,
                     args: List[Any], caller: str) -> ContractExecution:
        """Call contract function"""
        if contract_address not in self.contracts:
            return ContractExecution(
                success=False,
                error=f"Contract {contract_address} not found"
            )
        
        contract = self.contracts[contract_address]
        return contract.execute_function(function_name, args, caller, self.blockchain)
    
    def get_contract(self, address: str) -> Optional[DinariSmartContract]:
        """Get contract by address"""
        return self.contracts.get(address)
    
    def get_all_contracts(self) -> Dict[str, DinariSmartContract]:
        """Get all deployed contracts"""
        return self.contracts.copy()
    
    def get_contract_events(self, contract_address: str, 
                           event_name: str = None) -> List[Dict[str, Any]]:
        """Get contract events"""
        if contract_address not in self.contracts:
            return []
        
        return self.contracts[contract_address].get_events(event_name)
    
    def get_contracts_by_deployer(self, deployer: str) -> List[str]:
        """Get contracts deployed by address"""
        return [
            addr for addr, contract in self.contracts.items()
            if contract.deployer == deployer
        ]

# Example usage and testing
if __name__ == "__main__":
    # Test smart contract system
    manager = ContractManager()
    
    print("🧪 Testing DinariBlockchain Smart Contract System")
    print("=" * 50)
    
    # Deploy token contract
    print("📦 Deploying token contract...")
    try:
        deployment = manager.deploy_from_template(
            'token', 
            'DINARI123deployer456', 
            ['AfroToken', 'ATK', '1000000']
        )
        
        print(f"✅ Token contract deployed at: {deployment.address}")
        
        # Test token functions
        print("\n💰 Testing token functions...")
        
        # Check balance
        result = manager.call_contract(deployment.address, 'balance_of', ['DINARI123deployer456'], 'DINARI123deployer456')
        print(f"Deployer balance: {result.result}")
        
        # Transfer tokens
        result = manager.call_contract(deployment.address, 'transfer', ['DINARIuser123', 1000], 'DINARI123deployer456')
        print(f"Transfer result: {result.success}")
        
        # Check events
        events = manager.get_contract_events(deployment.address, 'Transfer')
        print(f"Transfer events: {len(events)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n✅ Smart contract system test completed!")

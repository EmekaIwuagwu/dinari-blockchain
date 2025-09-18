#!/usr/bin/env python3
"""
DinariBlockchain Consensus Implementation
Dinari/consensus.py - Proof of Authority consensus mechanism
"""

import time
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
from decimal import Decimal

# Import blockchain components
from .blockchain import Block, Transaction

class ConsensusType(Enum):
    """Types of consensus mechanisms"""
    PROOF_OF_AUTHORITY = "proof_of_authority"
    PROOF_OF_WORK = "proof_of_work"  # Future implementation
    PROOF_OF_STAKE = "proof_of_stake"  # Future implementation

@dataclass
class ValidatorInfo:
    """Information about a validator"""
    address: str
    name: str
    added_at: float
    added_by: str
    is_active: bool = True
    blocks_mined: int = 0
    last_block_time: float = 0
    reputation_score: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'address': self.address,
            'name': self.name,
            'added_at': self.added_at,
            'added_by': self.added_by,
            'is_active': self.is_active,
            'blocks_mined': self.blocks_mined,
            'last_block_time': self.last_block_time,
            'reputation_score': self.reputation_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidatorInfo':
        return cls(**data)

@dataclass
class ConsensusConfig:
    """Consensus configuration parameters"""
    consensus_type: ConsensusType
    block_time: int  # Target block time in seconds
    min_validators: int  # Minimum validators required
    max_validators: int  # Maximum validators allowed
    validator_rotation: bool  # Whether to rotate validators
    epoch_length: int  # Blocks per epoch
    validator_timeout: int  # Seconds before validator is considered inactive
    reputation_threshold: float  # Minimum reputation to remain active
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'consensus_type': self.consensus_type.value,
            'block_time': self.block_time,
            'min_validators': self.min_validators,
            'max_validators': self.max_validators,
            'validator_rotation': self.validator_rotation,
            'epoch_length': self.epoch_length,
            'validator_timeout': self.validator_timeout,
            'reputation_threshold': self.reputation_threshold
        }

class ProofOfAuthority:
    """Proof of Authority consensus implementation for Dinari"""
    
    def __init__(self, config: ConsensusConfig, initial_validators: List[str] = None):
        self.config = config
        self.validators: Dict[str, ValidatorInfo] = {}
        self.validator_order: List[str] = []  # For round-robin scheduling
        self.current_epoch = 0
        self.blocks_in_epoch = 0
        
        # Validator performance tracking
        self.validator_stats = {}
        self.missed_blocks = {}
        
        # Initialize validators
        if initial_validators:
            for validator in initial_validators:
                self.add_validator(validator, f"validator_{validator}", "genesis")
        
        # Setup logging
        self.logger = logging.getLogger("ProofOfAuthority")
        self.logger.info(f"PoA consensus initialized with {len(self.validators)} validators")
    
    def add_validator(self, address: str, name: str, added_by: str) -> bool:
        """Add a new validator to the network"""
        
        # Check if validator already exists
        if address in self.validators:
            self.logger.warning(f"Validator {address} already exists")
            return False
        
        # Check maximum validators limit
        if len(self.validators) >= self.config.max_validators:
            self.logger.error(f"Maximum validators ({self.config.max_validators}) reached")
            return False
        
        # Create validator info
        validator_info = ValidatorInfo(
            address=address,
            name=name,
            added_at=time.time(),
            added_by=added_by,
            is_active=True
        )
        
        # Add to validators
        self.validators[address] = validator_info
        self.validator_order.append(address)
        self.validator_stats[address] = {'blocks_mined': 0, 'blocks_missed': 0}
        self.missed_blocks[address] = 0
        
        self.logger.info(f"Validator added: {name} ({address})")
        return True
    
    def remove_validator(self, address: str, removed_by: str) -> bool:
        """Remove a validator from the network"""
        
        if address not in self.validators:
            self.logger.error(f"Validator {address} not found")
            return False
        
        # Check minimum validators requirement
        active_validators = self.get_active_validators()
        if len(active_validators) <= self.config.min_validators:
            self.logger.error(f"Cannot remove validator: minimum ({self.config.min_validators}) required")
            return False
        
        # Remove validator
        validator_name = self.validators[address].name
        del self.validators[address]
        
        if address in self.validator_order:
            self.validator_order.remove(address)
        
        self.logger.info(f"Validator removed: {validator_name} ({address})")
        return True
    
    def deactivate_validator(self, address: str, reason: str = "") -> bool:
        """Deactivate a validator (temporarily disable)"""
        
        if address not in self.validators:
            return False
        
        self.validators[address].is_active = False
        self.logger.warning(f"Validator deactivated: {address} - {reason}")
        return True
    
    def activate_validator(self, address: str) -> bool:
        """Reactivate a validator"""
        
        if address not in self.validators:
            return False
        
        self.validators[address].is_active = True
        self.logger.info(f"Validator reactivated: {address}")
        return True
    
    def get_active_validators(self) -> List[str]:
        """Get list of active validators"""
        return [
            addr for addr, info in self.validators.items() 
            if info.is_active
        ]
    
    def get_current_validator(self, block_height: int) -> Optional[str]:
        """Get the validator who should mine the current block"""
        active_validators = self.get_active_validators()
        
        if not active_validators:
            return None
        
        # Round-robin selection based on block height
        validator_index = block_height % len(active_validators)
        return active_validators[validator_index]
    
    def is_valid_validator(self, address: str, block_height: int) -> bool:
        """Check if address is the valid validator for current block"""
        expected_validator = self.get_current_validator(block_height)
        return expected_validator == address
    
    def validate_block_consensus(self, block: Block, previous_block: Optional[Block] = None) -> bool:
        """Validate block according to PoA consensus rules"""
        
        # Check if validator is authorized
        if block.validator not in self.validators:
            self.logger.error(f"Unknown validator: {block.validator}")
            return False
        
        # Check if validator is active
        if not self.validators[block.validator].is_active:
            self.logger.error(f"Inactive validator: {block.validator}")
            return False
        
        # Check if it's the correct validator's turn (for round-robin)
        if not self.is_valid_validator(block.validator, block.index):
            expected = self.get_current_validator(block.index)
            self.logger.error(f"Wrong validator turn: expected {expected}, got {block.validator}")
            return False
        
        # Check block timing
        if previous_block:
            time_diff = block.timestamp - previous_block.timestamp
            min_time = self.config.block_time * 0.5  # Allow 50% variance
            max_time = self.config.block_time * 10   # Maximum wait time
            
            if time_diff < min_time:
                self.logger.error(f"Block too fast: {time_diff}s < {min_time}s")
                return False
            
            if time_diff > max_time:
                self.logger.warning(f"Block slow: {time_diff}s > {max_time}s")
                # Don't reject, just warn for slow blocks
        
        self.logger.debug(f"Block consensus validation passed for {block.validator}")
        return True
    
    def update_validator_stats(self, block: Block):
        """Update validator statistics after block is mined"""
        validator = block.validator
        
        if validator in self.validators:
            # Update validator info
            self.validators[validator].blocks_mined += 1
            self.validators[validator].last_block_time = block.timestamp
            
            # Update stats
            if validator in self.validator_stats:
                self.validator_stats[validator]['blocks_mined'] += 1
            
            # Reset missed blocks counter
            self.missed_blocks[validator] = 0
            
            # Update reputation (small positive adjustment)
            current_rep = self.validators[validator].reputation_score
            self.validators[validator].reputation_score = min(100.0, current_rep + 0.1)
    
    def handle_missed_block(self, expected_validator: str, block_height: int):
        """Handle when a validator misses their block"""
        
        if expected_validator not in self.validators:
            return
        
        # Increment missed blocks
        self.missed_blocks[expected_validator] += 1
        
        if expected_validator in self.validator_stats:
            self.validator_stats[expected_validator]['blocks_missed'] += 1
        
        # Decrease reputation
        current_rep = self.validators[expected_validator].reputation_score
        self.validators[expected_validator].reputation_score = max(0.0, current_rep - 1.0)
        
        self.logger.warning(f"Validator {expected_validator} missed block {block_height}")
        
        # Deactivate if too many misses or low reputation
        if (self.missed_blocks[expected_validator] >= 5 or 
            self.validators[expected_validator].reputation_score < self.config.reputation_threshold):
            
            self.deactivate_validator(expected_validator, "Poor performance")
    
    def start_new_epoch(self, block_height: int):
        """Start a new consensus epoch"""
        self.current_epoch += 1
        self.blocks_in_epoch = 0
        
        # Validator rotation logic
        if self.config.validator_rotation:
            self._rotate_validators()
        
        # Performance review
        self._review_validator_performance()
        
        self.logger.info(f"Started epoch {self.current_epoch} at block {block_height}")
    
    def _rotate_validators(self):
        """Rotate validator order (optional)"""
        if len(self.validator_order) > 1:
            # Simple rotation: move first validator to end
            first_validator = self.validator_order.pop(0)
            self.validator_order.append(first_validator)
            self.logger.debug("Validators rotated")
    
    def _review_validator_performance(self):
        """Review and adjust validator performance"""
        current_time = time.time()
        
        for address, validator in self.validators.items():
            # Check for inactive validators (haven't mined recently)
            time_since_last_block = current_time - validator.last_block_time
            
            if (validator.is_active and 
                time_since_last_block > self.config.validator_timeout and
                validator.last_block_time > 0):  # Skip if never mined
                
                self.deactivate_validator(address, "Timeout - no recent blocks")
            
            # Reactivate validators with good reputation
            if (not validator.is_active and 
                validator.reputation_score >= self.config.reputation_threshold):
                
                self.activate_validator(address)
    
    def get_validator_info(self, address: str) -> Optional[ValidatorInfo]:
        """Get validator information"""
        return self.validators.get(address)
    
    def get_all_validators(self) -> Dict[str, ValidatorInfo]:
        """Get all validators"""
        return self.validators.copy()
    
    def get_validator_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get validator statistics"""
        stats = {}
        
        for address, validator in self.validators.items():
            validator_stats = self.validator_stats.get(address, {})
            stats[address] = {
                'name': validator.name,
                'is_active': validator.is_active,
                'blocks_mined': validator.blocks_mined,
                'blocks_missed': validator_stats.get('blocks_missed', 0),
                'reputation_score': validator.reputation_score,
                'last_block_time': validator.last_block_time,
                'missed_blocks_current': self.missed_blocks.get(address, 0)
            }
        
        return stats
    
    def get_consensus_status(self) -> Dict[str, Any]:
        """Get overall consensus status"""
        active_validators = self.get_active_validators()
        
        return {
            'consensus_type': self.config.consensus_type.value,
            'current_epoch': self.current_epoch,
            'blocks_in_epoch': self.blocks_in_epoch,
            'total_validators': len(self.validators),
            'active_validators': len(active_validators),
            'min_validators_met': len(active_validators) >= self.config.min_validators,
            'block_time': self.config.block_time,
            'epoch_length': self.config.epoch_length,
            'validator_rotation': self.config.validator_rotation
        }
    
    def can_mine_block(self, validator_address: str, block_height: int) -> Tuple[bool, str]:
        """Check if validator can mine block at given height"""
        
        # Check if validator exists
        if validator_address not in self.validators:
            return False, f"Validator {validator_address} not found"
        
        # Check if validator is active
        if not self.validators[validator_address].is_active:
            return False, f"Validator {validator_address} is inactive"
        
        # Check if it's validator's turn
        expected_validator = self.get_current_validator(block_height)
        if expected_validator != validator_address:
            return False, f"Not validator's turn. Expected: {expected_validator}"
        
        # Check reputation
        reputation = self.validators[validator_address].reputation_score
        if reputation < self.config.reputation_threshold:
            return False, f"Reputation too low: {reputation}"
        
        return True, "Can mine block"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert consensus state to dictionary"""
        return {
            'config': self.config.to_dict(),
            'validators': {addr: info.to_dict() for addr, info in self.validators.items()},
            'validator_order': self.validator_order,
            'current_epoch': self.current_epoch,
            'blocks_in_epoch': self.blocks_in_epoch,
            'validator_stats': self.validator_stats,
            'missed_blocks': self.missed_blocks
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProofOfAuthority':
        """Create consensus from dictionary"""
        
        # Recreate config
        config_data = data['config']
        config = ConsensusConfig(
            consensus_type=ConsensusType(config_data['consensus_type']),
            block_time=config_data['block_time'],
            min_validators=config_data['min_validators'],
            max_validators=config_data['max_validators'],
            validator_rotation=config_data['validator_rotation'],
            epoch_length=config_data['epoch_length'],
            validator_timeout=config_data['validator_timeout'],
            reputation_threshold=config_data['reputation_threshold']
        )
        
        # Create instance
        poa = cls(config)
        
        # Load validators
        poa.validators = {
            addr: ValidatorInfo.from_dict(info_data)
            for addr, info_data in data['validators'].items()
        }
        
        # Load other state
        poa.validator_order = data.get('validator_order', [])
        poa.current_epoch = data.get('current_epoch', 0)
        poa.blocks_in_epoch = data.get('blocks_in_epoch', 0)
        poa.validator_stats = data.get('validator_stats', {})
        poa.missed_blocks = data.get('missed_blocks', {})
        
        return poa

# Helper functions for creating consensus configurations
def create_default_poa_config() -> ConsensusConfig:
    """Create default PoA configuration"""
    return ConsensusConfig(
        consensus_type=ConsensusType.PROOF_OF_AUTHORITY,
        block_time=30,  # 30 seconds
        min_validators=1,
        max_validators=21,  # Like many PoA networks
        validator_rotation=True,
        epoch_length=100,  # 100 blocks per epoch
        validator_timeout=300,  # 5 minutes
        reputation_threshold=50.0
    )

def create_fast_poa_config() -> ConsensusConfig:
    """Create fast PoA configuration for testing"""
    return ConsensusConfig(
        consensus_type=ConsensusType.PROOF_OF_AUTHORITY,
        block_time=5,  # 5 seconds
        min_validators=1,
        max_validators=10,
        validator_rotation=False,
        epoch_length=20,
        validator_timeout=60,  # 1 minute
        reputation_threshold=30.0
    )

# Example usage and testing
if __name__ == "__main__":
    print("🔧 Testing DinariBlockchain Proof of Authority Consensus")
    print("=" * 60)
    
    # Create PoA consensus
    config = create_default_poa_config()
    poa = ProofOfAuthority(config, ["validator1", "validator2", "validator3"])
    
    # Test validator management
    print(f"✅ Initial validators: {len(poa.get_active_validators())}")
    
    # Add validator
    success = poa.add_validator("validator4", "Test Validator 4", "admin")
    print(f"✅ Added validator: {success}")
    
    # Test block validation
    print(f"\n🧪 Testing validator rotation...")
    for height in range(10):
        current_validator = poa.get_current_validator(height)
        print(f"   Block {height}: {current_validator}")
    
    # Test consensus status
    status = poa.get_consensus_status()
    print(f"\n📊 Consensus Status:")
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n✅ PoA consensus test completed!")
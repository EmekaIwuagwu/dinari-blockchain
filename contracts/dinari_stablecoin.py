"""
File: dinari-blockchain/contracts/dinari_stablecoin.py

Dinari Stablecoin Smart Contract
A blockchain-based stablecoin designed for African financial inclusion
Pegged to USD with collateral backing and algorithmic stability mechanisms
"""

import json
import time
from decimal import Decimal, getcontext
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Set high precision for financial calculations
getcontext().prec = 28

class StabilityMechanism(Enum):
    COLLATERAL_BACKED = "collateral_backed"
    ALGORITHMIC = "algorithmic"
    HYBRID = "hybrid"

@dataclass
class CollateralAsset:
    """Represents a collateral asset backing Dinari"""
    symbol: str
    name: str
    address: str
    price_usd: Decimal
    total_deposited: Decimal
    collateral_ratio: Decimal  # Required collateral ratio (e.g., 1.5 = 150%)
    liquidation_threshold: Decimal  # Liquidation threshold (e.g., 1.2 = 120%)
    is_active: bool
    last_updated: int

@dataclass
class UserVault:
    """User's collateral vault for minting Dinari"""
    user_address: str
    collateral_deposits: Dict[str, Decimal]  # asset_symbol -> amount
    dinari_minted: Decimal
    collateral_ratio: Decimal
    last_interaction: int
    is_liquidatable: bool

@dataclass
class StabilityPool:
    """Stability pool for maintaining peg"""
    total_dinari: Decimal
    total_collateral_value: Decimal
    stability_fee: Decimal  # Annual percentage
    liquidation_penalty: Decimal
    redemption_fee: Decimal

@dataclass
class GovernanceProposal:
    """Governance proposal for protocol parameters"""
    proposal_id: str
    proposer: str
    title: str
    description: str
    parameter_changes: Dict[str, any]
    votes_for: Decimal
    votes_against: Decimal
    voting_deadline: int
    status: str  # pending, active, executed, failed
    created_at: int

class DinariStablecoin:
    """
    Dinari Stablecoin Smart Contract
    
    Features:
    - Multi-collateral backing (BTC, ETH, USDC, Gold tokens)
    - Algorithmic stability mechanisms
    - Governance system for parameter adjustment
    - African-focused features (mobile money integration ready)
    - Low transaction costs
    - Transparency and auditability
    """
    
    def __init__(self, initial_admin: str):
        # Contract metadata
        self.name = "Dinari"
        self.symbol = "DINARI"
        self.decimals = 18
        self.total_supply = Decimal('0')
        self.contract_version = "1.0.0"
        self.deployed_at = int(time.time())
        
        # Admin and governance
        self.admin = initial_admin
        self.governance_token_holders = {}  # address -> voting power
        self.proposals = {}  # proposal_id -> GovernanceProposal
        self.proposal_counter = 0
        
        # Balances and allowances
        self.balances = {}  # address -> balance
        self.allowances = {}  # owner -> {spender -> amount}
        
        # Stablecoin mechanisms
        self.target_price = Decimal('1.00')  # Pegged to $1 USD
        self.stability_mechanism = StabilityMechanism.HYBRID
        self.stability_pool = StabilityPool(
            total_dinari=Decimal('0'),
            total_collateral_value=Decimal('0'),
            stability_fee=Decimal('0.02'),  # 2% annually (competitive for Africa)
            liquidation_penalty=Decimal('0.08'),  # 8% penalty
            redemption_fee=Decimal('0.003')  # 0.3% fee (low for financial inclusion)
        )
        
        # Collateral management
        self.collateral_assets = {}  # symbol -> CollateralAsset
        self.user_vaults = {}  # address -> UserVault
        self.total_collateral_ratio = Decimal('0')
        
        # Price oracle (simplified - in production would use Chainlink/Band)
        self.price_feeds = {}  # asset_symbol -> price_usd
        self.oracle_admin = initial_admin
        
        # African-specific features
        self.mobile_money_gateways = {}  # gateway_id -> gateway_info
        self.country_regulations = {}  # country_code -> regulation_info
        self.remittance_corridors = {}  # corridor_id -> corridor_info
        
        # Events (for logging and transparency)
        self.events = []
        
        # Initialize default collateral assets
        self._initialize_collateral_assets()
        
        # Initialize African mobile money gateways
        self._initialize_mobile_money_gateways()
    
    def _initialize_collateral_assets(self):
        """Initialize collateral assets suitable for African markets"""
        collaterals = [
            {
                "symbol": "BTC", "name": "Bitcoin", "address": "btc_token",
                "price_usd": Decimal('43500'), "collateral_ratio": Decimal('1.5'),
                "liquidation_threshold": Decimal('1.2')
            },
            {
                "symbol": "ETH", "name": "Ethereum", "address": "eth_token",
                "price_usd": Decimal('2900'), "collateral_ratio": Decimal('1.4'),
                "liquidation_threshold": Decimal('1.15')
            },
            {
                "symbol": "USDC", "name": "USD Coin", "address": "usdc_token",
                "price_usd": Decimal('1.00'), "collateral_ratio": Decimal('1.05'),
                "liquidation_threshold": Decimal('1.02')
            },
            {
                "symbol": "GOLD", "name": "Tokenized Gold", "address": "gold_token",
                "price_usd": Decimal('2050'), "collateral_ratio": Decimal('1.3'),
                "liquidation_threshold": Decimal('1.1')
            },
            {
                "symbol": "COCOA", "name": "Cocoa Futures Token", "address": "cocoa_token",
                "price_usd": Decimal('2.85'), "collateral_ratio": Decimal('1.6'),
                "liquidation_threshold": Decimal('1.3')
            }
        ]
        
        for collateral in collaterals:
            self.collateral_assets[collateral["symbol"]] = CollateralAsset(
                symbol=collateral["symbol"],
                name=collateral["name"],
                address=collateral["address"],
                price_usd=collateral["price_usd"],
                total_deposited=Decimal('0'),
                collateral_ratio=collateral["collateral_ratio"],
                liquidation_threshold=collateral["liquidation_threshold"],
                is_active=True,
                last_updated=int(time.time())
            )
    
    def _initialize_mobile_money_gateways(self):
        """Initialize African mobile money gateways for integration"""
        gateways = {
            "mpesa": {
                "name": "M-Pesa",
                "countries": ["Kenya", "Tanzania", "Ghana", "Mozambique"],
                "provider": "Vodafone",
                "active": True,
                "fee_percentage": Decimal('0.01')  # 1%
            },
            "mtn_money": {
                "name": "MTN Mobile Money",
                "countries": ["Uganda", "Rwanda", "Cameroon", "Ghana", "Ivory Coast"],
                "provider": "MTN",
                "active": True,
                "fee_percentage": Decimal('0.012')  # 1.2%
            },
            "orange_money": {
                "name": "Orange Money",
                "countries": ["Senegal", "Mali", "Burkina Faso", "Niger", "Cameroon"],
                "provider": "Orange",
                "active": True,
                "fee_percentage": Decimal('0.015')  # 1.5%
            },
            "airtel_money": {
                "name": "Airtel Money",
                "countries": ["Nigeria", "Kenya", "Tanzania", "Uganda", "Zambia"],
                "provider": "Bharti Airtel",
                "active": True,
                "fee_percentage": Decimal('0.011')  # 1.1%
            }
        }
        
        self.mobile_money_gateways = gateways
    
    # ========== CORE ERC-20 FUNCTIONS ==========
    
    def balance_of(self, address: str) -> Decimal:
        """Get Dinari balance of an address"""
        return self.balances.get(address, Decimal('0'))
    
    def transfer(self, from_address: str, to_address: str, amount: Decimal) -> bool:
        """Transfer Dinari between addresses with low transaction costs"""
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
            
        if self.balance_of(from_address) < amount:
            raise ValueError("Insufficient Dinari balance")
        
        self.balances[from_address] = self.balance_of(from_address) - amount
        self.balances[to_address] = self.balance_of(to_address) + amount
        
        self._emit_event("Transfer", {
            "from": from_address,
            "to": to_address,
            "amount": str(amount),
            "timestamp": int(time.time())
        })
        
        return True
    
    def approve(self, owner: str, spender: str, amount: Decimal) -> bool:
        """Approve spending allowance"""
        if owner not in self.allowances:
            self.allowances[owner] = {}
        
        self.allowances[owner][spender] = amount
        
        self._emit_event("Approval", {
            "owner": owner,
            "spender": spender,
            "amount": str(amount),
            "timestamp": int(time.time())
        })
        
        return True
    
    # ========== STABLECOIN CORE FUNCTIONS ==========
    
    def deposit_collateral(self, user_address: str, asset_symbol: str, amount: Decimal) -> bool:
        """Deposit collateral to user's vault for minting Dinari"""
        if asset_symbol not in self.collateral_assets:
            raise ValueError(f"Collateral asset {asset_symbol} not supported")
        
        if not self.collateral_assets[asset_symbol].is_active:
            raise ValueError(f"Collateral asset {asset_symbol} is not active")
        
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        # Initialize user vault if doesn't exist
        if user_address not in self.user_vaults:
            self.user_vaults[user_address] = UserVault(
                user_address=user_address,
                collateral_deposits={},
                dinari_minted=Decimal('0'),
                collateral_ratio=Decimal('0'),
                last_interaction=int(time.time()),
                is_liquidatable=False
            )
        
        vault = self.user_vaults[user_address]
        
        # Update collateral deposits
        current_deposit = vault.collateral_deposits.get(asset_symbol, Decimal('0'))
        vault.collateral_deposits[asset_symbol] = current_deposit + amount
        vault.last_interaction = int(time.time())
        
        # Update total deposited for asset
        self.collateral_assets[asset_symbol].total_deposited += amount
        
        # Recalculate collateral ratio
        self._update_vault_collateral_ratio(user_address)
        
        self._emit_event("CollateralDeposited", {
            "user": user_address,
            "asset": asset_symbol,
            "amount": str(amount),
            "new_collateral_ratio": str(vault.collateral_ratio),
            "timestamp": int(time.time())
        })
        
        return True
    
    def mint_dinari(self, user_address: str, dinari_amount: Decimal) -> bool:
        """Mint Dinari against collateral with safety checks"""
        if dinari_amount <= 0:
            raise ValueError("Mint amount must be positive")
        
        if user_address not in self.user_vaults:
            raise ValueError("No collateral vault found for user")
        
        vault = self.user_vaults[user_address]
        
        # Calculate what the collateral ratio would be after minting
        total_collateral_value = self._calculate_vault_collateral_value(user_address)
        new_dinari_total = vault.dinari_minted + dinari_amount
        
        if new_dinari_total == 0:
            raise ValueError("Cannot mint zero Dinari")
        
        new_collateral_ratio = total_collateral_value / new_dinari_total
        
        # Check minimum collateral ratio requirement (take the highest requirement)
        min_collateral_ratio = Decimal('1.1')  # Default 110%
        for asset_symbol, deposit_amount in vault.collateral_deposits.items():
            if deposit_amount > 0:
                asset_min_ratio = self.collateral_assets[asset_symbol].collateral_ratio
                min_collateral_ratio = max(min_collateral_ratio, asset_min_ratio)
        
        if new_collateral_ratio < min_collateral_ratio:
            raise ValueError(f"Insufficient collateral. Required ratio: {min_collateral_ratio}, current: {new_collateral_ratio}")
        
        # Mint Dinari
        vault.dinari_minted = new_dinari_total
        vault.collateral_ratio = new_collateral_ratio
        vault.last_interaction = int(time.time())
        
        # Add to user's balance
        self.balances[user_address] = self.balance_of(user_address) + dinari_amount
        self.total_supply += dinari_amount
        
        # Update stability pool
        self.stability_pool.total_dinari += dinari_amount
        
        self._emit_event("DinariMinted", {
            "user": user_address,
            "amount": str(dinari_amount),
            "collateral_ratio": str(new_collateral_ratio),
            "total_supply": str(self.total_supply),
            "timestamp": int(time.time())
        })
        
        return True
    
    def burn_dinari(self, user_address: str, dinari_amount: Decimal) -> bool:
        """Burn Dinari to improve collateral ratio or prepare for collateral withdrawal"""
        if dinari_amount <= 0:
            raise ValueError("Burn amount must be positive")
        
        if self.balance_of(user_address) < dinari_amount:
            raise ValueError("Insufficient Dinari balance to burn")
        
        if user_address not in self.user_vaults:
            raise ValueError("No vault found for user")
        
        vault = self.user_vaults[user_address]
        
        if vault.dinari_minted < dinari_amount:
            raise ValueError("Cannot burn more Dinari than minted from vault")
        
        # Burn Dinari
        self.balances[user_address] = self.balance_of(user_address) - dinari_amount
        self.total_supply -= dinari_amount
        vault.dinari_minted -= dinari_amount
        vault.last_interaction = int(time.time())
        
        # Update stability pool
        self.stability_pool.total_dinari -= dinari_amount
        
        # Recalculate collateral ratio
        self._update_vault_collateral_ratio(user_address)
        
        self._emit_event("DinariBurned", {
            "user": user_address,
            "amount": str(dinari_amount),
            "new_collateral_ratio": str(vault.collateral_ratio),
            "total_supply": str(self.total_supply),
            "timestamp": int(time.time())
        })
        
        return True
    
    def withdraw_collateral(self, user_address: str, asset_symbol: str, amount: Decimal) -> bool:
        """Withdraw collateral from vault (if collateral ratio allows)"""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        if user_address not in self.user_vaults:
            raise ValueError("No vault found for user")
        
        vault = self.user_vaults[user_address]
        current_deposit = vault.collateral_deposits.get(asset_symbol, Decimal('0'))
        
        if current_deposit < amount:
            raise ValueError("Insufficient collateral to withdraw")
        
        # Calculate collateral ratio after withdrawal
        vault_copy = vault.__dict__.copy()
        vault_copy['collateral_deposits'] = vault.collateral_deposits.copy()
        vault_copy['collateral_deposits'][asset_symbol] = current_deposit - amount
        
        new_collateral_value = self._calculate_collateral_value(vault_copy['collateral_deposits'])
        
        if vault.dinari_minted > 0:
            new_collateral_ratio = new_collateral_value / vault.dinari_minted
            min_required_ratio = self.collateral_assets[asset_symbol].collateral_ratio
            
            if new_collateral_ratio < min_required_ratio:
                raise ValueError(f"Withdrawal would leave vault undercollateralized. Required: {min_required_ratio}, new ratio: {new_collateral_ratio}")
        
        # Execute withdrawal
        vault.collateral_deposits[asset_symbol] = current_deposit - amount
        vault.last_interaction = int(time.time())
        
        # Update total deposited for asset
        self.collateral_assets[asset_symbol].total_deposited -= amount
        
        # Recalculate collateral ratio
        self._update_vault_collateral_ratio(user_address)
        
        self._emit_event("CollateralWithdrawn", {
            "user": user_address,
            "asset": asset_symbol,
            "amount": str(amount),
            "new_collateral_ratio": str(vault.collateral_ratio),
            "timestamp": int(time.time())
        })
        
        return True
    
    # ========== AFRICAN INTEGRATION FEATURES ==========
    
    def mobile_money_deposit(self, user_address: str, gateway_id: str, 
                           local_amount: Decimal, local_currency: str) -> bool:
        """Deposit via mobile money and receive Dinari"""
        if gateway_id not in self.mobile_money_gateways:
            raise ValueError(f"Mobile money gateway {gateway_id} not supported")
        
        gateway = self.mobile_money_gateways[gateway_id]
        if not gateway["active"]:
            raise ValueError(f"Gateway {gateway_id} is not active")
        
        # Convert local currency to USD (simplified - would use real forex rates)
        usd_amount = self._convert_to_usd(local_amount, local_currency)
        
        # Apply gateway fee
        fee = usd_amount * gateway["fee_percentage"]
        net_usd_amount = usd_amount - fee
        
        # Mint Dinari 1:1 with USD (assuming sufficient protocol collateral)
        dinari_amount = net_usd_amount
        
        # Add to user balance
        self.balances[user_address] = self.balance_of(user_address) + dinari_amount
        self.total_supply += dinari_amount
        
        self._emit_event("MobileMoneyDeposit", {
            "user": user_address,
            "gateway": gateway_id,
            "local_amount": str(local_amount),
            "local_currency": local_currency,
            "usd_amount": str(usd_amount),
            "fee": str(fee),
            "dinari_received": str(dinari_amount),
            "timestamp": int(time.time())
        })
        
        return True
    
    def remittance_transfer(self, from_address: str, to_country: str, 
                          recipient_mobile: str, dinari_amount: Decimal) -> str:
        """Send Dinari as remittance to recipient in target country"""
        if dinari_amount <= 0:
            raise ValueError("Remittance amount must be positive")
        
        if self.balance_of(from_address) < dinari_amount:
            raise ValueError("Insufficient Dinari balance for remittance")
        
        # Generate remittance ID
        remittance_id = f"REM_{int(time.time())}_{hash(from_address + recipient_mobile) % 10000}"
        
        # Calculate remittance fee (lower than traditional services)
        fee_percentage = Decimal('0.02')  # 2% - much lower than traditional 8-10%
        fee = dinari_amount * fee_percentage
        net_amount = dinari_amount - fee
        
        # Deduct from sender
        self.balances[from_address] = self.balance_of(from_address) - dinari_amount
        
        # Add to protocol treasury for remittance processing
        treasury_address = "dinari_remittance_treasury"
        self.balances[treasury_address] = self.balance_of(treasury_address) + net_amount
        
        self._emit_event("RemittanceInitiated", {
            "remittance_id": remittance_id,
            "from": from_address,
            "to_country": to_country,
            "recipient_mobile": recipient_mobile,
            "dinari_amount": str(dinari_amount),
            "fee": str(fee),
            "net_amount": str(net_amount),
            "timestamp": int(time.time())
        })
        
        return remittance_id
    
    # ========== HELPER FUNCTIONS ==========
    
    def _calculate_vault_collateral_value(self, user_address: str) -> Decimal:
        """Calculate total USD value of user's collateral"""
        if user_address not in self.user_vaults:
            return Decimal('0')
        
        vault = self.user_vaults[user_address]
        return self._calculate_collateral_value(vault.collateral_deposits)
    
    def _calculate_collateral_value(self, collateral_deposits: Dict[str, Decimal]) -> Decimal:
        """Calculate USD value of collateral deposits"""
        total_value = Decimal('0')
        
        for asset_symbol, amount in collateral_deposits.items():
            if asset_symbol in self.collateral_assets and amount > 0:
                asset_price = self.collateral_assets[asset_symbol].price_usd
                total_value += amount * asset_price
        
        return total_value
    
    def _update_vault_collateral_ratio(self, user_address: str):
        """Update vault's collateral ratio and liquidation status"""
        vault = self.user_vaults[user_address]
        total_collateral_value = self._calculate_vault_collateral_value(user_address)
        
        if vault.dinari_minted > 0:
            vault.collateral_ratio = total_collateral_value / vault.dinari_minted
            
            # Check if vault is liquidatable
            min_liquidation_threshold = Decimal('1.0')
            for asset_symbol, deposit_amount in vault.collateral_deposits.items():
                if deposit_amount > 0:
                    threshold = self.collateral_assets[asset_symbol].liquidation_threshold
                    min_liquidation_threshold = max(min_liquidation_threshold, threshold)
            
            vault.is_liquidatable = vault.collateral_ratio < min_liquidation_threshold
        else:
            vault.collateral_ratio = Decimal('999999999')  # Infinite ratio when no debt
            vault.is_liquidatable = False
    
    def _convert_to_usd(self, local_amount: Decimal, local_currency: str) -> Decimal:
        """Convert local currency to USD (simplified implementation)"""
        # In production, this would use real forex rates from oracles
        exchange_rates = {
            "KES": Decimal('0.0067'),  # Kenyan Shilling
            "NGN": Decimal('0.0012'),  # Nigerian Naira
            "GHS": Decimal('0.084'),   # Ghanaian Cedi
            "UGX": Decimal('0.00027'), # Ugandan Shilling
            "TZS": Decimal('0.00043'), # Tanzanian Shilling
            "ZAR": Decimal('0.054'),   # South African Rand
            "XOF": Decimal('0.0016'),  # West African CFA Franc
            "XAF": Decimal('0.0016'),  # Central African CFA Franc
        }
        
        if local_currency not in exchange_rates:
            raise ValueError(f"Currency {local_currency} not supported")
        
        return local_amount * exchange_rates[local_currency]
    
    def _emit_event(self, event_type: str, event_data: dict):
        """Emit an event for transparency and logging"""
        event = {
            "type": event_type,
            "data": event_data,
            "block_timestamp": int(time.time()),
            "contract_address": "dinari_stablecoin"
        }
        self.events.append(event)
    
    # ========== VIEW FUNCTIONS ==========
    
    def get_vault_info(self, user_address: str) -> dict:
        """Get comprehensive vault information for a user"""
        if user_address not in self.user_vaults:
            return {"error": "No vault found for user"}
        
        vault = self.user_vaults[user_address]
        collateral_value = self._calculate_vault_collateral_value(user_address)
        
        return {
            "user_address": user_address,
            "collateral_deposits": {k: str(v) for k, v in vault.collateral_deposits.items()},
            "total_collateral_value_usd": str(collateral_value),
            "dinari_minted": str(vault.dinari_minted),
            "collateral_ratio": str(vault.collateral_ratio),
            "is_liquidatable": vault.is_liquidatable,
            "last_interaction": vault.last_interaction
        }
    
    def get_protocol_stats(self) -> dict:
        """Get overall protocol statistics"""
        return {
            "total_supply": str(self.total_supply),
            "total_collateral_value": str(self.stability_pool.total_collateral_value),
            "stability_fee": str(self.stability_pool.stability_fee),
            "supported_collateral_assets": list(self.collateral_assets.keys()),
            "mobile_money_gateways": list(self.mobile_money_gateways.keys()),
            "contract_version": self.contract_version,
            "target_price": str(self.target_price)
        }
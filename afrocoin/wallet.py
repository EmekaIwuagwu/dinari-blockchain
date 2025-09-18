#!/usr/bin/env python3
"""
DinariBlockchain Wallet Implementation  
Dinari/wallet.py - Wallet and key management for Dinari
"""

import hashlib
import secrets
import json
import time
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
import logging

# Import blockchain components
from .blockchain import Transaction, DinariBlockchain

@dataclass
class KeyPair:
    """Simple key pair for Dinari addresses"""
    private_key: str
    public_key: str
    address: str
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'KeyPair':
        """Create from dictionary"""
        return cls(**data)

class DinariWallet:
    """Simple wallet for managing Dinari addresses and transactions"""
    
    def __init__(self, wallet_name: str = "default", wallet_dir: str = "wallets"):
        self.wallet_name = wallet_name
        self.wallet_dir = wallet_dir
        self.wallet_file = os.path.join(wallet_dir, f"{wallet_name}.json")
        
        # Wallet data
        self.keys: Dict[str, KeyPair] = {}  # address -> KeyPair
        self.transaction_history: List[Transaction] = []
        self.created_at = time.time()
        self.version = "1.0.0"
        
        # Ensure wallet directory exists
        os.makedirs(wallet_dir, exist_ok=True)
        
        # Load existing wallet or create new
        self._load_or_create_wallet()
        
        # Setup logging
        self.logger = logging.getLogger(f"DinariWallet-{wallet_name}")
        
        self.logger.info(f"Wallet '{wallet_name}' initialized with {len(self.keys)} addresses")
    
    def _load_or_create_wallet(self):
        """Load existing wallet or create new one"""
        if os.path.exists(self.wallet_file):
            try:
                with open(self.wallet_file, 'r') as f:
                    data = json.load(f)
                
                # Load wallet data
                self.created_at = data.get('created_at', time.time())
                self.version = data.get('version', '1.0.0')
                
                # Load key pairs
                for addr, key_data in data.get('keys', {}).items():
                    self.keys[addr] = KeyPair.from_dict(key_data)
                
                # Load transaction history
                self.transaction_history = [
                    Transaction.from_dict(tx_data) 
                    for tx_data in data.get('transaction_history', [])
                ]
                
                self.logger.info(f"Loaded existing wallet from {self.wallet_file}")
                
            except Exception as e:
                self.logger.error(f"Failed to load wallet: {e}")
                # Create new wallet if loading fails
                self._create_new_wallet()
        else:
            self._create_new_wallet()
    
    def _create_new_wallet(self):
        """Create a new wallet"""
        self.logger.info("Creating new wallet")
        
        # Create initial address
        initial_address = self.create_new_address("main")
        
        # Save wallet
        self.save_wallet()
        
        self.logger.info(f"New wallet created with address: {initial_address}")
    
    def create_new_address(self, label: str = None) -> str:
        """Create a new address"""
        # Generate random private key (32 bytes = 256 bits)
        private_key = secrets.token_hex(32)
        
        # Generate public key (simplified - in production use proper elliptic curve)
        public_key = hashlib.sha256(private_key.encode()).hexdigest()
        
        # Generate address (Dinari format: DNMR + first 20 bytes of public key hash)
        public_key_hash = hashlib.sha256(public_key.encode()).hexdigest()
        address = f"DNMR{public_key_hash[:40]}"
        
        # Create key pair
        key_pair = KeyPair(
            private_key=private_key,
            public_key=public_key,
            address=address
        )
        
        # Store in wallet
        self.keys[address] = key_pair
        
        self.logger.info(f"Created new address: {address}")
        
        # Save wallet
        self.save_wallet()
        
        return address
    
    def get_all_addresses(self) -> List[str]:
        """Get all addresses in wallet"""
        return list(self.keys.keys())
    
    def get_balance(self, address: str, blockchain: DinariBlockchain) -> Decimal:
        """Get balance for an address from blockchain"""
        if address not in self.keys:
            return Decimal('0')
        
        return blockchain.get_balance(address)
    
    def get_total_balance(self, blockchain: DinariBlockchain) -> Decimal:
        """Get total balance across all addresses"""
        total = Decimal('0')
        for address in self.keys:
            total += blockchain.get_balance(address)
        return total
    
    def create_transaction(self, from_address: str, to_address: str, 
                         amount: str, fee: str = "0.001", data: str = "") -> Optional[Transaction]:
        """Create a new transaction"""
        
        # Check if we own the from_address
        if from_address not in self.keys:
            self.logger.error(f"Address {from_address} not found in wallet")
            return None
        
        # Create transaction
        transaction = Transaction(
            from_address=from_address,
            to_address=to_address,
            amount=amount,
            fee=fee,
            data=data,
            nonce=int(time.time() * 1000)  # Simple nonce
        )
        
        # Sign transaction (simplified signing)
        private_key = self.keys[from_address].private_key
        transaction.signature = self._sign_transaction(transaction, private_key)
        
        self.logger.info(f"Created transaction: {from_address} → {to_address} ({amount} DNMR)")
        
        return transaction
    
    def _sign_transaction(self, transaction: Transaction, private_key: str) -> str:
        """Sign a transaction (simplified signature)"""
        # In production, use proper digital signatures (ECDSA, EdDSA, etc.)
        tx_hash = transaction.calculate_hash()
        signature_data = f"{tx_hash}{private_key}"
        signature = hashlib.sha256(signature_data.encode()).hexdigest()
        
        return f"DNMR_sig_{signature[:32]}"
    
    def send_transaction(self, from_address: str, to_address: str, amount: str, 
                        blockchain: DinariBlockchain, fee: str = "0.001") -> bool:
        """Create and send transaction to blockchain"""
        
        # Check balance
        balance = self.get_balance(from_address, blockchain)
        total_needed = Decimal(amount) + Decimal(fee)
        
        if balance < total_needed:
            self.logger.error(f"Insufficient balance: {balance} < {total_needed}")
            return False
        
        # Create transaction
        transaction = self.create_transaction(from_address, to_address, amount, fee)
        
        if not transaction:
            return False
        
        # Submit to blockchain
        success = blockchain.add_transaction(transaction)
        
        if success:
            # Add to transaction history
            self.transaction_history.append(transaction)
            self.save_wallet()
            
            self.logger.info(f"Transaction sent successfully: {transaction.calculate_hash()[:8]}")
        
        return success
    
    def get_transaction_history(self, address: str = None) -> List[Transaction]:
        """Get transaction history for address or all addresses"""
        if address:
            return [
                tx for tx in self.transaction_history 
                if tx.from_address == address or tx.to_address == address
            ]
        else:
            return self.transaction_history.copy()
    
    def update_transaction_history(self, blockchain: DinariBlockchain):
        """Update transaction history from blockchain"""
        all_transactions = []
        
        # Get transactions for all our addresses
        for address in self.keys:
            address_transactions = blockchain.get_transaction_history(address)
            all_transactions.extend(address_transactions)
        
        # Remove duplicates and sort by timestamp
        unique_transactions = []
        seen_hashes = set()
        
        for tx in all_transactions:
            tx_hash = tx.calculate_hash()
            if tx_hash not in seen_hashes:
                seen_hashes.add(tx_hash)
                unique_transactions.append(tx)
        
        # Sort by timestamp
        unique_transactions.sort(key=lambda x: x.timestamp)
        
        self.transaction_history = unique_transactions
        self.save_wallet()
        
        self.logger.info(f"Updated transaction history: {len(unique_transactions)} transactions")
    
    def export_address(self, address: str) -> Optional[Dict]:
        """Export address and private key"""
        if address not in self.keys:
            return None
        
        return {
            "address": address,
            "private_key": self.keys[address].private_key,
            "public_key": self.keys[address].public_key,
            "created_at": self.keys[address].created_at
        }
    
    def import_address(self, private_key: str, label: str = None) -> Optional[str]:
        """Import an address from private key"""
        try:
            # Generate public key and address
            public_key = hashlib.sha256(private_key.encode()).hexdigest()
            public_key_hash = hashlib.sha256(public_key.encode()).hexdigest()
            address = f"DNMR{public_key_hash[:40]}"
            
            # Check if already exists
            if address in self.keys:
                self.logger.warning(f"Address {address} already exists in wallet")
                return address
            
            # Create key pair
            key_pair = KeyPair(
                private_key=private_key,
                public_key=public_key,
                address=address
            )
            
            # Store in wallet
            self.keys[address] = key_pair
            self.save_wallet()
            
            self.logger.info(f"Imported address: {address}")
            return address
            
        except Exception as e:
            self.logger.error(f"Failed to import address: {e}")
            return None
    
    def get_wallet_info(self) -> Dict:
        """Get wallet information"""
        return {
            "name": self.wallet_name,
            "version": self.version,
            "created_at": self.created_at,
            "total_addresses": len(self.keys),
            "addresses": list(self.keys.keys()),
            "total_transactions": len(self.transaction_history)
        }
    
    def save_wallet(self):
        """Save wallet to file"""
        try:
            wallet_data = {
                "name": self.wallet_name,
                "version": self.version,
                "created_at": self.created_at,
                "keys": {addr: key_pair.to_dict() for addr, key_pair in self.keys.items()},
                "transaction_history": [tx.to_dict() for tx in self.transaction_history]
            }
            
            with open(self.wallet_file, 'w') as f:
                json.dump(wallet_data, f, indent=2)
            
            self.logger.debug(f"Wallet saved to {self.wallet_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save wallet: {e}")
    
    def backup_wallet(self, backup_path: str):
        """Create wallet backup"""
        try:
            wallet_data = {
                "name": self.wallet_name,
                "version": self.version,
                "created_at": self.created_at,
                "keys": {addr: key_pair.to_dict() for addr, key_pair in self.keys.items()},
                "transaction_history": [tx.to_dict() for tx in self.transaction_history],
                "backup_created_at": time.time()
            }
            
            with open(backup_path, 'w') as f:
                json.dump(wallet_data, f, indent=2)
            
            self.logger.info(f"Wallet backup created: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
    
    def restore_from_backup(self, backup_path: str):
        """Restore wallet from backup"""
        try:
            with open(backup_path, 'r') as f:
                data = json.load(f)
            
            # Load wallet data
            self.created_at = data.get('created_at', time.time())
            self.version = data.get('version', '1.0.0')
            
            # Load key pairs
            self.keys = {}
            for addr, key_data in data.get('keys', {}).items():
                self.keys[addr] = KeyPair.from_dict(key_data)
            
            # Load transaction history
            self.transaction_history = [
                Transaction.from_dict(tx_data) 
                for tx_data in data.get('transaction_history', [])
            ]
            
            # Save restored wallet
            self.save_wallet()
            
            self.logger.info(f"Wallet restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            return False
    
    def print_wallet_summary(self, blockchain: DinariBlockchain = None):
        """Print human-readable wallet summary"""
        print("\n" + "="*60)
        print(f"Dinari WALLET SUMMARY - {self.wallet_name}")
        print("="*60)
        
        info = self.get_wallet_info()
        print(f"📅 Created: {time.ctime(info['created_at'])}")
        print(f"🏷️  Version: {info['version']}")
        print(f"📍 Addresses: {info['total_addresses']}")
        print(f"📊 Transactions: {info['total_transactions']}")
        
        if blockchain:
            total_balance = self.get_total_balance(blockchain)
            print(f"💰 Total Balance: {total_balance} DNMR")
        
        print(f"\n📍 Addresses:")
        for i, address in enumerate(self.keys.keys(), 1):
            balance = self.get_balance(address, blockchain) if blockchain else "N/A"
            print(f"   {i}. {address[:20]}...{address[-10:]}")
            if blockchain:
                print(f"      Balance: {balance} DNMR")
        
        if self.transaction_history:
            print(f"\n📊 Recent Transactions (last 5):")
            recent_txs = sorted(self.transaction_history, key=lambda x: x.timestamp, reverse=True)[:5]
            
            for tx in recent_txs:
                tx_type = "Sent" if tx.from_address in self.keys else "Received"
                other_address = tx.to_address if tx_type == "Sent" else tx.from_address
                print(f"   🔸 {tx_type}: {tx.amount} DNMR")
                print(f"      {'To' if tx_type == 'Sent' else 'From'}: {other_address[:20]}...{other_address[-10:]}")
                print(f"      Date: {time.ctime(tx.timestamp)}")
        
        print("="*60)

# Wallet CLI helper functions
def create_wallet(wallet_name: str, wallet_dir: str = "wallets") -> DinariWallet:
    """Create a new wallet"""
    wallet = DinariWallet(wallet_name, wallet_dir)
    print(f"✅ Wallet '{wallet_name}' created successfully!")
    return wallet

def load_wallet(wallet_name: str, wallet_dir: str = "wallets") -> Optional[DinariWallet]:
    """Load existing wallet"""
    wallet_file = os.path.join(wallet_dir, f"{wallet_name}.json")
    
    if not os.path.exists(wallet_file):
        print(f"❌ Wallet '{wallet_name}' not found")
        return None
    
    wallet = DinariWallet(wallet_name, wallet_dir)
    print(f"✅ Wallet '{wallet_name}' loaded successfully!")
    return wallet

# Example usage
if __name__ == "__main__":
    import argparse
    
    # Simple CLI for wallet operations
    parser = argparse.ArgumentParser(description="DinariBlockchain Wallet")
    parser.add_argument("--wallet", default="default", help="Wallet name")
    parser.add_argument("--wallet-dir", default="wallets", help="Wallet directory")
    
    subparsers = parser.add_subparsers(dest='action', help='Wallet actions')
    
    # Create wallet
    create_parser = subparsers.add_parser('create', help='Create new wallet')
    
    # New address
    addr_parser = subparsers.add_parser('address', help='Create new address')
    
    # Show info
    info_parser = subparsers.add_parser('info', help='Show wallet info')
    
    # Backup
    backup_parser = subparsers.add_parser('backup', help='Backup wallet')
    backup_parser.add_argument('backup_file', help='Backup file path')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        wallet = create_wallet(args.wallet, args.wallet_dir)
        wallet.print_wallet_summary()
    
    elif args.action == 'address':
        wallet = load_wallet(args.wallet, args.wallet_dir)
        if wallet:
            new_addr = wallet.create_new_address()
            print(f"✅ New address created: {new_addr}")
    
    elif args.action == 'info':
        wallet = load_wallet(args.wallet, args.wallet_dir)
        if wallet:
            wallet.print_wallet_summary()
    
    elif args.action == 'backup':
        wallet = load_wallet(args.wallet, args.wallet_dir)
        if wallet:
            success = wallet.backup_wallet(args.backup_file)
            if success:
                print(f"✅ Wallet backed up to {args.backup_file}")
    
    else:
        parser.print_help()
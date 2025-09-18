"""
DinariLevelDB Storage Implementation
===================================
LevelDB-based storage for DinariBlockchain
"""

import json
import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal

try:
    import plyvel
    LEVELDB_AVAILABLE = True
except ImportError:
    LEVELDB_AVAILABLE = False
    plyvel = None

class DinariLevelDB:
    """
    LevelDB storage implementation for DinariBlockchain
    Falls back to file-based storage if LevelDB is not available
    """
    
    def __init__(self, db_path: str = "./dinari_data"):
        self.db_path = db_path
        self.logger = logging.getLogger("Dinari.database")
        
        if LEVELDB_AVAILABLE:
            try:
                self.db = plyvel.DB(db_path, create_if_missing=True)
                self.storage_type = "leveldb"
                self.logger.info(f"LevelDB storage initialized at {db_path}")
            except Exception as e:
                self.logger.warning(f"LevelDB failed, falling back to file storage: {e}")
                self._init_file_storage()
        else:
            self.logger.warning("LevelDB not available, using file storage")
            self._init_file_storage()
    
    def _init_file_storage(self):
        """Initialize file-based storage as fallback"""
        import os
        self.storage_type = "file"
        self.data = {}
        
        # Create data directory
        os.makedirs(self.db_path, exist_ok=True)
        
        # Load existing data
        self.data_file = os.path.join(self.db_path, "blockchain_data.json")
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
                self.logger.info(f"Loaded existing data from {self.data_file}")
            except Exception as e:
                self.logger.error(f"Failed to load data file: {e}")
                self.data = {}
    
    def _save_file_data(self):
        """Save data to file (for file storage mode)"""
        if self.storage_type == "file":
            try:
                with open(self.data_file, 'w') as f:
                    json.dump(self.data, f, indent=2)
            except Exception as e:
                self.logger.error(f"Failed to save data file: {e}")
    
    def put(self, key: str, value: Any) -> None:
        """Store a key-value pair"""
        try:
            serialized_value = json.dumps(value, default=str)
            
            if self.storage_type == "leveldb":
                self.db.put(key.encode(), serialized_value.encode())
            else:
                self.data[key] = value
                self._save_file_data()
                
        except Exception as e:
            self.logger.error(f"Failed to put key {key}: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key"""
        try:
            if self.storage_type == "leveldb":
                raw_value = self.db.get(key.encode())
                if raw_value is None:
                    return None
                return json.loads(raw_value.decode())
            else:
                return self.data.get(key)
                
        except Exception as e:
            self.logger.error(f"Failed to get key {key}: {e}")
            return None
    
    def delete(self, key: str) -> None:
        """Delete a key-value pair"""
        try:
            if self.storage_type == "leveldb":
                self.db.delete(key.encode())
            else:
                if key in self.data:
                    del self.data[key]
                    self._save_file_data()
                    
        except Exception as e:
            self.logger.error(f"Failed to delete key {key}: {e}")
    
    def store_block(self, block_hash: str, block_data: Dict[str, Any]) -> None:
        """Store a block"""
        self.put(f"block:{block_hash}", block_data)
        self.logger.debug(f"Block {block_hash} stored")
    
    def get_block(self, block_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve a block by hash"""
        return self.get(f"block:{block_hash}")
    
    def store_transaction(self, tx_hash: str, tx_data: Dict[str, Any]) -> None:
        """Store a transaction"""
        self.put(f"tx:{tx_hash}", tx_data)
        self.logger.debug(f"Transaction {tx_hash} stored")
    
    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve a transaction by hash"""
        return self.get(f"tx:{tx_hash}")
    
    def store_chain_state(self, state: Dict[str, Any]) -> None:
        """Store blockchain state"""
        self.put("chain_state", state)
    
    def get_chain_state(self) -> Optional[Dict[str, Any]]:
        """Retrieve blockchain state"""
        return self.get("chain_state")
    
    def store_account_state(self, address: str, state: Dict[str, Any]) -> None:
        """Store account state"""
        self.put(f"account:{address}", state)
    
    def get_account_state(self, address: str) -> Optional[Dict[str, Any]]:
        """Retrieve account state"""
        return self.get(f"account:{address}")
    
    def list_blocks(self, limit: int = 100) -> List[str]:
        """List block hashes (limited functionality in file mode)"""
        try:
            if self.storage_type == "leveldb":
                block_hashes = []
                for key, _ in self.db.iterator(prefix=b"block:"):
                    block_hash = key.decode().replace("block:", "")
                    block_hashes.append(block_hash)
                    if len(block_hashes) >= limit:
                        break
                return block_hashes
            else:
                # File mode - list blocks from data
                block_hashes = []
                for key in self.data.keys():
                    if key.startswith("block:"):
                        block_hash = key.replace("block:", "")
                        block_hashes.append(block_hash)
                        if len(block_hashes) >= limit:
                            break
                return block_hashes
                
        except Exception as e:
            self.logger.error(f"Failed to list blocks: {e}")
            return []
    
    def list_transactions(self, limit: int = 100) -> List[str]:
        """List transaction hashes (limited functionality in file mode)"""
        try:
            if self.storage_type == "leveldb":
                tx_hashes = []
                for key, _ in self.db.iterator(prefix=b"tx:"):
                    tx_hash = key.decode().replace("tx:", "")
                    tx_hashes.append(tx_hash)
                    if len(tx_hashes) >= limit:
                        break
                return tx_hashes
            else:
                # File mode - list transactions from data
                tx_hashes = []
                for key in self.data.keys():
                    if key.startswith("tx:"):
                        tx_hash = key.replace("tx:", "")
                        tx_hashes.append(tx_hash)
                        if len(tx_hashes) >= limit:
                            break
                return tx_hashes
                
        except Exception as e:
            self.logger.error(f"Failed to list transactions: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            if self.storage_type == "leveldb":
                # Count items by prefix
                block_count = sum(1 for _ in self.db.iterator(prefix=b"block:"))
                tx_count = sum(1 for _ in self.db.iterator(prefix=b"tx:"))
                account_count = sum(1 for _ in self.db.iterator(prefix=b"account:"))
                
                return {
                    "storage_type": "leveldb",
                    "blocks": block_count,
                    "transactions": tx_count,
                    "accounts": account_count,
                    "total_keys": block_count + tx_count + account_count
                }
            else:
                # File mode statistics
                blocks = sum(1 for k in self.data.keys() if k.startswith("block:"))
                txs = sum(1 for k in self.data.keys() if k.startswith("tx:"))
                accounts = sum(1 for k in self.data.keys() if k.startswith("account:"))
                
                return {
                    "storage_type": "file",
                    "blocks": blocks,
                    "transactions": txs,
                    "accounts": accounts,
                    "total_keys": len(self.data)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
    
    def compact(self) -> None:
        """Compact database (LevelDB only)"""
        if self.storage_type == "leveldb":
            try:
                self.db.compact_range()
                self.logger.info("Database compacted")
            except Exception as e:
                self.logger.error(f"Database compaction failed: {e}")
        else:
            self.logger.info("File storage doesn't require compaction")
    
    def backup(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        try:
            import shutil
            import os
            
            if self.storage_type == "leveldb":
                # For LevelDB, copy the entire directory
                if os.path.exists(backup_path):
                    shutil.rmtree(backup_path)
                shutil.copytree(self.db_path, backup_path)
            else:
                # For file storage, copy the JSON file
                os.makedirs(backup_path, exist_ok=True)
                shutil.copy2(self.data_file, os.path.join(backup_path, "blockchain_data.json"))
            
            self.logger.info(f"Database backed up to {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False
    
    def close(self) -> None:
        """Close database connection"""
        try:
            if self.storage_type == "leveldb" and hasattr(self, 'db'):
                self.db.close()
                self.logger.info("LevelDB connection closed")
            elif self.storage_type == "file":
                self._save_file_data()
                self.logger.info("File storage saved and closed")
                
        except Exception as e:
            self.logger.error(f"Failed to close database: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
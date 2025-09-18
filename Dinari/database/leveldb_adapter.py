"""
LevelDB Database Adapter for Dinari Blockchain
File: dinari/database/leveldb_adapter.py
"""

import json
import plyvel
import os
from typing import Optional, Dict, List, Any
import threading
from contextlib import contextmanager

class DinariLevelDB:
    """LevelDB adapter for Dinari blockchain storage"""
    
    def __init__(self, db_path: str = "./dinari_data"):
        self.db_path = db_path
        self.db = None
        self._lock = threading.RLock()
        self._open_db()
        
    def _open_db(self):
        """Open LevelDB database"""
        try:
            os.makedirs(self.db_path, exist_ok=True)
            self.db = plyvel.DB(self.db_path, create_if_missing=True)
            print(f"✅ LevelDB opened: {self.db_path}")
        except Exception as e:
            print(f"❌ LevelDB error: {e}")
            raise

    def close(self):
        """Close database"""
        if self.db:
            self.db.close()
            print("✅ LevelDB closed")

    # ============= BASIC OPERATIONS =============
    
    def put(self, key: str, value: Any) -> bool:
        """Store key-value pair"""
        try:
            with self._lock:
                data = json.dumps(value).encode('utf-8')
                self.db.put(key.encode('utf-8'), data)
                return True
        except Exception as e:
            print(f"❌ Put failed {key}: {e}")
            return False

    def get(self, key: str, default=None) -> Any:
        """Get value by key"""
        try:
            with self._lock:
                raw = self.db.get(key.encode('utf-8'))
                if raw is None:
                    return default
                return json.loads(raw.decode('utf-8'))
        except Exception as e:
            print(f"❌ Get failed {key}: {e}")
            return default

    def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            with self._lock:
                self.db.delete(key.encode('utf-8'))
                return True
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return self.get(key) is not None

    # ============= BLOCKCHAIN SPECIFIC =============
    
    def store_block(self, block_hash: str, block_data: dict) -> bool:
        """Store blockchain block"""
        return self.put(f"block:{block_hash}", block_data)

    def get_block(self, block_hash: str) -> Optional[dict]:
        """Get blockchain block"""
        return self.get(f"block:{block_hash}")

    def store_transaction(self, tx_hash: str, tx_data: dict) -> bool:
        """Store transaction"""
        return self.put(f"tx:{tx_hash}", tx_data)

    def get_transaction(self, tx_hash: str) -> Optional[dict]:
        """Get transaction"""
        return self.get(f"tx:{tx_hash}")

    def store_chain_state(self, state_data: dict) -> bool:
        """Store blockchain state"""
        return self.put("chain:state", state_data)

    def get_chain_state(self) -> Optional[dict]:
        """Get blockchain state"""
        return self.get("chain:state")

    def store_wallet(self, address: str, wallet_data: dict) -> bool:
        """Store wallet data"""
        return self.put(f"wallet:{address}", wallet_data)

    def get_wallet(self, address: str) -> Optional[dict]:
        """Get wallet data"""
        return self.get(f"wallet:{address}")

    # ============= BATCH OPERATIONS =============
    
    @contextmanager
    def batch_write(self):
        """Batch write context manager"""
        with self._lock:
            batch = self.db.write_batch()
            try:
                yield batch
                batch.write()
            except Exception as e:
                print(f"❌ Batch failed: {e}")
                raise

    def get_all_blocks(self) -> List[dict]:
        """Get all blocks (for small chains only)"""
        blocks = []
        try:
            with self.db.iterator(prefix=b'block:') as it:
                for key, value in it:
                    blocks.append(json.loads(value.decode('utf-8')))
        except Exception as e:
            print(f"❌ Get all blocks failed: {e}")
        return blocks
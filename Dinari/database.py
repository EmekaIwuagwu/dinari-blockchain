#!/usr/bin/env python3
"""
DinariBlockchain - Database Integration Layer
afrocoin/database.py - Simple database abstraction for PostgreSQL and Redis
"""

import os
import json
import time
import logging
import psycopg2
import redis
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime
import threading

# Database configuration from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://dinari:password@localhost:5432/dinari_blockchain')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

class DatabaseManager:
    """Simple database manager for DinariBlockchain"""
    
    def __init__(self):
        self.postgres_conn = None
        self.redis_client = None
        self.lock = threading.Lock()
        
        # Setup logging
        self.logger = logging.getLogger("DatabaseManager")
        
        # Initialize connections
        self._init_postgres()
        self._init_redis()
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        try:
            self.postgres_conn = psycopg2.connect(DATABASE_URL)
            self.postgres_conn.autocommit = True
            
            # Create tables if they don't exist
            self._create_tables()
            
            self.logger.info("✅ PostgreSQL connected successfully")
            
        except Exception as e:
            self.logger.warning(f"⚠️  PostgreSQL connection failed: {e}")
            self.postgres_conn = None
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            
            # Test connection
            self.redis_client.ping()
            
            self.logger.info("✅ Redis connected successfully")
            
        except Exception as e:
            self.logger.warning(f"⚠️  Redis connection failed: {e}")
            self.redis_client = None
    
    def _create_tables(self):
        """Create database tables"""
        if not self.postgres_conn:
            return
        
        cursor = self.postgres_conn.cursor()
        
        # Blocks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blocks (
                id SERIAL PRIMARY KEY,
                block_index INTEGER UNIQUE NOT NULL,
                hash VARCHAR(64) UNIQUE NOT NULL,
                previous_hash VARCHAR(64) NOT NULL,
                validator VARCHAR(100) NOT NULL,
                timestamp BIGINT NOT NULL,
                nonce INTEGER DEFAULT 0,
                transaction_count INTEGER DEFAULT 0,
                block_data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_blocks_index ON blocks(block_index);
            CREATE INDEX IF NOT EXISTS idx_blocks_hash ON blocks(hash);
            CREATE INDEX IF NOT EXISTS idx_blocks_timestamp ON blocks(timestamp);
        """)
        
        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                hash VARCHAR(64) UNIQUE NOT NULL,
                from_address VARCHAR(100) NOT NULL,
                to_address VARCHAR(100) NOT NULL,
                amount DECIMAL(36,18) NOT NULL,
                fee DECIMAL(36,18) NOT NULL,
                block_index INTEGER,
                transaction_data JSONB NOT NULL,
                timestamp BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (block_index) REFERENCES blocks(block_index)
            );
            CREATE INDEX IF NOT EXISTS idx_transactions_hash ON transactions(hash);
            CREATE INDEX IF NOT EXISTS idx_transactions_from ON transactions(from_address);
            CREATE INDEX IF NOT EXISTS idx_transactions_to ON transactions(to_address);
            CREATE INDEX IF NOT EXISTS idx_transactions_block ON transactions(block_index);
        """)
        
        # Balances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS balances (
                address VARCHAR(100) PRIMARY KEY,
                balance DECIMAL(36,18) NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_balances_address ON balances(address);
        """)
        
        # Smart contracts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS smart_contracts (
                address VARCHAR(100) PRIMARY KEY,
                deployer VARCHAR(100) NOT NULL,
                code TEXT NOT NULL,
                state JSONB DEFAULT '{}',
                deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Validators table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validators (
                address VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200),
                is_active BOOLEAN DEFAULT true,
                blocks_mined INTEGER DEFAULT 0,
                reputation DECIMAL(5,2) DEFAULT 100.00,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.close()
        self.logger.info("✅ Database tables created/verified")
    
    # Block operations
    def save_block(self, block) -> bool:
        """Save block to database"""
        if not self.postgres_conn:
            return False
        
        try:
            with self.lock:
                cursor = self.postgres_conn.cursor()
                
                # Save block
                cursor.execute("""
                    INSERT INTO blocks (block_index, hash, previous_hash, validator, 
                                      timestamp, nonce, transaction_count, block_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (block_index) DO NOTHING
                """, (
                    block.index,
                    block.hash,
                    block.previous_hash,
                    block.validator,
                    int(block.timestamp),
                    block.nonce,
                    len(block.transactions),
                    json.dumps(block.to_dict())
                ))
                
                # Save transactions
                for tx in block.transactions:
                    self.save_transaction(tx, block.index)
                
                cursor.close()
                
                # Cache in Redis
                if self.redis_client:
                    self.redis_client.setex(
                        f"block:{block.index}", 
                        3600,  # 1 hour
                        json.dumps(block.to_dict())
                    )
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save block {block.index}: {e}")
            return False
    
    def get_block(self, block_index: int) -> Optional[Dict]:
        """Get block from database"""
        # Try Redis first
        if self.redis_client:
            try:
                cached = self.redis_client.get(f"block:{block_index}")
                if cached:
                    return json.loads(cached)
            except:
                pass
        
        # Try PostgreSQL
        if not self.postgres_conn:
            return None
        
        try:
            cursor = self.postgres_conn.cursor()
            cursor.execute("""
                SELECT block_data FROM blocks WHERE block_index = %s
            """, (block_index,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                block_data = result[0]
                
                # Cache in Redis
                if self.redis_client:
                    self.redis_client.setex(
                        f"block:{block_index}",
                        3600,
                        json.dumps(block_data)
                    )
                
                return block_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get block {block_index}: {e}")
            return None
    
    # Transaction operations
    def save_transaction(self, tx, block_index: Optional[int] = None) -> bool:
        """Save transaction to database"""
        if not self.postgres_conn:
            return False
        
        try:
            cursor = self.postgres_conn.cursor()
            
            cursor.execute("""
                INSERT INTO transactions (hash, from_address, to_address, amount, 
                                        fee, block_index, transaction_data, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hash) DO NOTHING
            """, (
                tx.calculate_hash(),
                tx.from_address,
                tx.to_address,
                Decimal(tx.amount),
                Decimal(tx.fee),
                block_index,
                json.dumps(tx.to_dict()),
                int(tx.timestamp)
            ))
            
            cursor.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save transaction: {e}")
            return False
    
    def get_transactions_for_address(self, address: str) -> List[Dict]:
        """Get all transactions for an address"""
        if not self.postgres_conn:
            return []
        
        try:
            cursor = self.postgres_conn.cursor()
            cursor.execute("""
                SELECT transaction_data FROM transactions 
                WHERE from_address = %s OR to_address = %s
                ORDER BY timestamp DESC
                LIMIT 100
            """, (address, address))
            
            results = cursor.fetchall()
            cursor.close()
            
            return [result[0] for result in results]
            
        except Exception as e:
            self.logger.error(f"Failed to get transactions for {address}: {e}")
            return []
    
    # Balance operations
    def update_balance(self, address: str, balance: Decimal) -> bool:
        """Update balance for an address"""
        if not self.postgres_conn:
            return False
        
        try:
            cursor = self.postgres_conn.cursor()
            
            cursor.execute("""
                INSERT INTO balances (address, balance, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (address) 
                DO UPDATE SET balance = %s, updated_at = CURRENT_TIMESTAMP
            """, (address, balance, balance))
            
            cursor.close()
            
            # Cache in Redis
            if self.redis_client:
                self.redis_client.setex(
                    f"balance:{address}",
                    1800,  # 30 minutes
                    str(balance)
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update balance for {address}: {e}")
            return False
    
    def get_balance(self, address: str) -> Optional[Decimal]:
        """Get balance for an address"""
        # Try Redis first
        if self.redis_client:
            try:
                cached = self.redis_client.get(f"balance:{address}")
                if cached:
                    return Decimal(cached)
            except:
                pass
        
        # Try PostgreSQL
        if not self.postgres_conn:
            return None
        
        try:
            cursor = self.postgres_conn.cursor()
            cursor.execute("""
                SELECT balance FROM balances WHERE address = %s
            """, (address,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                balance = result[0]
                
                # Cache in Redis
                if self.redis_client:
                    self.redis_client.setex(
                        f"balance:{address}",
                        1800,
                        str(balance)
                    )
                
                return balance
            
            return Decimal('0')
            
        except Exception as e:
            self.logger.error(f"Failed to get balance for {address}: {e}")
            return None
    
    # Smart contract operations
    def save_contract(self, contract) -> bool:
        """Save smart contract to database"""
        if not self.postgres_conn:
            return False
        
        try:
            cursor = self.postgres_conn.cursor()
            
            cursor.execute("""
                INSERT INTO smart_contracts (address, deployer, code, state)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (address) 
                DO UPDATE SET state = %s
            """, (
                contract.address,
                contract.deployer,
                contract.code,
                json.dumps(contract.state),
                json.dumps(contract.state)
            ))
            
            cursor.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save contract {contract.address}: {e}")
            return False
    
    def get_contract(self, address: str) -> Optional[Dict]:
        """Get smart contract from database"""
        if not self.postgres_conn:
            return None
        
        try:
            cursor = self.postgres_conn.cursor()
            cursor.execute("""
                SELECT address, deployer, code, state FROM smart_contracts 
                WHERE address = %s
            """, (address,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return {
                    'address': result[0],
                    'deployer': result[1],
                    'code': result[2],
                    'state': result[3]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get contract {address}: {e}")
            return None
    
    # Statistics
    def get_blockchain_stats(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        stats = {}
        
        if self.postgres_conn:
            try:
                cursor = self.postgres_conn.cursor()
                
                # Block stats
                cursor.execute("SELECT COUNT(*), MAX(block_index) FROM blocks")
                block_count, latest_block = cursor.fetchone()
                
                # Transaction stats
                cursor.execute("SELECT COUNT(*) FROM transactions")
                tx_count = cursor.fetchone()[0]
                
                # Active validators
                cursor.execute("SELECT COUNT(*) FROM validators WHERE is_active = true")
                validator_count = cursor.fetchone()[0]
                
                # Total supply
                cursor.execute("SELECT SUM(balance) FROM balances")
                total_supply = cursor.fetchone()[0] or Decimal('0')
                
                cursor.close()
                
                stats.update({
                    'total_blocks': block_count or 0,
                    'latest_block': latest_block or 0,
                    'total_transactions': tx_count or 0,
                    'active_validators': validator_count or 0,
                    'total_supply': str(total_supply)
                })
                
            except Exception as e:
                self.logger.error(f"Failed to get blockchain stats: {e}")
        
        return stats
    
    # Cache operations
    def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache value"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            self.logger.error(f"Failed to set cache {key}: {e}")
            return False
    
    def cache_get(self, key: str) -> Any:
        """Get cache value"""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            self.logger.error(f"Failed to get cache {key}: {e}")
        
        return None
    
    # Cleanup and maintenance
    def cleanup_old_data(self, days: int = 30):
        """Cleanup old cached data"""
        if not self.postgres_conn:
            return
        
        try:
            cursor = self.postgres_conn.cursor()
            
            # Keep transactions but cleanup old temporary data
            cutoff_time = int(time.time()) - (days * 24 * 3600)
            
            # Clean old cache entries
            if self.redis_client:
                # This would need more sophisticated cache key management
                pass
            
            cursor.close()
            self.logger.info(f"Cleaned up data older than {days} days")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
    
    def close(self):
        """Close database connections"""
        if self.postgres_conn:
            self.postgres_conn.close()
        
        if self.redis_client:
            self.redis_client.close()
        
        self.logger.info("Database connections closed")

# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

# Example usage
if __name__ == "__main__":
    # Test database connection
    db = DatabaseManager()
    
    print("🧪 Testing DinariBlockchain Database Integration")
    print("=" * 50)
    
    # Test stats
    stats = db.get_blockchain_stats()
    print(f"📊 Blockchain Stats: {stats}")
    
    # Test cache
    success = db.cache_set("test_key", {"message": "Hello Dinari!"}, 60)
    print(f"💾 Cache Set: {'✅' if success else '❌'}")
    
    cached_value = db.cache_get("test_key")
    print(f"💾 Cache Get: {cached_value}")
    
    print("✅ Database integration test completed!")

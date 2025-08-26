import copy
import time
import threading
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json
import os

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Transaction.MultiTransactions import MultiTransactions
from EZ_Transaction.SingleTransaction import Transaction
from EZ_Tool_Box.Hash import sha256_hash


@dataclass
class ValidationResult:
    """Validation result dataclass"""
    is_valid: bool
    error_message: str = ""
    sender_match: bool = False
    signature_valid: bool = False
    structural_valid: bool = False
    duplicates_found: List[str] = None
    
    def __post_init__(self):
        if self.duplicates_found is None:
            self.duplicates_found = []

class MultiTxnsPool:
    """MultiTransactions pool with validation and database storage"""

    def __init__(self, db_path: str = "transaction_pool.db"):
        self.pool: List[MultiTransactions] = []
        self.sender_index: Dict[str, List[int]] = {}  # sender_id -> indices in pool
        self.digest_index: Dict[str, int] = {}  # digest -> index in pool
        self.db_path = db_path
        self.lock = threading.RLock()
        self.stats = {
            'total_received': 0,
            'valid_received': 0,
            'invalid_received': 0,
            'duplicates': 0
        }
        
        # Initialize database
        self._init_database()
        
        # Start periodic cleanup
        self._start_cleanup_thread()
    
    def _init_database(self):
        """Initialize SQLite database for transaction pool persistence"""
        import sqlite3
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS multi_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    digest TEXT UNIQUE NOT NULL,
                    sender TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    transactions_blob BLOB NOT NULL,
                    is_valid BOOLEAN DEFAULT TRUE,
                    validation_time TEXT,
                    processed BOOLEAN DEFAULT FALSE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS validation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    digest TEXT NOT NULL,
                    validation_type TEXT NOT NULL,
                    is_valid BOOLEAN NOT NULL,
                    error_message TEXT,
                    validation_time TEXT NOT NULL,
                    FOREIGN KEY (digest) REFERENCES multi_transactions(digest)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sender_id ON multi_transactions(sender_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_digest ON multi_transactions(digest)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON multi_transactions(timestamp)
            ''')
            
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
    
    def _start_cleanup_thread(self):
        """Start background thread for cleaning up old transactions"""
        def cleanup_worker():
            while True:
                time.sleep(3600)  # Run cleanup every hour
                self._cleanup_old_transactions()
        
        thread = threading.Thread(target=cleanup_worker, daemon=True)
        thread.start()
    
    def _cleanup_old_transactions(self, max_age_hours: int = 24):
        """Clean up transactions older than max_age_hours"""
        try:
            import sqlite3
            
            cutoff_time = time.time() - (max_age_hours * 3600)
            cutoff_iso = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(cutoff_time))
            
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get old digests
                cursor.execute('''
                    SELECT digest FROM multi_transactions 
                    WHERE timestamp < ? AND processed = FALSE
                ''', (cutoff_iso,))
                
                old_digests = [row[0] for row in cursor.fetchall()]
                
                # Remove from database
                cursor.execute('''
                    DELETE FROM multi_transactions WHERE timestamp < ? AND processed = FALSE
                ''', (cutoff_iso,))
                
                # Remove from memory
                for digest in old_digests:
                    if digest in self.digest_index:
                        index = self.digest_index[digest]
                        del self.digest_index[digest]
                        
                        # Remove from sender_index
                        multi_txn = self.pool[index]
                        if multi_txn.sender_id in self.sender_index:
                            if index in self.sender_index[multi_txn.sender_id]:
                                self.sender_index[multi_txn.sender_id].remove(index)
                                if not self.sender_index[multi_txn.sender_id]:
                                    del self.sender_index[multi_txn.sender_id]
                        
                        # Remove from pool
                        del self.pool[index]
                        
                        # Rebuild indices
                        self._rebuild_indices()
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            print(f"Cleanup error: {e}")

    def _rebuild_indices(self):
        """Rebuild sender and digest indices after pool modification"""
        self.sender_index.clear()
        self.digest_index.clear()
        
        for i, multi_txn in enumerate(self.pool):
            if multi_txn.sender_id not in self.sender_index:
                self.sender_index[multi_txn.sender_id] = []
            self.sender_index[multi_txn.sender_id].append(i)
            self.digest_index[multi_txn.digest] = i

    def _persist_to_database(self, multi_txn: MultiTransactions, validation_result: ValidationResult):
        """Persist MultiTransactions and validation result to database"""
        try:
            import sqlite3
            
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Insert or replace MultiTransactions
                cursor.execute('''
                    INSERT OR REPLACE INTO multi_transactions 
                    (digest, sender, sender_id, timestamp, signature, transactions_blob, is_valid, validation_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    multi_txn.digest,
                    multi_txn.sender,
                    multi_txn.sender_id,
                    multi_txn.time,
                    multi_txn.signature.hex() if multi_txn.signature else None,
                    multi_txn.encode(),
                    validation_result.is_valid,
                    time.strftime('%Y-%m-%dT%H:%M:%S')
                ))
                
                # Insert validation result
                cursor.execute('''
                    INSERT INTO validation_results 
                    (digest, validation_type, is_valid, error_message, validation_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    multi_txn.digest,
                    'formal_validation',
                    validation_result.is_valid,
                    validation_result.error_message,
                    time.strftime('%Y-%m-%dT%H:%M:%S')
                ))
                
                conn.commit()
                conn.close()
                
        except sqlite3.Error as e:
            print(f"Database persistence error: {e}")

    def validate_multi_transactions(self, multi_txn: MultiTransactions, public_key_pem: bytes = None) -> ValidationResult:
        """
        Perform formal validation of MultiTransactions:
        1) All transactions in the MultiTransactions must come from the same Sender
        2) All transaction signatures must be correct (Sender signature)
        3) Other data structural correctness
        """
        validation_result = ValidationResult(is_valid=True)
        
        try:
            # 1. Check if MultiTransactions is empty
            if not multi_txn.multi_txns:
                validation_result.is_valid = False
                validation_result.error_message = "MultiTransactions cannot be empty"
                validation_result.structural_valid = False
                return validation_result
            
            # 2. Check structural correctness
            if not multi_txn.sender or not multi_txn.sender_id:
                validation_result.is_valid = False
                validation_result.error_message = "Missing sender or sender_id"
                validation_result.structural_valid = False
                return validation_result
            
            # 3. Check if all transactions come from the same sender
            first_sender = None
            for i, txn in enumerate(multi_txn.multi_txns):
                if not isinstance(txn, Transaction):
                    validation_result.is_valid = False
                    validation_result.error_message = f"Transaction {i} is not a valid Transaction object"
                    validation_result.structural_valid = False
                    return validation_result
                
                if first_sender is None:
                    first_sender = txn.sender
                elif txn.sender != first_sender:
                    validation_result.is_valid = False
                    validation_result.error_message = f"Transaction {i} has different sender: expected {first_sender}, got {txn.sender}"
                    validation_result.sender_match = False
                    return validation_result
            
            validation_result.sender_match = True
            
            # 4. Verify MultiTransactions signature
            if multi_txn.signature is None:
                validation_result.is_valid = False
                validation_result.error_message = "MultiTransactions signature is missing"
                validation_result.signature_valid = False
                return validation_result
            
            if multi_txn.digest is None:
                validation_result.is_valid = False
                validation_result.error_message = "MultiTransactions digest is missing"
                validation_result.signature_valid = False
                return validation_result
            
            # Verify signature if public key is provided
            if public_key_pem:
                try:
                    if not multi_txn.check_acc_txn_sig(public_key_pem):
                        validation_result.is_valid = False
                        validation_result.error_message = "MultiTransactions signature verification failed"
                        validation_result.signature_valid = False
                        return validation_result
                except Exception as e:
                    validation_result.is_valid = False
                    validation_result.error_message = f"Signature verification error: {str(e)}"
                    validation_result.signature_valid = False
                    return validation_result
            
            validation_result.signature_valid = True
            
            # 5. Validate individual transaction signatures
            for i, txn in enumerate(multi_txn.multi_txns):
                if txn.signature is None:
                    validation_result.is_valid = False
                    validation_result.error_message = f"Transaction {i} signature is missing"
                    return validation_result
                
                # Verify individual transaction signature if public key is available
                if public_key_pem:
                    try:
                        if not txn.check_txn_sig(public_key_pem):
                            validation_result.is_valid = False
                            validation_result.error_message = f"Transaction {i} signature verification failed"
                            return validation_result
                    except Exception as e:
                        validation_result.is_valid = False
                        validation_result.error_message = f"Transaction {i} signature verification error: {str(e)}"
                        return validation_result
            
            # 6. Check for duplicates in current pool
            if multi_txn.digest in self.digest_index:
                validation_result.is_valid = False
                validation_result.error_message = "Duplicate MultiTransactions found"
                validation_result.duplicates_found.append(multi_txn.digest)
                return validation_result
            
            validation_result.structural_valid = True
            
        except Exception as e:
            validation_result.is_valid = False
            validation_result.error_message = f"Validation error: {str(e)}"
            validation_result.structural_valid = False
        
        return validation_result

    def add_multi_transactions(self, multi_txn: MultiTransactions, public_key_pem: bytes = None) -> Tuple[bool, str]:
        """
        Add MultiTransactions to the pool after validation
        Returns: (success, message)
        """
        try:
            # Validate the MultiTransactions
            validation_result = self.validate_multi_transactions(multi_txn, public_key_pem)
            
            self.stats['total_received'] += 1
            
            if not validation_result.is_valid:
                self.stats['invalid_received'] += 1
                return False, validation_result.error_message
            
            # Check for duplicates
            if multi_txn.digest in self.digest_index:
                self.stats['duplicates'] += 1
                return False, "Duplicate MultiTransactions"
            
            # Add to pool
            with self.lock:
                self.pool.append(multi_txn)
                index = len(self.pool) - 1
                
                # Update indices
                if multi_txn.sender_id not in self.sender_index:
                    self.sender_index[multi_txn.sender_id] = []
                self.sender_index[multi_txn.sender_id].append(index)
                self.digest_index[multi_txn.digest] = index
                
                # Persist to database
                self._persist_to_database(multi_txn, validation_result)
            
            self.stats['valid_received'] += 1
            return True, "MultiTransactions added successfully"
            
        except Exception as e:
            return False, f"Error adding MultiTransactions: {str(e)}"

    def get_multi_transactions_by_sender(self, sender_id: str) -> List[MultiTransactions]:
        """Get all MultiTransactions from a specific sender"""
        with self.lock:
            if sender_id not in self.sender_index:
                return []
            
            return [self.pool[i] for i in self.sender_index[sender_id]]

    def get_multi_transactions_by_digest(self, digest: str) -> Optional[MultiTransactions]:
        """Get MultiTransactions by digest"""
        with self.lock:
            if digest not in self.digest_index:
                return None
            
            return self.pool[self.digest_index[digest]]

    def remove_multi_transactions(self, digest: str) -> bool:
        """Remove MultiTransactions from pool by digest"""
        try:
            with self.lock:
                if digest not in self.digest_index:
                    return False
                
                index = self.digest_index[digest]
                multi_txn = self.pool[index]
                
                # Remove from pool
                del self.pool[index]
                
                # Remove from indices
                del self.digest_index[digest]
                if multi_txn.sender_id in self.sender_index:
                    if index in self.sender_index[multi_txn.sender_id]:
                        self.sender_index[multi_txn.sender_id].remove(index)
                        if not self.sender_index[multi_txn.sender_id]:
                            del self.sender_index[multi_txn.sender_id]
                
                # Rebuild indices
                self._rebuild_indices()
                
                # Mark as processed in database
                try:
                    import sqlite3
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE multi_transactions SET processed = TRUE WHERE digest = ?
                    ''', (digest,))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"Database update error: {e}")
                
                return True
                
        except Exception as e:
            print(f"Error removing MultiTransactions: {e}")
            return False

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self.lock:
            return {
                'total_transactions': len(self.pool),
                'unique_senders': len(self.sender_index),
                'stats': self.stats.copy(),
                'pool_size_bytes': sum(len(multi_txn.encode()) for multi_txn in self.pool)
            }

    def get_all_multi_transactions(self) -> List[MultiTransactions]:
        """Get all MultiTransactions in the pool"""
        with self.lock:
            return self.pool.copy()

    def clear_pool(self):
        """Clear all MultiTransactions from pool"""
        try:
            with self.lock:
                self.pool.clear()
                self.sender_index.clear()
                self.digest_index.clear()
                
                # Clear database
                try:
                    import sqlite3
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM multi_transactions')
                    cursor.execute('DELETE FROM validation_results')
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"Database clear error: {e}")
                
        except Exception as e:
            print(f"Error clearing pool: {e}")

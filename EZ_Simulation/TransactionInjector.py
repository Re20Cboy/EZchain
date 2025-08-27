import threading
import time
import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import os
import sys
import shutil

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Transaction_Pool.TransactionPool import TransactionPool
from EZ_Transaction.MultiTransactions import MultiTransactions
from EZ_Transaction.SingleTransaction import Transaction
from EZ_Value.Value import Value, ValueState


@dataclass
class SimulationConfig:
    """Configuration for transaction injection simulation"""
    num_senders: int = 5
    num_transactions_per_batch: int = 10
    num_batches: int = 20
    injection_interval: float = 0.1  # seconds between injections
    validation_enabled: bool = True
    signature_enabled: bool = True
    duplicate_probability: float = 0.05  # probability of duplicate transactions
    invalid_probability: float = 0.02  # probability of invalid transactions
    preserve_database: bool = True  # whether to preserve the database file after simulation
    database_output_dir: str = "EZ_simulation_data"  # directory to save database files


@dataclass
class SimulationStats:
    """Statistics for simulation results"""
    total_injected: int = 0
    successfully_added: int = 0
    failed_validation: int = 0
    duplicates: int = 0
    injection_errors: int = 0
    start_time: float = 0
    end_time: float = 0
    
    @property
    def success_rate(self) -> float:
        return (self.successfully_added / self.total_injected * 100) if self.total_injected > 0 else 0
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class TransactionInjector:
    """Transaction injector for simulation purposes"""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.transaction_pool = TransactionPool("simulation_pool.db")
        self.sender_keys = self._generate_sender_keys()
        self.injected_transactions = []
        self.stats = SimulationStats()
        self.lock = threading.Lock()
        
        # Create output directory if it doesn't exist
        if self.config.preserve_database and not os.path.exists(self.config.database_output_dir):
            os.makedirs(self.config.database_output_dir)
        
    def _generate_sender_keys(self) -> Dict[str, bytes]:
        """Generate sender addresses and their corresponding public keys"""
        from cryptography.hazmat.primitives import serialization
        
        sender_keys = {}
        
        # Generate test sender addresses and keys
        for i in range(self.config.num_senders):
            sender = f"sender_{i:03d}"
            # Generate a new ECDSA key pair for each sender
            private_key = ec.generate_private_key(ec.SECP256R1())
            public_key = private_key.public_key()
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            sender_keys[sender] = public_key_pem
            
        return sender_keys
    
    def _generate_values(self, num_values: int = 3) -> List[Value]:
        """Generate random values for transactions"""
        values = []
        
        # Generate random begin indices
        for i in range(num_values):
            begin_index = f"0x{random.randint(0x1000, 0xFFFF):04x}"
            value_num = random.randint(1, 100)
            value = Value(begin_index, value_num, ValueState.UNSPENT)
            values.append(value)
            
        return values
    
    def _create_single_transaction(self, sender: str, recipient: str, nonce: int) -> Transaction:
        """Create a single transaction"""
        values = self._generate_values(random.randint(1, 3))
        
        # Create transaction without signature initially
        tx = Transaction.new_transaction(
            sender=sender,
            recipient=recipient,
            value=values,
            nonce=nonce
        )
        
        # Sign the transaction if enabled
        if self.config.signature_enabled and sender in self.sender_keys:
            # For simulation, we'll use a simple signing approach
            # In real implementation, you'd use proper private keys
            pass
            
        return tx
    
    def _create_multi_transactions(self, sender: str, batch_size: int) -> MultiTransactions:
        """Create a MultiTransactions object with multiple transactions"""
        transactions = []
        
        for i in range(batch_size):
            recipient = f"recipient_{random.randint(0, 99):03d}"
            nonce = random.randint(0, 1000000)
            
            try:
                tx = self._create_single_transaction(sender, recipient, nonce)
                transactions.append(tx)
            except Exception as e:
                print(f"Error creating transaction: {e}")
                continue
        
        # Create MultiTransactions
        multi_txn = MultiTransactions(sender=sender, multi_txns=transactions)
        
        # Set digest and sign if enabled
        if self.config.signature_enabled:
            multi_txn.set_digest()
            # In real implementation, you'd sign with private key here
            # For simulation, we'll skip actual signing
            
        return multi_txn
    
    def _create_invalid_multi_transactions(self, sender: str) -> MultiTransactions:
        """Create an invalid MultiTransactions for testing"""
        # Create transactions with different senders (invalid)
        transactions = []
        for i in range(2):
            if i == 0:
                tx_sender = sender
            else:
                tx_sender = f"different_sender_{i}"
                
            recipient = f"recipient_{random.randint(0, 99):03d}"
            values = self._generate_values(1)
            
            tx = Transaction.new_transaction(
                sender=tx_sender,
                recipient=recipient,
                value=values,
                nonce=random.randint(0, 1000000)
            )
            transactions.append(tx)
        
        return MultiTransactions(sender=sender, multi_txns=transactions)
    
    def inject_single_transaction(self, sender: Optional[str] = None) -> Tuple[bool, str]:
        """Inject a single transaction into the pool"""
        if sender is None:
            sender = random.choice(list(self.sender_keys.keys()))
        
        try:
            # Create a single-transaction MultiTransactions
            recipient = f"recipient_{random.randint(0, 99):03d}"
            tx = self._create_single_transaction(sender, recipient, random.randint(0, 1000000))
            
            multi_txn = MultiTransactions(sender=sender, multi_txns=[tx])
            
            # Always set digest for proper validation
            multi_txn.set_digest()
            
            # For simulation purposes, add signatures to all transactions
            if self.config.validation_enabled:
                # Add dummy signature to MultiTransactions
                multi_txn.signature = b"dummy_signature_for_simulation"
                
                # Add dummy signatures to individual transactions
                for txn in multi_txn.multi_txns:
                    txn.signature = b"dummy_transaction_signature"
            else:
                # Even when validation is disabled, we need to provide dummy signatures
                # to pass the basic existence checks
                multi_txn.signature = b"dummy_signature_for_simulation"
                for txn in multi_txn.multi_txns:
                    txn.signature = b"dummy_transaction_signature"
            
            # Add to pool
            public_key = self.sender_keys[sender] if self.config.validation_enabled else None
            success, message = self.transaction_pool.add_multi_transactions(multi_txn, public_key)
            
            with self.lock:
                self.stats.total_injected += 1
                if success:
                    self.stats.successfully_added += 1
                    self.injected_transactions.append(multi_txn.digest)
                else:
                    if "duplicate" in message.lower():
                        self.stats.duplicates += 1
                    elif "validation" in message.lower():
                        self.stats.failed_validation += 1
                    else:
                        self.stats.injection_errors += 1
            
            return success, message
            
        except Exception as e:
            with self.lock:
                self.stats.total_injected += 1
                self.stats.injection_errors += 1
            return False, f"Error injecting transaction: {str(e)}"
    
    def inject_batch_transactions(self, sender: Optional[str] = None, batch_size: Optional[int] = None) -> List[Tuple[bool, str]]:
        """Inject a batch of transactions"""
        if sender is None:
            sender = random.choice(list(self.sender_keys.keys()))
        if batch_size is None:
            batch_size = self.config.num_transactions_per_batch
        
        results = []
        
        # Determine if this should be an invalid transaction
        is_invalid = random.random() < self.config.invalid_probability
        
        try:
            if is_invalid:
                multi_txn = self._create_invalid_multi_transactions(sender)
            else:
                multi_txn = self._create_multi_transactions(sender, batch_size)
            
            # Always set digest for proper validation
            multi_txn.set_digest()
            
            # For simulation purposes, add signatures to all transactions
            if self.config.validation_enabled:
                # Add dummy signature to MultiTransactions
                multi_txn.signature = b"dummy_signature_for_simulation"
                
                # Add dummy signatures to individual transactions
                for txn in multi_txn.multi_txns:
                    txn.signature = b"dummy_transaction_signature"
            else:
                # Even when validation is disabled, we need to provide dummy signatures
                # to pass the basic existence checks
                multi_txn.signature = b"dummy_signature_for_simulation"
                for txn in multi_txn.multi_txns:
                    txn.signature = b"dummy_transaction_signature"
            
            # Add to pool
            public_key = self.sender_keys[sender] if self.config.validation_enabled else None
            success, message = self.transaction_pool.add_multi_transactions(multi_txn, public_key)
            
            with self.lock:
                self.stats.total_injected += 1
                if success:
                    self.stats.successfully_added += 1
                    self.injected_transactions.append(multi_txn.digest)
                else:
                    if "duplicate" in message.lower():
                        self.stats.duplicates += 1
                    elif "validation" in message.lower():
                        self.stats.failed_validation += 1
                    else:
                        self.stats.injection_errors += 1
            
            results.append((success, message))
            
        except Exception as e:
            with self.lock:
                self.stats.total_injected += 1
                self.stats.injection_errors += 1
            results.append((False, f"Error injecting batch: {str(e)}"))
        
        return results
    
    def run_simulation(self) -> SimulationStats:
        """Run the complete simulation"""
        print(f"Starting transaction injection simulation...")
        print(f"Configuration: {self.config}")
        
        self.stats.start_time = time.time()
        
        try:
            for batch_num in range(self.config.num_batches):
                print(f"\n--- Batch {batch_num + 1}/{self.config.num_batches} ---")
                
                # Inject batch transactions
                batch_results = self.inject_batch_transactions()
                
                # Print batch results
                for i, (success, message) in enumerate(batch_results):
                    status = "SUCCESS" if success else "FAILED"
                    print(f"  Transaction {i+1}: {status} - {message}")
                
                # Print current stats
                current_stats = self.get_current_stats()
                print(f"  Current Stats: {current_stats.total_injected} injected, "
                      f"{current_stats.successfully_added} successful, "
                      f"{current_stats.failed_validation} failed validation, "
                      f"{current_stats.duplicates} duplicates")
                
                # Wait for next injection
                if batch_num < self.config.num_batches - 1:
                    time.sleep(self.config.injection_interval)
        
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
        
        self.stats.end_time = time.time()
        
        # Print final statistics
        self.print_final_stats()
        
        return self.stats
    
    def get_current_stats(self) -> SimulationStats:
        """Get current simulation statistics"""
        with self.lock:
            return SimulationStats(
                total_injected=self.stats.total_injected,
                successfully_added=self.stats.successfully_added,
                failed_validation=self.stats.failed_validation,
                duplicates=self.stats.duplicates,
                injection_errors=self.stats.injection_errors,
                start_time=self.stats.start_time,
                end_time=time.time()
            )
    
    def print_final_stats(self):
        """Print final simulation statistics"""
        pool_stats = self.transaction_pool.get_pool_stats()
        
        print("\n" + "="*60)
        print("SIMULATION RESULTS")
        print("="*60)
        print(f"Total simulation time: {self.stats.duration:.2f} seconds")
        print(f"Total transactions injected: {self.stats.total_injected}")
        print(f"Successfully added to pool: {self.stats.successfully_added}")
        print(f"Failed validation: {self.stats.failed_validation}")
        print(f"Duplicates: {self.stats.duplicates}")
        print(f"Injection errors: {self.stats.injection_errors}")
        print(f"Success rate: {self.stats.success_rate:.2f}%")
        print(f"Injection rate: {self.stats.total_injected/self.stats.duration:.2f} tx/sec")
        
        print("\nTransaction Pool Status:")
        print(f"  Transactions in pool: {pool_stats['total_transactions']}")
        print(f"  Unique senders: {pool_stats['unique_senders']}")
        print(f"  Pool size: {pool_stats['pool_size_bytes']} bytes")
        
        print("="*60)
    
    def cleanup(self):
        """Clean up simulation resources"""
        try:
            # Clear the transaction pool
            self.transaction_pool.clear_pool()
            
            # Remove database file or save it if preservation is enabled
            if os.path.exists("simulation_pool.db"):
                if self.config.preserve_database:
                    # Generate timestamp for unique filename
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    db_filename = f"simulation_pool_{timestamp}.db"
                    save_path = os.path.join(self.config.database_output_dir, db_filename)
                    
                    # Copy database file to output directory
                    import shutil
                    shutil.copy2("simulation_pool.db", save_path)
                    print(f"Database file preserved at: {save_path}")
                
                # Remove original database file
                os.remove("simulation_pool.db")
                
        except Exception as e:
            print(f"Error during cleanup: {e}")


def main():
    """Main function to run the simulation"""
    # Create simulation configuration
    config = SimulationConfig(
        num_senders=5,
        num_transactions_per_batch=3,
        num_batches=10,
        injection_interval=0.5,
        validation_enabled=True,
        signature_enabled=False,  # Disabled for simplicity in simulation
        duplicate_probability=0.05,
        invalid_probability=0.02,
        preserve_database=False,  # Set to True to preserve database file
        database_output_dir="simulation_data"  # Directory to save database files
    )
    
    # Create injector and run simulation
    injector = TransactionInjector(config)
    
    try:
        stats = injector.run_simulation()
        return stats
    finally:
        injector.cleanup()


if __name__ == "__main__":
    main()
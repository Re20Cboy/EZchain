import hashlib
import pickle
import datetime
from typing import List, Any, Optional

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.exceptions import InvalidSignature

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from EZ_Tool_Box.Hash import sha256_hash
from .SingleTransaction import Transaction

class MultiTransactions:
    """Multi-transaction class for handling multiple transactions as a single unit."""
    
    # Class constants
    SIGNATURE_ALGORITHM = ec.ECDSA(hashes.SHA256())
    
    def __init__(self, sender: str, multi_txns: List[Transaction]):
        """
        Initialize MultiTransaction.
        
        Args:
            sender: Sender address
            multi_txns: List of transactions to include
        """
        self.sender = sender
        self.multi_txns = multi_txns
        self.time = datetime.datetime.now().isoformat()  # Record timestamp in ISO format
        self.signature: Optional[bytes] = None
        self.digest: Optional[str] = None

    def encode(self) -> bytes:
        """
        Encode the multi-transaction data using pickle.
        
        Returns:
            Encoded transaction data as bytes
        """
        # Encode the entire MultiTransactions object, not just multi_txns
        encoded_data = pickle.dumps({
            'sender': self.sender,
            'multi_txns': self.multi_txns,
            'time': self.time,
            'signature': self.signature,
            'digest': self.digest
        })
        return encoded_data

    @staticmethod
    def decode(to_decode: bytes) -> 'MultiTransactions':
        """
        Decode the multi-transaction data from pickle.
        
        Args:
            to_decode: Encoded transaction data
            
        Returns:
            Decoded MultiTransactions object
        """
        decoded_data = pickle.loads(to_decode)
        multi_txn = MultiTransactions(
            sender=decoded_data['sender'],
            multi_txns=decoded_data['multi_txns']
        )
        
        # Restore additional fields
        multi_txn.time = decoded_data.get('time')
        multi_txn.signature = decoded_data.get('signature')
        multi_txn.digest = decoded_data.get('digest')
        
        return multi_txn

    def set_digest(self) -> None:
        """
        Calculate and set the digest for the multi-transaction.
        """
        digest = sha256_hash(self.encode())
        self.digest = digest

    def sig_acc_txn(self, load_private_key: bytes) -> None:
        """
        Sign the multi-transaction with the provided private key.
        
        Args:
            load_private_key: Private key in PEM format for signing
        """
        # Check if multi_txns is empty
        if not self.multi_txns:
            raise ValueError("Cannot sign empty transaction list")
            
        private_key = load_pem_private_key(load_private_key, password=None)
        
        # Calculate digest once and reuse
        digest = sha256_hash(self.encode())
        digest_bytes = digest.encode('utf-8')
        self.digest = digest
        
        # Sign the digest
        signature = private_key.sign(data=digest_bytes, signature_algorithm=self.SIGNATURE_ALGORITHM)
        self.signature = signature

    def check_acc_txn_sig(self, load_public_key: bytes) -> bool:
        """
        Verify the multi-transaction signature with the provided public key.
        
        Args:
            load_public_key: Public key in PEM format for verification
            
        Returns:
            True if signature is valid, False otherwise
        """
        if self.signature is None or self.digest is None:
            return False
            
        public_key = load_pem_public_key(load_public_key)
        signature_algorithm = self.SIGNATURE_ALGORITHM
        
        try:
            public_key.verify(
                self.signature,
                self.digest.encode('utf-8'),
                signature_algorithm
            )
            return True
        except InvalidSignature:
            return False
    
    def __len__(self) -> int:
        """
        Return the number of transactions in this multi-transaction.
        
        Returns:
            Number of transactions
        """
        return len(self.multi_txns)
    
    def __getitem__(self, index):
        """
        Get transaction by index.
        
        Args:
            index: Index of the transaction to retrieve
            
        Returns:
            Transaction at the specified index
        """
        return self.multi_txns[index]
    
    def __iter__(self):
        """
        Make the MultiTransactions object iterable.
        
        Returns:
            Iterator over the transactions
        """
        return iter(self.multi_txns)
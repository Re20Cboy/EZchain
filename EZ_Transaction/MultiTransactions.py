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
    
    def __init__(self, sender: str, sender_id: str, multi_txns: List[Transaction]):
        """
        Initialize MultiTransaction.
        
        Args:
            sender: Sender address
            sender_id: Sender ID
            multi_txns: List of transactions to include
        """
        self.sender = sender
        self.sender_id = sender_id
        self.multi_txns = multi_txns
        self.time = datetime.datetime.now().isoformat()  # Record timestamp in ISO format
        self.signature: Optional[bytes] = None
        self.digest: Optional[str] = None

    def encode(self) -> bytes:
        """
        Encode the multi-transaction list using pickle.
        
        Returns:
            Encoded transaction data as bytes
        """
        encoded_txns = pickle.dumps(self.multi_txns)
        return encoded_txns

    @staticmethod
    def decode(to_decode: bytes) -> List[Transaction]:
        """
        Decode the multi-transaction data from pickle.
        
        Args:
            to_decode: Encoded transaction data
            
        Returns:
            Decoded transaction list
        """
        decoded_txns = pickle.loads(to_decode)
        return decoded_txns

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
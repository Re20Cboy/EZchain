import hashlib
import pickle
import datetime
from typing import List, Optional, Any
import sys
import os
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from EZ_Tool_Box.Hash import sha256_hash
from EZ_Tool_Box.SecureSignature import secure_signature_handler
from EZ_Value import Value

class Transaction:
    def __init__(self, sender: str, recipient: str, nonce: int, signature: Optional[bytes], value: List[Value], time: Optional[str]):
        self.sender = sender
        self.recipient = recipient
        self.nonce = nonce
        self.signature = signature
        self.value = value
        self.time = time
        # Auto-calculate tx_hash based on all parameters except signature
        self.tx_hash = self._calculate_hash()

    def _calculate_hash(self) -> bytes:
        """Calculate hash of the transaction using deterministic JSON serialization."""
        import json
        
        # Create a deterministic representation for hashing
        # Exclude signature and tx_hash as they are results of this hash
        txn_data = {
            "sender": self.sender,
            "recipient": self.recipient,
            "nonce": self.nonce,
            "time": self.time,
            "value": self._serialize_values()
        }
        
        # Use sorted keys and ensure consistent serialization
        txn_json = json.dumps(txn_data, sort_keys=True, separators=(',', ':'))
        
        # Calculate SHA256 hash
        return hashlib.sha256(txn_json.encode('utf-8')).digest()
    
    def _serialize_values(self) -> list:
        """Serialize Value objects for deterministic hashing."""
        serialized_values = []
        for value in self.value:
            # Assuming Value objects have a to_dict() method or similar
            if hasattr(value, 'to_dict'):
                serialized_values.append(value.to_dict())
            else:
                # Fallback to basic attributes
                serialized_values.append({
                    "amount": getattr(value, 'amount', 0),
                    "type": getattr(value, 'type', 'unknown')
                })
        return serialized_values

    def txn2str(self):
        txn_str = f"Sender: {self.sender}\n"
        txn_str += f"Recipient: {self.recipient}\n"
        txn_str += f"Nonce: {str(self.nonce)}\n"
        txn_str += f"Value: {self.value}\n"
        txn_str += f"TxHash: {str(self.tx_hash)}\n"
        txn_str += f"Time: {self.time}\n"
        return txn_str

    def print_txn_dst(self):
        print('---------txn---------')
        print(self)
        print(self.txn2str())
        for one_v in self.value:
            one_v.print_value()
        print('---------txn end---------')

    def sig_txn(self, load_private_key: bytes) -> None:
        """Sign the transaction with the provided private key using secure signature handler."""
        # Prepare transaction data for signing
        transaction_data = {
            "sender": self.sender,
            "recipient": self.recipient,
            "nonce": self.nonce,
            "timestamp": self.time,
            "value": self._serialize_values()
        }
        
        # Use secure signature handler
        signature_result = secure_signature_handler.sign_transaction(
            sender=self.sender,
            recipient=self.recipient,
            nonce=self.nonce,
            value_data=self._serialize_values(),
            private_key_pem=load_private_key,
            timestamp=self.time
        )
        
        # Set the signature from the secure handler result
        self.signature = bytes.fromhex(signature_result["signature"])

    def is_sent_to_self(self) -> bool:
        """Check if the transaction is sent to the same sender."""
        return self.sender == self.recipient

    def check_txn_sig(self, load_public_key: bytes) -> bool:
        """Verify the transaction signature with the provided public key using secure signature handler."""
        if self.signature is None:
            return False
        
        # Prepare transaction data for verification
        transaction_data = {
            "sender": self.sender,
            "recipient": self.recipient,
            "nonce": self.nonce,
            "timestamp": self.time,
            "value": self._serialize_values()
        }
        
        # Use secure signature handler for verification
        return secure_signature_handler.verify_transaction_signature(
            transaction_data=transaction_data,
            signature_hex=self.signature.hex(),
            public_key_pem=load_public_key
        )

    def get_values(self) -> List[Value]:
        """Get the list of values in this transaction."""
        return self.value

    def print_tx(self) -> str:
        """Format and return transaction details as string."""
        transaction_details = [self.sender, self.recipient, self.value, self.tx_hash]
        return f"{transaction_details}\n"

    def encode(self) -> bytes:
        """Encode the transaction using pickle."""
        return pickle.dumps(self)

    @staticmethod
    def decode(encoded_data: bytes) -> 'Transaction':
        """Decode the transaction from pickle data."""
        return pickle.loads(encoded_data)

    @staticmethod
    def new_transaction(sender: str, recipient: str, value: List[Any], nonce: int) -> 'Transaction':
        """Create a new transaction with automatic hash calculation."""
        return Transaction(
            sender=sender,
            recipient=recipient,
            nonce=nonce,
            signature=None,
            value=value,
            time=datetime.datetime.now().isoformat()
        )

    def count_value_intersect_txn(self, value: Any) -> int:
        """Count the number of values that intersect with the given value."""
        return sum(1 for v in self.value if v.is_intersect_value(value))

    def count_value_in_value(self, value: Any) -> int:
        """Count how many times the value is contained within the transaction values."""
        return sum(1 for v in self.value if v.is_in_value(value))
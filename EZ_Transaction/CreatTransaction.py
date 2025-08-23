#import sys
#import os

# Add the project root to Python path
#sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SingleTransaction import Transaction

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

class CreateTransaction:
    def __init__(self, sender, recipient, value, nonce):
        self.sender = sender
        self.recipient = recipient
        self.value = value
        self.nonce = nonce

    def sign_transaction(self, private_key):
        # Sign the transaction with the sender's private key
        self.signature = private_key.sign(self.to_bytes())
        return self.signature

    def to_bytes(self):
        # Convert the transaction details to bytes
        return f"{self.sender}{self.recipient}{self.value}{self.nonce}".encode()

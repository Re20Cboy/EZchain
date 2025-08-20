import hashlib
import pickle
import datetime

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from EZ_Tool_Box.Hash import sha256_hash

class AccountTxns:
    def __init__(self, sender, senderID, accTxns):
        self.sender = sender
        self.senderID = senderID
        # self.AccTxnsHash = None
        self.accTxns = accTxns
        self.time = str(datetime.datetime.now()) # Record the timestamp
        self.signature = None
        self.digest = None

    def Encode(self): # Here only the actual txn list is encoded
        encoded_tx = pickle.dumps(self.accTxns)
        return encoded_tx

    @staticmethod
    def Decode(to_decode):
        decoded_tx = pickle.loads(to_decode)
        return decoded_tx

    def set_digest(self):
        digest = sha256_hash(self.Encode())
        self.digest = digest

    def sig_accTxn(self, load_private_key): # The digest information of accTxn is assigned during signing
        private_key = load_pem_private_key(load_private_key, password=None)
        # Calculate the hash of the block using the SHA256 hash algorithm
        digest = sha256_hash(self.Encode())
        digest_bytes = digest.encode('utf-8')
        self.Digest = digest
        signature_algorithm = ec.ECDSA(hashes.SHA256())
        # Sign the block hash value
        signature = private_key.sign(data=digest_bytes, signature_algorithm=signature_algorithm)
        self.signature = signature

    def check_accTxn_sig(self, load_public_key):
        public_key = load_pem_public_key(load_public_key)
        digest = self.digest
        signature_algorithm = ec.ECDSA(hashes.SHA256())
        # Verify the signature
        try:
            public_key.verify(
                self.signature,
                digest,
                signature_algorithm
            )
            return True
        except:
            return False

class Transaction:
    def __init__(self, sender, recipient, nonce, signature, value, tx_hash, time):
        self.sender = sender
        self.recipient = recipient
        self.nonce = nonce
        self.signature = signature
        self.value = value
        self.tx_hash = tx_hash
        self.time = time

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

    def sig_txn(self, load_private_key):
        # Load private key from the private key path
        private_key = load_pem_private_key(load_private_key, password=None)
        # Calculate the hash of the block using the SHA256 hash algorithm
        block_hash = hashes.Hash(hashes.SHA256())
        block_hash.update(self.txn2str().encode('utf-8'))
        digest = block_hash.finalize()
        signature_algorithm = ec.ECDSA(hashes.SHA256())
        # Sign the block hash value
        signature = private_key.sign(data=digest, signature_algorithm=signature_algorithm)
        self.signature = signature

    def is_sent_to_self(self):
        if self.sender == self.recipient:
            return True
        return False

    def check_txn_sig(self, load_public_key):
        # Load public key from the public key path
        public_key = load_pem_public_key(load_public_key)
        # Calculate the hash of the block using the SHA256 hash algorithm
        block_hash = hashes.Hash(hashes.SHA256())
        block_hash.update(self.txn2str().encode('utf-8'))
        digest = block_hash.finalize()
        signature_algorithm = ec.ECDSA(hashes.SHA256())
        # Verify the signature
        try:
            public_key.verify(
                self.signature,
                digest,
                signature_algorithm
            )
            return True
        except:
            return False

    def get_values(self):
        return self.value

    def PrintTx(self):
        vals = [self.sender, self.recipient, self.value, self.tx_hash]
        res = f"{vals}\n"
        return res

    def Encode(self):
        encoded_tx = pickle.dumps(self)
        return encoded_tx

    @staticmethod
    def Decode(to_decode):
        decoded_tx = pickle.loads(to_decode)
        return decoded_tx

    @staticmethod
    def NewTransaction(sender, recipient, value, nonce):
        tx = Transaction(
            sender=sender,
            recipient=recipient,
            nonce=nonce,
            signature=None,
            value=value,
            tx_hash=None,
            time=None
        )
        encoded_tx = tx.Encode()
        tx_hash = hashlib.sha256(encoded_tx).digest()
        tx.tx_hash = tx_hash
        return tx

    def count_value_intersect_txn(self, value):
        # Calculate the total number of transactions that intersect with a given value subset
        count = 0  # Counter for the number of transactions intersecting with this value
        for V in self.value:
            if V.isIntersectValue(value):
                count += 1
        return count

    def count_value_in_value(self, value):
        # Check if the value is completely transferred only once in this transaction (either as the same value or contained within a larger value)
        count = 0  # Counter for the number of transactions
        for V in self.value:
            if V.isInValue(value):
                count += 1
        return count
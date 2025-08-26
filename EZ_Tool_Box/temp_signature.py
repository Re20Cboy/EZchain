import hashlib
import json
from EZ_Tool_Box.Hash import sha256_hash

class TempSignatureSystem:
    def __init__(self):
        # Temporary test key pair - in production this would come from proper key management
        self.test_private_key = "test_private_key_12345"
        self.test_public_key = "test_public_key_67890"
    
    def generate_signature(self, miner_id):
        """
        Generate a temporary signature using a test key pair.
        
        Args:
            miner_id (str): The miner ID to sign
            
        Returns:
            dict: A dictionary containing signature components for easy verification
        """
        # Create a signature string that includes miner info and timestamp
        timestamp = str(int(__import__('datetime').datetime.now().timestamp()))
        signature_string = f"{miner_id}:{timestamp}:{self.test_private_key}"
        
        # Create the signature
        signature_hash = sha256_hash(signature_string)
        
        return {
            "signature": signature_hash,
            "miner_id": miner_id,
            "timestamp": timestamp,
            "public_key": self.test_public_key
        }
    
    def verify_signature(self, signature_data, block_data):
        """
        Verify a temporary signature.
        
        Args:
            signature_data (dict): The signature data to verify
            block_data (str): The block data string that was originally signed
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not signature_data:
            return False
            
        expected_string = f"{signature_data['miner_id']}:{signature_data['timestamp']}:{self.test_private_key}"
        expected_signature = sha256_hash(expected_string)
        
        return signature_data["signature"] == expected_signature

# Create a global instance for easy access
temp_signature_system = TempSignatureSystem()
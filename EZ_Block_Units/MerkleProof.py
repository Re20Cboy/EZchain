import sys
import os
# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from EZ_Tool_Box.Hash import sha256_hash


class MerkleTreeProof:
    def __init__(self, mt_prf_list=[]):
        self.mt_prf_list = mt_prf_list

    def check_prf(self, acc_txns_digest, true_root):
        check_flag = True
        hashed_encode_acc_txns = sha256_hash(acc_txns_digest)

        if len(self.mt_prf_list) == 0:
            return False

        if len(self.mt_prf_list) == 1:
            if (hashed_encode_acc_txns != self.mt_prf_list[0] or true_root != self.mt_prf_list[0] or
                    true_root != hashed_encode_acc_txns):
                check_flag = False
            return check_flag

        # For Merkle proof structure, the first element should be the leaf hash
        # If it doesn't match, then the proof is invalid for this data
        # 这里验证mt_prf_list首位元素是否为data的hash，与之前的检测逻辑不同，之前是检测前两位是否相同。
        if hashed_encode_acc_txns != self.mt_prf_list[0]:
            check_flag = False
        
        if self.mt_prf_list[-1] != true_root:
            check_flag = False
        
        # Check if proof has correct structure (odd number of elements: pairs + root)
        if len(self.mt_prf_list) % 2 != 1:
            return False
        
        # Verify the proof path from leaf to root
        current_hash = hashed_encode_acc_txns
        
        # Process each pair in the proof (sibling hash, parent hash)
        for i in range(len(self.mt_prf_list) // 2):
            sibling_hash = self.mt_prf_list[2 * i + 1]
            parent_hash = self.mt_prf_list[2 * i + 2]
            
            # Try both orders for hash combination
            combined_hash1 = sha256_hash(current_hash + sibling_hash)
            combined_hash2 = sha256_hash(sibling_hash + current_hash)
            
            # The parent should match one of the combinations
            if combined_hash1 != parent_hash and combined_hash2 != parent_hash:
                check_flag = False
                break
            
            current_hash = parent_hash
        
        # Final verification: current_hash should match the root
        if current_hash != self.mt_prf_list[-1]:
            check_flag = False
        
        return check_flag
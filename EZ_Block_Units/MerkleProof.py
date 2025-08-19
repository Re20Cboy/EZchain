import sys
import os
# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from EZ_Tool_Box.Hash import sha256_hash


class merkle_tree_proof:
    def __init__(self, mt_prf_list=[]):
        self.mt_prf_list = mt_prf_list

    def check_prf(self, acc_txns_digest, true_root):
        def hash(val):
            return sha256_hash(val)

        check_flag = True
        hashed_encode_acc_txns = hash(acc_txns_digest)

        if len(self.mt_prf_list) == 1:
            if (hashed_encode_acc_txns != self.mt_prf_list[0] or true_root != self.mt_prf_list[0] or
                    true_root != hashed_encode_acc_txns):
                check_flag = False
            return check_flag

        if hashed_encode_acc_txns != self.mt_prf_list[0] and hashed_encode_acc_txns != self.mt_prf_list[1]:
            check_flag = False
        
        if self.mt_prf_list[-1] != true_root:
            check_flag = False
        
        last_hash = None
        for i in range(len(self.mt_prf_list) // 2):
            last_hash = self.mt_prf_list[2 * i + 2]
            if hash(self.mt_prf_list[2 * i] + self.mt_prf_list[2 * i + 1]) != last_hash and hash(
                    self.mt_prf_list[2 * i + 1] + self.mt_prf_list[2 * i]) != last_hash:
                check_flag = False
        
        if last_hash != self.mt_prf_list[-1]:
            check_flag = False
        
        return check_flag
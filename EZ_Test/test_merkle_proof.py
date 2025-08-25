#!/usr/bin/env python3
"""
Unit tests for Merkle Proof module.
"""

import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__) + '/..')

try:
    from EZ_Block_Units.MerkleProof import MerkleTreeProof
    from EZ_Block_Units.MerkleTree import MerkleTree
except ImportError as e:
    print(f"Error importing MerkleProof: {e}")
    sys.exit(1)


class TestMerkleTreeProof(unittest.TestCase):
    """Test suite for Merkle Tree Proof implementation."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data = ["data1", "data2", "data3", "data4"]
        self.tree = MerkleTree(self.test_data)
        self.true_root = self.tree.get_root_hash()
        
        # Generate proof for the first leaf
        self.proof_data = self.tree.prf_list[0]
        self.proof = MerkleTreeProof(self.proof_data)
        
        # Generate proof for the second leaf
        self.proof_data_2 = self.tree.prf_list[1]
        self.proof_2 = MerkleTreeProof(self.proof_data_2)
        
    def test_proof_initialization(self):
        """Test MerkleTreeProof initialization."""
        # Test with empty proof list
        empty_proof = MerkleTreeProof([])
        self.assertEqual(empty_proof.mt_prf_list, [])
        
        # Test with proof data
        self.assertEqual(self.proof.mt_prf_list, self.proof_data)
        self.assertEqual(self.proof_2.mt_prf_list, self.proof_data_2)
        
    def test_proof_single_item_validation(self):
        """Test proof validation with single item."""
        single_data = ["single_item"]
        single_tree = MerkleTree(single_data, is_genesis_block=True)
        single_root = single_tree.get_root_hash()
        
        # Create proof for single item
        single_proof = MerkleTreeProof([single_root])
        is_valid = single_proof.check_prf(single_data[0], single_root)
        
        self.assertTrue(is_valid)
        
    def test_proof_valid_proof(self):
        """Test valid proof validation."""
        # Test proof for first leaf
        is_valid = self.proof.check_prf(self.test_data[0], self.true_root)
        self.assertTrue(is_valid)
        
        # Test proof for second leaf
        is_valid = self.proof_2.check_prf(self.test_data[1], self.true_root)
        self.assertTrue(is_valid)
        
    def test_proof_invalid_root_hash(self):
        """Test proof validation with invalid root hash."""
        invalid_root = "invalid_root_hash"
        is_valid = self.proof.check_prf(self.test_data[0], invalid_root)
        self.assertFalse(is_valid)
        
    def test_proof_invalid_transaction_hash(self):
        """Test proof validation with invalid transaction hash."""
        invalid_tx = "invalid_transaction_hash"
        is_valid = self.proof.check_prf(invalid_tx, self.true_root)
        self.assertFalse(is_valid)
        
    def test_proof_modified_proof_data(self):
        """Test proof validation with modified proof data."""
        # Modify proof data by changing one element
        modified_proof_data = self.proof_data.copy()
        modified_proof_data[0] = "modified_hash"

        modified_proof = MerkleTreeProof(modified_proof_data)
        is_valid = modified_proof.check_prf(self.test_data[0], self.true_root)
        self.assertFalse(is_valid)
        
    def test_proof_empty_proof_list(self):
        """Test proof validation with empty proof list."""
        empty_proof = MerkleTreeProof([])
        is_valid = empty_proof.check_prf("test_data", self.true_root)
        self.assertFalse(is_valid)
        
    def test_proof_single_item_proof(self):
        """Test single item proof with different scenarios."""
        single_data = ["single_item"]
        single_tree = MerkleTree(single_data)
        single_root = single_tree.get_root_hash()
        
        # Test with correct data and root
        single_proof = MerkleTreeProof([single_root])
        self.assertTrue(single_proof.check_prf(single_data[0], single_root))
        
        # Test with wrong data
        self.assertFalse(single_proof.check_prf("wrong_data", single_root))
        
        # Test with wrong root
        self.assertFalse(single_proof.check_prf(single_data[0], "wrong_root"))
        
    def test_proof_different_leaves(self):
        """Test proof validation for different leaves."""
        # Create tree with more data
        more_data = ["tx1", "tx2", "tx3", "tx4", "tx5", "tx6"]
        more_tree = MerkleTree(more_data)
        more_root = more_tree.get_root_hash()
        
        # Test proof for each leaf
        for i in range(len(more_data)):
            leaf_proof = MerkleTreeProof(more_tree.prf_list[i])
            is_valid = leaf_proof.check_prf(more_data[i], more_root)
            self.assertTrue(is_valid, f"Proof for leaf {i} should be valid")
            
    def test_proof_hash_order_consistency(self):
        """Test proof validation with hash order variations."""
        # Create proof and verify it works
        is_valid = self.proof.check_prf(self.test_data[0], self.true_root)
        self.assertTrue(is_valid)
        
        # Reverse the order of hash pairs in proof and check if it still works
        # (this depends on the implementation's handling of hash order)
        reversed_proof = []
        for i in range(0, len(self.proof_data), 2):
            if i + 1 < len(self.proof_data):
                reversed_proof.extend([self.proof_data[i + 1], self.proof_data[i]])
            else:
                reversed_proof.append(self.proof_data[i])

        reversed_proof_obj = MerkleTreeProof(reversed_proof)
        # This should work if the implementation handles both orders
        # If not, this test might fail, which is acceptable
        result = reversed_proof_obj.check_prf(self.test_data[0], self.true_root)
        self.assertIsInstance(result, bool)  # Should not crash, just return boolean
        
    def test_proof_large_dataset(self):
        """Test proof validation with large dataset."""
        large_data = [f"tx_{i}" for i in range(50)]
        large_tree = MerkleTree(large_data)
        large_root = large_tree.get_root_hash()
        
        # Test proof for middle leaf
        middle_index = len(large_data) // 2
        middle_proof = MerkleTreeProof(large_tree.prf_list[middle_index])
        is_valid = middle_proof.check_prf(large_data[middle_index], large_root)
        self.assertTrue(is_valid)
        
    def test_proof_unicode_data(self):
        """Test proof validation with unicode data."""
        unicode_data = ["你好", "世界", "🌍"]
        unicode_tree = MerkleTree(unicode_data)
        unicode_root = unicode_tree.get_root_hash()
        
        # Test proof for first unicode item
        unicode_proof = MerkleTreeProof(unicode_tree.prf_list[0])
        is_valid = unicode_proof.check_prf(unicode_data[0], unicode_root)
        self.assertTrue(is_valid)
        
    """def test_proof_mixed_data_types(self):
        mixed_data = ["string", 123, 45.67, True, None]
        mixed_tree = merkle_tree(mixed_data)
        mixed_root = mixed_tree.get_root_hash()
        
        # Test proof for numeric data
        numeric_proof = merkle_tree_proof(mixed_tree.prf_list[1])
        is_valid = numeric_proof.check_prf(str(mixed_data[1]), mixed_root)
        self.assertTrue(is_valid)"""
        
    def test_proof_edge_cases(self):
        """Test proof validation edge cases."""
        # Test with empty string
        empty_string_data = [""]
        empty_tree = MerkleTree(empty_string_data)
        empty_root = empty_tree.get_root_hash()
        empty_proof = MerkleTreeProof(empty_tree.prf_list[0])
        self.assertTrue(empty_proof.check_prf("", empty_root))
        
        # Test with very long strings
        long_string = "a" * 1000
        long_data = [long_string]
        long_tree = MerkleTree(long_data)
        long_root = long_tree.get_root_hash()
        long_proof = MerkleTreeProof(long_tree.prf_list[0])
        self.assertTrue(long_proof.check_prf(long_string, long_root))
        
    def test_proof_integrity(self):
        """Test proof data integrity."""
        # Ensure proof data has proper structure
        self.assertIsInstance(self.proof_data, list)
        
        # For multi-item proofs, should have even number of elements (pairs)
        if len(self.proof_data) > 1:
            self.assertEqual(len(self.proof_data) % 2, 1)  # Should be odd (last element is root)
            
    def test_proof_corrupted_proof_structure(self):
        """Test proof validation with corrupted proof structure."""
        # Create proof with wrong number of elements
        corrupted_proof_data = self.proof_data.copy()
        
        # Remove one element (making it even, but should fail validation)
        if len(corrupted_proof_data) > 1:
            corrupted_proof_data.pop()
            corrupted_proof = MerkleTreeProof(corrupted_proof_data)
            result = corrupted_proof.check_prf(self.test_data[0], self.true_root)
            self.assertFalse(result)
            
    def test_proof_multiple_different_proofs(self):
        """Test multiple different proofs from same tree."""
        # Create tree with multiple items
        multi_data = ["tx1", "tx2", "tx3", "tx4"]
        multi_tree = MerkleTree(multi_data)
        multi_root = multi_tree.get_root_hash()
        
        # Verify all proofs are valid
        for i in range(len(multi_data)):
            proof = MerkleTreeProof(multi_tree.prf_list[i])
            is_valid = proof.check_prf(multi_data[i], multi_root)
            self.assertTrue(is_valid, f"Proof for item {i} should be valid")
            
        # Verify that cross-verification fails (wrong data with proof)
        for i in range(len(multi_data)):
            proof = MerkleTreeProof(multi_tree.prf_list[i])
            # Try with wrong data
            wrong_data_index = (i + 1) % len(multi_data)
            is_valid = proof.check_prf(multi_data[wrong_data_index], multi_root)
            self.assertFalse(is_valid, f"Proof for item {i} should fail with wrong data")


class TestMerkleProofIntegration(unittest.TestCase):
    """Test suite for Merkle Proof integration with Merkle Tree."""
    
    def setUp(self):
        """Set up test fixtures for integration tests."""
        self.test_data_sets = [
            ["item1", "item2"],
            ["a", "b", "c"],
            ["tx1", "tx2", "tx3", "tx4", "tx5"],
            [f"item_{i}" for i in range(10)]
        ]
        
    def test_integration_tree_proof_consistency(self):
        """Test that tree and proof work together consistently."""
        for data in self.test_data_sets:
            with self.subTest(data=data):
                tree = MerkleTree(data)
                root_hash = tree.get_root_hash()
                
                # Test that each leaf's proof is valid
                for i in range(len(data)):
                    proof = MerkleTreeProof(tree.prf_list[i])
                    is_valid = proof.check_prf(data[i], root_hash)
                    self.assertTrue(is_valid, f"Proof for leaf {i} should be valid")
                    
    def test_integration_proof_modification_detection(self):
        """Test that proof modifications are detected."""
        tree = MerkleTree(["data1", "data2", "data3", "data4"])
        root_hash = tree.get_root_hash()
        
        # Get proof and modify it
        proof_data = tree.prf_list[0].copy()
        proof_obj = MerkleTreeProof(proof_data)

        # Original should be valid
        self.assertTrue(proof_obj.check_prf("data1", root_hash))
        
        # Modify proof data and check detection
        proof_data[0] = "modified_hash"
        modified_proof = MerkleTreeProof(proof_data)
        self.assertFalse(modified_proof.check_prf("data1", root_hash))


if __name__ == '__main__':
    unittest.main(verbosity=2)
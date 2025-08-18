#from const import *
from Bloom import BloomFilter,BloomFilterEncoder
import datetime
import unit
import hashlib
import json
import pickle

class Block:
    def __init__(self, index, m_tree_root, miner, pre_hash, nonce=0, bloom_size=1024*1024, bloom_hash_count=5, time=None):
        """
        Initialize a new block in the blockchain.

        Args:
            index (int): The index of the block in the blockchain.
            m_tree_root (str): The root of the Merkle Tree for this block.
            miner (str): The ID of the miner who mined this block.
            pre_hash (str): The hash of the previous block in the chain.
            nonce (int): The nonce used in the mining process. Defaults to 0.
            bloom_size (int): The size of the Bloom filter. Defaults to 1024*1024.
            bloom_hash_count (int): The number of hash functions for the Bloom filter. Defaults to 5.
            time (datetime): The timestamp when the block is created. Defaults to current time.
        """
        self.index = index
        self.nonce = nonce
        self.bloom = BloomFilter(bloom_size, bloom_hash_count)
        self.m_tree_root = m_tree_root
        self.time = time if time is not None else datetime.datetime.now()
        self.miner = miner
        self.pre_hash = pre_hash
        self.sig = unit.generate_signature(miner) if index != 0 else 0  # Digital signature implementation pending

    def block_to_json(self):
        """
        # encode bloom to json
        serialized_bloom_filter = json.dumps(self.bloom, cls=bloom.BloomFilterEncoder, indent=4)
        other_json = json.dumps(
            {"index": self.index, "nonce": self.nonce, "m_tree_root": self.m_tree_root,
             "time": self.time, "miner": self.miner, "pre_hash": self.pre_hash, "sig": self.sig}, sort_keys=True).encode()
        return (other_json, serialized_bloom_filter)
        """
        # Create a dictionary to represent the non-byte data
        other_data = {
            "index": self.index,
            "nonce": self.nonce,
            "m_tree_root": self.m_tree_root,
            "time": self.time,
            "miner": self.miner,
            "pre_hash": self.pre_hash,
            "sig": self.sig
        }
        # Encode the bloom filter to JSON
        serialized_bloom_filter = json.dumps(self.bloom, cls=BloomFilterEncoder, indent=4)
        return (json.dumps(other_data, sort_keys=True), serialized_bloom_filter)

    def block_to_str(self):
        """
        Convert the block into a string representation for hashing and signing.
        The signature is not included in this representation.

        DO NOT CHANGE THIS FUNC !!!!! otherwise, sig and check_sig ERR!!

        Returns:
            str: The string representation of the block.
        """
        block_str = f"Index: {self.index}\n"
        block_str += f"Nonce: {self.nonce}\n"
        block_str += f"Bloom: {str(self.bloom)}\n"
        block_str += f"Merkle Tree Root: {self.m_tree_root}\n"
        block_str += f"Time: {str(self.time)}\n"
        block_str += f"Miner: {self.miner}\n"
        block_str += f"Previous Hash: {self.pre_hash}\n"
        return block_str # no sig_to_str !!!

    def block_to_short_str(self):
        block_str = f"Index: {self.index}, Miner: {self.miner}"
        return block_str

    def block_to_pickle(self):
        return pickle.dumps(self)

    """def is_valid_next_block(self, block):
        if self.index + 1 == block.index:
            if self.get_hash() == block.get_pre_hash():
                return self.index
        return False"""

    def is_valid_next_block_dst(self, block):
        if self.index + 1 == block.index:
            if self.get_hash() == block.get_pre_hash():
                return True
        return False

    """def print_block(self):
      print('//////// BLOCK ////////\n')
      print(self.block_to_str())
      print('//////// BLOCK ////////')"""

    # Getter methods
    def get_index(self):
        return self.index

    def get_nonce(self):
        return self.nonce

    def get_bloom(self):
        return self.bloom

    def get_m_tree_root(self):
        return self.m_tree_root

    def get_time(self):
        return self.time

    def get_miner(self):
        return self.miner

    def get_pre_hash(self):
        return self.pre_hash

    def get_sig(self):
        return self.sig

    def get_hash(self):
        """Calculate and return the hash of the block."""
        return hashlib.sha256(self.block_to_str().encode("utf-8")).hexdigest()

    def add_item_to_bloom(self, item):
        """Add an item to the block's Bloom filter."""
        self.bloom.add(item)

    def is_in_bloom(self, item):
        """Check if an item is in the block's Bloom filter."""
        return item in self.bloom
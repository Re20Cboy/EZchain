from bitarray import bitarray
import mmh3
import zlib
import base64

class BloomFilter(set):  # Inherits from the set class
    """
    A Bloom Filter implementation.

    Attributes:
        size (int): Length of the binary vector.
        hash_count (int): Number of hash functions.
    
    The number of hash functions should satisfy:
    (hash_count = binary_vector_length * ln(2) / number_of_elements_inserted)
    """
    def __init__(self, size=1024 * 1024, hash_count=5, compressed=False):
        """
        Initializes the Bloom Filter with a given size and hash count.

        Parameters:
            size (int): The size of the bit array. Default is 1024 * 1024.
            hash_count (int): The number of hash functions to use. Default is 5.
            compressed (bool): Whether to use compressed storage. Default is False.
        """
        super(BloomFilter, self).__init__()  # Calling the constructor of the superclass 'set'
        self.size = size
        self.hash_count = hash_count  # hash_count = size * ln(2) / num_elements
        self.compressed = compressed
        
        # Initialize either bit_array or compressed_bit_array, not both
        if compressed:
            self.compressed_bit_array = ""
            self.bit_array = None
        else:
            self.bit_array = bitarray(size)
            self.bit_array.setall(0)  # Initialize all bits to 0
            self.compressed_bit_array = None

    def __len__(self):
        """ Returns the size of the binary vector. """
        return self.size

    def __iter__(self):
        """ Makes the Bloom Filter iterable. """
        self._ensure_uncompressed()
        return iter(self.bit_array)

    def _ensure_uncompressed(self):
        """Ensure the bloom filter is in uncompressed state for operations."""
        if self.compressed:
            self.decompress()

    def _ensure_compressed(self):
        """Ensure the bloom filter is in compressed state for storage."""
        if not self.compressed:
            self.compress()

    def compress(self):
        """
        Compress the bit array and free up memory.
        
        After compression, self.bit_array becomes None and self.compressed_bit_array
        contains the compressed data.
        """
        if self.compressed or self.bit_array is None:
            return
            
        # Convert bitarray to bytes
        bit_bytes = self.bit_array.tobytes()
        
        # Compress using zlib
        compressed_data = zlib.compress(bit_bytes)
        
        # Encode as base64 for safe storage/transmission
        self.compressed_bit_array = base64.b64encode(compressed_data).decode('utf-8')
        
        # Free up memory
        self.bit_array = None
        self.compressed = True

    def decompress(self):
        """
        Decompress the bit array for operations.
        
        After decompression, self.compressed_bit_array becomes None and self.bit_array
        contains the uncompressed data.
        """
        if not self.compressed or self.compressed_bit_array is None:
            return
            
        try:
            # Decode from base64
            compressed_data = base64.b64decode(self.compressed_bit_array.encode('utf-8'))
            
            # Decompress using zlib
            bit_bytes = zlib.decompress(compressed_data)
            
            # Convert back to bitarray
            self.bit_array = bitarray()
            self.bit_array.frombytes(bit_bytes)
            
            # Free up memory
            self.compressed_bit_array = None
            self.compressed = False
        except (zlib.error, base64.binascii.Error):
            # If decompression fails, create a fresh bitarray
            self.bit_array = bitarray(self.size)
            self.bit_array.setall(0)
            self.compressed_bit_array = None
            self.compressed = False

    def get_compression_ratio(self):
        """
        Calculate the compression ratio for the current bit array.
        
        Returns:
            float: Compression ratio (original size / compressed size)
        """
        if not self.compressed:
            self._ensure_compressed()
            
        original_size = (self.size + 7) // 8  # Convert bits to bytes
        compressed_size = len(self.compressed_bit_array.encode('utf-8'))
        
        if compressed_size == 0:
            return float('inf')
        
        return original_size / compressed_size

    def get_statistics(self):
        """
        Get statistics about the bit array including density and compression info.
        
        Returns:
            dict: Dictionary containing bit array statistics
        """
        total_bits = self.size
        
        # Ensure uncompressed for density calculation
        was_compressed = self.compressed
        if was_compressed:
            self._ensure_uncompressed()
            
        set_bits = sum(1 for bit in self.bit_array if bit == 1)
        density = set_bits / total_bits if total_bits > 0 else 0
        compression_ratio = self.get_compression_ratio()
        
        # Restore original state
        if was_compressed:
            self._ensure_compressed()
        
        return {
            'total_bits': total_bits,
            'set_bits': set_bits,
            'unset_bits': total_bits - set_bits,
            'density': density,
            'compression_ratio': compression_ratio,
            'compressed_storage': self.compressed
        }

    def add(self, item):
        """
        Adds an item to the Bloom Filter.

        Parameters:
            item: The item to be added to the Bloom Filter.
        """
        self._ensure_uncompressed()
        
        for ii in range(self.hash_count):
            index = mmh3.hash(item, ii) % self.size  # Calculate the bit position to set
            self.bit_array[index] = 1  # Set the bit at the calculated position

        return self

    def __contains__(self, item):
        """
        Checks if an item is in the Bloom Filter.

        Parameters:
            item: The item to check for in the Bloom Filter.

        Returns:
            bool: True if the item might be in the filter, False if it's definitely not.
        """
        self._ensure_uncompressed()
        
        for ii in range(self.hash_count):
            index = mmh3.hash(item, ii) % self.size
            if self.bit_array[index] == 0:
                return False  # Item is definitely not in the filter

        return True  # Item might be in the filter (subject to false positives)

import json

class BloomFilterEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BloomFilter):
            # Ensure compressed storage for serialization
            obj._ensure_compressed()
            return {
                'size': obj.size,
                'hash_count': obj.hash_count,
                'compressed_bit_array': obj.compressed_bit_array,
                'compressed': obj.compressed,
                '__class__': obj.__class__.__name__,
                '__module__': obj.__module__
            }
        return json.JSONEncoder.default(self, obj)


def bloom_decoder(dct):
    """
    JSON decoder for BloomFilter that handles compressed data.
    
    Parameters:
        dct (dict): Dictionary to decode
        
    Returns:
        BloomFilter or dict: Decoded BloomFilter or original dict
    """
    if dct.get('__class__') == 'BloomFilter':
        # Create a new BloomFilter with the same parameters and compressed state
        bloom = BloomFilter(dct['size'], dct['hash_count'], compressed=dct.get('compressed', False))
        
        # Set the compressed data if available
        if 'compressed_bit_array' in dct and dct['compressed_bit_array'] is not None:
            bloom.compressed_bit_array = dct['compressed_bit_array']
            bloom.compressed = True
            bloom.bit_array = None
        
        return bloom
    return dct
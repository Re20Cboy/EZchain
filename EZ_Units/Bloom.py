from bitarray import bitarray
import mmh3

class BloomFilter(set):  # Inherits from the set class
    """
    A Bloom Filter implementation.

    Attributes:
        size (int): Length of the binary vector.
        hash_count (int): Number of hash functions.
    
    The number of hash functions should satisfy:
    (hash_count = binary_vector_length * ln(2) / number_of_elements_inserted)
    """
    def __init__(self, size=1024 * 1024, hash_count=5):
        """
        Initializes the Bloom Filter with a given size and hash count.

        Parameters:
            size (int): The size of the bit array. Default is 1024 * 1024.
            hash_count (int): The number of hash functions to use. Default is 5.
        """
        super(BloomFilter, self).__init__()  # Calling the constructor of the superclass 'set'
        self.bit_array = bitarray(size)
        self.bit_array.setall(0)  # Initialize all bits to 0
        self.size = size
        self.hash_count = hash_count  # hash_count = size * ln(2) / num_elements

    def __len__(self):
        """ Returns the size of the binary vector. """
        return self.size

    def __iter__(self):
        """ Makes the Bloom Filter iterable. """
        return iter(self.bit_array)

    def add(self, item):
        """
        Adds an item to the Bloom Filter.

        Parameters:
            item: The item to be added to the Bloom Filter.
        """
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
        for ii in range(self.hash_count):
            index = mmh3.hash(item, ii) % self.size
            if self.bit_array[index] == 0:
                return False  # Item is definitely not in the filter

        return True  # Item might be in the filter (subject to false positives)

import json

class BloomFilterEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BloomFilter):
            return {
                'size': obj.size,
                'hash_count': obj.hash_count,
                'bit_array': list(obj.bit_array),
                '__class__': obj.__class__.__name__,
                '__module__': obj.__module__
            }
        return json.JSONEncoder.default(self, obj)


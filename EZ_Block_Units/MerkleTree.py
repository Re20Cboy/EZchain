import copy
import random
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from EZ_Tool_Box.Hash import sha256_hash
import hashlib

# TODO: 默克尔树构造前的数据类型检查。

class MerkleTreeNode:
    def __init__(self, left, right, value, content=None, path=[], leaf_index=None):
        self.left = left
        self.right = right
        self.value = value
        self.content = content
        self.path = path
        self.leaf_index = leaf_index
        self.father = None

    def __str__(self):
        return str(self.value)


class MerkleTree:
    def __init__(self, values, is_genesis_block=False):
        self.leaves = []
        self.prf_list = None
        self.build_tree(values, is_genesis_block)

    def build_tree(self, leaves, is_genesis_block):
        leaves = [MerkleTreeNode(None, None, sha256_hash(e), e, leaf_index=index) for index, e in
                  enumerate(leaves, start=0)]

        for item in leaves:
            self.leaves.append(item)

        if not leaves:
            self.root = None
            return

        if is_genesis_block:
            self.root = leaves[0]
            return

        org_leaves_len = len(leaves)
        pop_leave_num = 0
        prf_list = []

        while len(leaves) > 1:
            length = len(leaves)
            for i in range(length // 2):
                if leaves[0].content is not None:
                    leaves[0].path = [pop_leave_num]
                    pop_leave_num += 1
                left = leaves.pop(0)
                if leaves[0].content is not None:
                    leaves[0].path = [pop_leave_num]
                    pop_leave_num += 1
                right = leaves.pop(0)
                value = sha256_hash(left.value + right.value)
                com_path = left.path + right.path
                left.path = com_path
                right.path = com_path
                new_mtree_node = MerkleTreeNode(left, right, value, path=com_path)
                left.father = new_mtree_node
                right.father = new_mtree_node
                leaves.append(new_mtree_node)
            if length % 2 == 1:
                leaves.append(leaves.pop(0))

        self.root = leaves[0]

        tmp_list = []
        for i in range(org_leaves_len):
            prf_list.append(copy.deepcopy(tmp_list))

        def add_unit_prf_list(tmp_prf_list, now_node, round_index):
            father = now_node.father
            father_right_child = father.right
            father_left_child = father.left
            another_child = None
            if father_right_child == now_node:
                another_child = father_left_child
            if father_left_child == now_node:
                another_child = father_right_child
            tmp_prf_list[round_index].append(another_child.value)
            tmp_prf_list[round_index].append(father.value)

        for leaf in self.leaves:
            prf_list[leaf.leaf_index].append(leaf.value)
            now_node = leaf
            while now_node != self.root:
                add_unit_prf_list(tmp_prf_list=prf_list, now_node=now_node, round_index=leaf.leaf_index)
                now_node = now_node.father

        self.prf_list = prf_list

    def get_root_hash(self):
        return self.root.value

    def check_tree(self, node=None):
        if node is None:
            node = self.root
        if node.left is not None and node.right is not None:
            if node.value != sha256_hash(node.left.value + node.right.value):
                return False
            else:
                return (self.check_tree(node=node.left) and self.check_tree(node=node.right))
        else:
            if node.value != sha256_hash(node.content):
                return False
        return True

    """def find_leaves_num(self, node):
        if node.content is None:
            self.find_leaves_num(node.left)
            self.find_leaves_num(node.right)
        else:
            self.test_num += 1

    def print_tree(self, node):
        if node is not None:
            if node.left is not None:
                print("Left: " + str(node.left))
                print("Right: " + str(node.right))
            else:
                print("Input")
            print("Value: " + str(node.value))
            print("")
            self.print_tree(node.left)
            self.print_tree(node.right)"""
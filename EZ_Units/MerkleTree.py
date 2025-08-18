import hashlib
import random
import copy


class MTreeProof:
    def __init__(self, MTPrfList=[]):
        self.MTPrfList = MTPrfList

    def checkPrf(self, accTxnsDigest, trueRoot):  # accTxns为待检查的账户交易集合. trueRoot是公链上的mTree root信息
        def hash(val):
            if type(val) == str:
                return hashlib.sha256(val.encode("utf-8")).hexdigest()
            else:
                return hashlib.sha256(val).hexdigest()

        # check_flag is used for de-bug
        check_flag = True
        hashedEncodeAccTxns = hash(accTxnsDigest)

        if len(self.MTPrfList) == 1:
            # this mTree proof only includes one acc_txn
            if (hashedEncodeAccTxns != self.MTPrfList[0] or trueRoot != self.MTPrfList[0] or
                    trueRoot != hashedEncodeAccTxns):
                check_flag = False
            return check_flag

        if hashedEncodeAccTxns != self.MTPrfList[0] and hashedEncodeAccTxns != self.MTPrfList[1]:
            check_flag = False
            #return False
        if self.MTPrfList[-1] != trueRoot:
            check_flag = False
            #return False
        lastHash = None
        for i in range(len(self.MTPrfList) // 2):
            lastHash = self.MTPrfList[2 * i + 2]
            if hash(self.MTPrfList[2 * i] + self.MTPrfList[2 * i + 1]) != lastHash and hash(
                    self.MTPrfList[2 * i + 1] + self.MTPrfList[2 * i]) != lastHash:
                check_flag = False
                #return False
        if lastHash != self.MTPrfList[-1]:
            check_flag = False
            #return False
        return check_flag
        #return True


class MerkleTreeNode:
    def __init__(self, left, right, value, content=None, path=[], leafIndex=None):
        self.left = left
        self.right = right
        self.value = value
        self.content = content
        self.path = path
        self.leafIndex = leafIndex  # 叶子节点的编号，用于跟踪叶子节点，便于制造prfList
        self.father = None  # 用于记录节点的父亲节点

    def hash(val):  # val is self
        # return hashlib.sha256(val.encode("utf-8")).hexdigest()
        if type(val) == str:
            return hashlib.sha256(val.encode("utf-8")).hexdigest()
        else:
            return hashlib.sha256(val).hexdigest()

    def __str__(self):
        return (str(self.value))


class MerkleTree:
    def __init__(self, values, isGenesisBlcok=False):
        self.leaves = []
        self.prfList = None  # 这里的prf是针对每轮每个参与交易的account产生一个proof list
        self.buildTree(values, isGenesisBlcok)

    def buildTree(self, leaves, isGenesisBlcok):
        leaves = [MerkleTreeNode(None, None, MerkleTreeNode.hash(e), e, leafIndex=index) for index, e in
                enumerate(leaves, start=0)]

        for item in leaves:
            self.leaves.append(item)  # 记录叶子节点的备份

        if isGenesisBlcok:
            self.root = leaves[0]  # 创世块的仅记录树根信息
            return
        OrgLeavesLen = len(leaves)  # 原始AccTxns的长度
        popLeaveNum = 0  # 记录生成mTree时pop了多少叶子节点
        PrfList = []  # 记录mTree的生成路径用于追踪以生成prf

        while len(leaves) > 1:
            length = len(leaves)
            for i in range(length // 2):
                if leaves[0].content != None:  # 是叶子节点
                    leaves[0].path = [popLeaveNum]  # 用.append添加会造成所有节点的path都同步变化！！# 可能是python的指针机制导致的
                    popLeaveNum += 1
                left = leaves.pop(0)
                if leaves[0].content != None:  # 是叶子节点
                    leaves[0].path = [popLeaveNum]
                    popLeaveNum += 1
                right = leaves.pop(0)
                value: str = MerkleTreeNode.hash(left.value + right.value)
                comPath = left.path + right.path
                left.path = comPath
                right.path = comPath
                newMTreeNode = MerkleTreeNode(left, right, value, path=comPath)
                left.father = newMTreeNode  # 添加父节点信息
                right.father = newMTreeNode  # 添加父节点信息
                leaves.append(newMTreeNode)
            if length % 2 == 1:
                leaves.append(leaves.pop(0))

        self.root = leaves[0]

        # 对每个accTxns生成对应的的proof trace
        tmpList = []
        for i in range(OrgLeavesLen):  # 添加root节点到所有prflist中
            PrfList.append(copy.deepcopy(tmpList))

        def addUnitPrfList(tmpPrfList, nowNode, roundIndex):
            father = nowNode.father
            fatherRightChild = father.right
            fatherLeftChild = father.left
            anotherChild = None
            if fatherRightChild == nowNode:
                anotherChild = fatherLeftChild
            if fatherLeftChild == nowNode:
                anotherChild = fatherRightChild
            tmpPrfList[roundIndex].append(anotherChild.value)
            tmpPrfList[roundIndex].append(father.value)

        for leaf in self.leaves:
            # 添加叶子节点
            PrfList[leaf.leafIndex].append(leaf.value)
            nowNode = leaf
            while nowNode != self.root:
                addUnitPrfList(tmpPrfList=PrfList, nowNode=nowNode, roundIndex=leaf.leafIndex)
                nowNode = nowNode.father

        """
        def add_given_path_2_prfList(node, givenIndex):
            if node.left is not None and node.right is not None:
                add_given_path_2_prfList(node.left, givenIndex)
                add_given_path_2_prfList(node.right, givenIndex)
            if givenIndex in node.path:
                PrfList[givenIndex].append(node.value)

        for leafIndex in range(OrgLeavesLen):
            add_given_path_2_prfList(self.root.left, leafIndex)
            add_given_path_2_prfList(self.root.right, leafIndex)
            PrfList[leafIndex].append(copy.deepcopy(self.root.value))
        """

        self.prfList = PrfList

    # 测试mTree的叶子节点数
    def find_leaves_num(self, node):  # 调用时赋node = self.root
        if node.content is None:
            self.find_leaves_num(node.left)
            self.find_leaves_num(node.right)
        else:
            self.testNum += 1

    def printTree(self, node) -> None:
        if node != None:
            if node.left != None:
                print("Left: " + str(node.left))
                print("Right: " + str(node.right))
            else:
                print("Input")
            print("Value: " + str(node.value))
            print("")
            self.printTree(node.left)
            self.printTree(node.right)

    def getRootHash(self) -> str:
        return self.root.value

    def checkTree(self, node=None):
        if node is None:
            node = self.root
        if node.left != None and node.right != None:  # 不是叶子节点
            # tmp = MerkleTreeNode.hash(node.left.value + node.right.value)
            # tmp2 = node.value
            if node.value != MerkleTreeNode.hash(node.left.value + node.right.value):
                return False
            else:
                return (self.checkTree(node=node.left) and self.checkTree(node=node.right))
        else:  # 是叶子节点
            if node.value != MerkleTreeNode.hash(node.content):
                return False
        return True


def generate_signature(address):
    # 生成随机数
    random_number = random.randint(1, 100000)
    # 将随机数与地址连接起来
    data = str(random_number) + str(address)
    # 使用SHA256哈希函数计算数据的摘要
    hash_object = hashlib.sha256(data.encode())
    signature = hash_object.hexdigest()
    return signature


def generate_random_hex(length):
    hex_digits = "0123456789ABCDEF"
    hex_number = "0x"
    for _ in range(length):
        hex_number += random.choice(hex_digits)
    return hex_number


def sort_and_get_positions(A):
    sorted_A = sorted(A)
    positions = [sorted_A.index(x) for x in A]
    return positions
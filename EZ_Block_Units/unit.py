from .transaction_pool import txnsPool
from .checkpoint_manager import checkedVPBList
from .proof_system import ProofUnit, Proof
from .value_handling import Value
from .merkle_tree import MTreeProof, MerkleTreeNode, MerkleTree, generate_signature, generate_random_hex, sort_and_get_positions
from .utils import generate_signature, generate_random_hex, sort_and_get_positions


if __name__ == "__main__":
    elems = ['1', '2', '3', '4', '5', '6']
    print('构造树')
    mtree = MerkleTree(elems)
    print('打印根哈希值')
    print("Root Hash: " + mtree.getRootHash() + "\n")
    print('打印默克尔树')
    mtree.printTree(mtree.root)
    print('打印所有proof')
    print(mtree.prfList)
    prf = MTreeProof(MTPrfList=mtree.prfList)

    print('======================')
    v_begin = generate_random_hex(65)
    print("v_begin:" + v_begin)
    v_num = 777
    print("v_num:" + str(v_num))
    v = Value(v_begin, v_num)
    print("v_end:" + v.endIndex)
    traget_num = 9999
    t = Value(v.getEndIndex(v.endIndex, 0), traget_num)
    flag1 = v.checkValue()
    flag2 = v.isInValue(t)
    print("flag1:" + str(flag1))
    print("flag2:" + str(flag2))
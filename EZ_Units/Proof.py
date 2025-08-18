class ProofUnit:  # 一个值在一个区块内的证明
    def __init__(self, owner, ownerAccTxnsList, ownerMTreePrfList):
        self.owner = owner
        self.ownerAccTxnsList = ownerAccTxnsList  # 在此区块内的ownTxns
        self.ownerMTreePrfList = ownerMTreePrfList  # ownTxns对应的mTreePrf

    def print_proof_unit(self):
        ownerMTreePrfList_str = ''
        for index, item in enumerate(self.ownerMTreePrfList):
            ownerMTreePrfList_str += '  ' + str(index) + ': ' + str(item) + '\n'
        print('owner: ' + str(self.owner) + '; ownerAccTxnsList: ' + str(self.ownerAccTxnsList))
        print('ownerMTreePrfList: ' + '\n' + ownerMTreePrfList_str)


class Proof:
    def __init__(self, prfList):
        self.prfList = prfList

    def add_prf_unit(self, prfUint):
        self.prfList.append(prfUint)

    def add_prf_unit_dst(self, prfUnit, add_position):
        self.prfList.insert(add_position, prfUnit)

    def get_latest_prf_unit_owner_dst(self):
        return self.prfList[-1].owner

    def print_proof(self):
        for index, item in enumerate(self.prfList):
            print('#'+str(index)+' prf_unit: ')
            item.print_proof_unit()
            print('--------------------')
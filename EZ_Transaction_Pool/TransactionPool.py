import copy
import transaction


class TxnPool:
    def __init__(self):
        self.pool = []  # [[(accTxn's Digest, acc's sig for hash, acc's addr, acc's ID), ...], ...]
        self.sender_id = []  # list of acc nodes' uuid

    def freshPool(self, accounts, accTxns):
        # this func is used for NON-DST mode only
        for i in range(len(accTxns)):
            accTxns[i].sig_accTxn(accounts[i].privateKey)  # 对accTxn进行签名
            self.pool.append(copy.deepcopy((accTxns[i].Digest, accTxns[i].Signature, accounts[i].addr, accounts[i].id)))

    def add_acc_txns_package_dst(self, acc_txns_package, uuid):
        # this func is designed for DST mode.
        # this func add the acc_txns_package & acc's uuid to self txns pool
        # the txns pool's form is :
        # self.sender_id = [uuid_1, uuid_2, uuid_3, ...]
        # self.pool = [[package_1_1, package_1_2, ...],[package_2_1, package_2_2, ...],[...], ...],
        # where package_i_j (j=1,2,3, ...) is sent by uuid_i.

        if self.sender_id == []:
            # no package recv, thus accept this package directly
            self.pool.append([acc_txns_package])
            self.sender_id.append(uuid)
        else:
            index_flag = None
            for index, send_uuid in enumerate(self.sender_id):
                if send_uuid == uuid:
                    index_flag = index
            if index_flag == None:
                # this uuid is new
                self.sender_id.append(uuid)
                self.pool.append([acc_txns_package])
            else:
                self.pool[index_flag].append(acc_txns_package)

    def get_packages_for_new_block_dst(self):
        # this func return a list of packages, which are built for the new block body
        lst_packages = []
        for acc_packages in self.pool:
            # pick the oldest package (i.e., acc_packages[0]), since it wait for the longest time.
            if acc_packages != []:
                # this acc_packages is not empty.
                lst_packages.append(acc_packages[0])
        return lst_packages

    def check_is_repeated_package(self, acc_txns_package, uuid):
        if self.txns_pool_is_empty():
            # if the pool is empty, this package must not be repeated.
            return False
        index_of_uuid = None
        for index, item in enumerate(self.sender_id):
            if item == uuid:
                index_of_uuid = index
        if index_of_uuid != None and self.pool[index_of_uuid] != []:
            for item in self.pool[index_of_uuid]:
                # item & acc_txns_package=(digest, sig, addr, global_id)
                if item[0] == acc_txns_package[0]:
                    return True
        return False

    def get_packages_num(self):
        return len(self.pool)

    def txns_pool_is_empty(self):
        if self.sender_id == []:
            return True
        for acc_packages in self.pool:
            if acc_packages != []:
                return False
        return True

    def clearPool(self):
        # this func is used for NON-DST mode
        self.pool = []
        self.sender_id = []

    def del_all_packages_in_pool(self):
        # this func del all packages in the txns pool,
        # but remains the send_id list.
        for acc_packages in self.pool:
            acc_packages.clear()

    def clear_pool_dst(self, acc_digests):
        # Logic of flash self txns pool:
        # if new block mined by other con node, self should delete the same package in local txns pool,
        # if self mine success, delete all package in the new block.

        # del_lst shape as {1:[1,3,6], 2:[3,5], ...}, where
        # 1:[1,3,6] means del self.pool[1][1], [1][3] and [1][6]

        del_lst = {}
        for acc_digest in acc_digests:
            for index_1, acc_packages in enumerate(self.pool):
                for index_2, acc_package in enumerate(acc_packages):
                    if acc_package[0] == acc_digest:
                        if index_1 in del_lst:
                            del_lst[index_1].append(index_2)
                        else:
                            del_lst[index_1] = [index_2]

        # reverse all del list, for correct delete
        for key, value in del_lst.items():
            del_lst[key] = reversed(value)

        # del the package in the pool
        for key, value in del_lst.items():
            if value != []:
                for del_index in value:
                    del self.pool[key][del_index]

    """def print_tnxs_pool_dst(self):
        # show the txns pool
        for index, uuid in enumerate(self.sender_id):
            print(str(uuid) + ': ')
            print(self.pool[index])
            print('-----------')"""
import copy


class CheckedVPBList:
    def __init__(self):
        self.VPBCheckPoints = []

    def findCKviaVPB(self, VPB):
        # Input VPB and check if the V of this VPB is included in the checkpoint.
        # Note that it should be an "inclusion" relationship (i.e., checkpoint includes this value).

        # todo: re-write this func in dst mode, when fork appear, which need more blocks to confirm a txn.
        #  the logic of find-ck should be re-build.

        value = VPB[0]
        returnList = []
        indexList = []
        if self.VPBCheckPoints != []:
            for index, ck in enumerate(self.VPBCheckPoints):
                # un-package this vpb-ck
                ckValue = ck[0]
                ckOwner = ck[1]
                ckBIndex = ck[2]
                # check inclusion relationship between ck and value
                if ckValue.isInValue(value):
                    returnList.append((ckOwner, ckBIndex))
                    indexList.append(index)
            if len(returnList) > 1:
                raise ValueError("more than 1 ck is found !!!")
        return returnList

    def fresh_local_vpb_check_point_dst(self, will_sent_vpb_pairs):
        for vpb in will_sent_vpb_pairs:
            value = vpb[0]
            valuePrf = vpb[1].prfList
            blockIndex = vpb[2]
            LatestPrfUnit = valuePrf[-1]
            LatestOwner = LatestPrfUnit.owner

            if self.VPBCheckPoints != []:
                newVPBCP = [value, LatestOwner, blockIndex]
                RestVPBCPs = None
                delIndex = None
                for index, VPBCP in enumerate(self.VPBCheckPoints, start=0):
                    V = VPBCP[0]
                    VOwner = VPBCP[1]
                    BIndex = VPBCP[2]
                    intersectValueReslut = V.getIntersectValue(value)
                    if intersectValueReslut != None:
                        # The value in the newly held VPB intersects with the original checkpoint (v)
                        # and needs to be processed before adding a checkpoint
                        if delIndex:
                            raise ValueError('delIndex Err: There are multiple delIndices!')
                        IntersectValue, RestValues = intersectValueReslut
                        delIndex = index
                        RestVPBCPs = []
                        if RestValues != []:
                            for item in RestValues:
                                tmpRestVPBCP = [item, VOwner, BIndex]
                                RestVPBCPs.append(tmpRestVPBCP)
                        break
                if RestVPBCPs != None:
                    # If RestVPBCPs=[], it means that the entire value
                    # needs to be updated without splitting the remaining parts
                    self.VPBCheckPoints.append(copy.deepcopy(newVPBCP))
                    for item in RestVPBCPs:
                        self.VPBCheckPoints.append(copy.deepcopy(item))
                    # Delete split check points
                    del self.VPBCheckPoints[delIndex]
                else:  # This value is completely "foreign", i.e., "first time seen".
                    self.VPBCheckPoints.append(copy.deepcopy(newVPBCP))
            else:  # Add the first batch of VPB checkpoints
                VPBCP = [value, LatestOwner, blockIndex]
                self.VPBCheckPoints.append(copy.deepcopy(VPBCP))

    def addAndFreshCheckPoint(self, VPBPairs):
        for VPB in VPBPairs:
            value = VPB[0]
            valuePrf = VPB[1].prfList
            blockIndex = VPB[2]
            LatestPrfUnit = valuePrf[-1]
            LatestOwner = LatestPrfUnit.owner

            if self.VPBCheckPoints != []:
                newVPBCP = [value, LatestOwner, blockIndex]
                RestVPBCPs = None
                delIndex = None
                for index, VPBCP in enumerate(self.VPBCheckPoints, start=0):
                    V = VPBCP[0]
                    VOwner = VPBCP[1]
                    BIndex = VPBCP[2]
                    intersectValueReslut = V.getIntersectValue(value)
                    if intersectValueReslut != None:  # 新一轮持有的VPB中的value 和 原有的检查点（v） 有交集，需要处理后加入检查点
                        if delIndex:
                            raise ValueError('delIndex Err: 有多数个delIndex！')
                        IntersectValue, RestValues = intersectValueReslut
                        delIndex = index
                        RestVPBCPs = []
                        if RestValues != []:
                            for item in RestValues:
                                tmpRestVPBCP = [item, VOwner, BIndex]
                                RestVPBCPs.append(tmpRestVPBCP)
                        break
                if RestVPBCPs != None:  # 若RestVPBCPs = []则说明整个值都要更新，没有拆分剩下的部分
                    self.VPBCheckPoints.append(copy.deepcopy(newVPBCP))
                    for item in RestVPBCPs:
                        self.VPBCheckPoints.append(copy.deepcopy(item))
                    # 删除被拆分的check points
                    del self.VPBCheckPoints[delIndex]
                else:  # 说明此值完全是"外来"，"第一次见到"。
                    self.VPBCheckPoints.append(copy.deepcopy(newVPBCP))

            else:  # 添加第一批VPB检查点
                VPBCP = [value, LatestOwner, blockIndex]
                self.VPBCheckPoints.append(copy.deepcopy(VPBCP))
#ifndef __DEMO_NODE_H
#define __DEMO_NODE_H

#include <sstream>
#include <string>
#include <deque>
#include <map>
#include <set>
#include <unordered_map>
#include <malloc.h>

#include "block.h"
#include "msg.h"
#include "transaction.h"

namespace ezchain {

    class node
    {
        unsigned long N;  // 节点数
        unsigned long M;  // 委员会大小
        double n_v;  // 每个节点的初始资产数
        double T;  // 周期（epoch）
        double round = 600;  // 轮的预期间隔
        double k;  // 每个节点生成交易的速率
        double abstract_size = 0.2;  // 摘要大小
        int tx_size = 62.5;  // 交易大小
        int CCB_size = 1024; // CC块大小
        bool useCC;

        double gama_1 = 10;
        double gama_2 = 10;
        double gama_3 = 10;
        double gama_4 = 10;
        
        std::deque<cMessage *>              Inf_cc; // 用于存储等待CC算法的交易
        std::vector<size_t>                 Inf_sz; // Inf_CC的辅助工具
        std::set<std::string>               abs_set; // 用来收集abstract
        std::map<std::string, cMessage*>    sig_set; // 用来收集门限签名

        std::vector<std::string>                    tx_pool; //节点待发送的交易
        std::vector<ac_block*>              ac_chain; // ac链
        
        std::map<std::string, pc_block*>    pb_map; // 摘要交易集对，存储发送后等待确认的交易
        std::vector<std::string>              pb_chain; // 按序存放节点发起并已经上块的交易
        std::vector<Prf*>                   val_prf;  // 为持有的交易缓存prf
        std::set<unsigned long>             committee; // 当前轮committee
        
        cMessage* pow = nullptr;
        cMessage* gTimer =  nullptr;
        ac_block* cur_ac = nullptr;// 当前节点视角下最后一个块
        std::size_t ac_cur = 0;// 记录已经记录下来的ac链
        int gState = 0; // 临时使用
        unsigned long pID; // 当前节点视角下最后一个块的ID
        unsigned long pHigh;// 当前节点视角下最后一个块的高度
        bool in_committee = false; //
        bool in_CC = false; // 作为委员正在进行CC算法
        unsigned long leader_ID; // 当前epoch的Leader的ID
        unsigned long leader_ID_CC; //
        int block_epoch = 0; // 当前轮的出块数
        
    public:
        const unsigned long ID;
        cMessage* Inf_collect = nullptr;
        cc_block* cb_ptr = nullptr;

        node(const unsigned long ID);
        virtual ~node();
        void handleMessage(cMessage* msg);
        int genTX(cMessage* msg);
        int handlePow(cMessage* msg);
        int handleACBlock(cMessage* msg);
        int selfACBlock(ac_block* block);
        int sendInf();
        int packandVerifyInf(ac_block* block);
        int handleRecvtx(cMessage* msg);
        bool GetOwner(Prf* prf, cMessage* t_msg, int state);
        bool getprfOwner(Prf* prf);
        bool getprfOwner(std::string tx_str, std::string prf_st, cMessage* c_msg, size_t idx);
        bool checkAbstract(unsigned long prev_high, unsigned long high, unsigned long oID, std::vector<TX*> &txs, std::string& txs_abs);
        bool prf_structure(Prf* prf);
        int handleTtimer(cMessage* T_msg);
        int initializeCC();
        int broadcastInf();
        int collectInf(cMessage* msg);
        int handleGama_1(cMessage* msg);
        cMessage* sendCCblock(int kind);
        int handleCCB_2(cMessage* msg);
        int handleGama_2(cMessage* msg);
        bool verify(INF* inf, std::string abstract);
        int signCCB(cMessage* c_msg);
        int handleSig(cMessage* msg);
        bool verifyThreholdSig();
        void getLeader(unsigned long cnt);
        int handleCCB_3(cMessage* msg);
        int handleGama_3(cMessage* msg);
        int handleCCB_4(cMessage* msg);
        int handleCCB(cMessage* msg);
        int statistic(staticticStruct* sta);
    };
}; // namespace


#endif // !__DEMO_NODE_H

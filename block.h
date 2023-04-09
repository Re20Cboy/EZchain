#ifndef __DEMO_BLOCK_H
#define __DEMO_BLOCK_H
#include <map>
#include <set>
#include <unordered_map>
#include <malloc.h>

//#include "transaction.h"

namespace ezchain {

    // personal chain 块
    class pc_block {
    public:
        unsigned long height = 0; // 在AC链上的位置
        //std::map<unsigned int, size_t> val_map; // 根据价值编号寻找对应的交易
        std::vector<std::string>  txs; //每个字符表示一个txn
        std::vector<std::string>  prfs;
        std::string txs_abstract;


        pc_block(unsigned long h) :height(h) {};
        pc_block() {};
        pc_block(std::string str);
        virtual ~pc_block() {
            for (auto t : txs) {
                t.~basic_string();
            }
            std::vector<std::string>().swap(txs);
            for (auto t : prfs) {
                t.~basic_string();
            }
            std::vector<std::string>().swap(prfs);
            //std::map<unsigned int, size_t>().swap(val_map);
            txs_abstract.~basic_string();
        }

        std::string block_2_str();
        
    };

    // AC块
    class ac_block {
    public:
        const unsigned int height; // 高度，也用来表示时刻
        const unsigned long ID;
        const unsigned long prev_ID;
        const unsigned int node_ID; // 出块节点ID
        const double time;
        unsigned int state = 0;
        ac_block* prev = nullptr;

        std::map<unsigned int, bool> node_filter; // 记录交易集的发起节点
        std::vector<std::string> A_vec; // 存储交易集对应的摘要A_i(x)

        ac_block(unsigned int height, unsigned long ID, unsigned long prev_ID, unsigned int node_ID, double time);
        virtual ~ac_block();

        std::string block_2_str();
        static ac_block* str_2_block(std::string str);
        static void record();
    };

    // CC块,存储的内容为无效交易的index
    class cc_block {
    public:
        unsigned int height; // 高度，也用来表示时刻
        unsigned long ID;
        unsigned long prev_ID; // 之前区块的ID 为0表示创始区块
        unsigned int node_ID; // 出块节点ID
        unsigned int acb_height; // 本轮中最后的acb块的高度
        int block_epoch; // 当前轮的出块数
        double time;
        int txn_cnt;
        cc_block* prev = nullptr;
        cc_block* next = nullptr;

        // 如果整个交易集非法，则int = -1,否则int 表示交易集对应在fail_txn中的坐标
        std::unordered_map<std::string, int> fail_txs; // 根据摘要记录所有存在失败交易的交易集
        std::vector<std::vector<std::string>> fail_txn; // 交易集-交易

        cc_block(unsigned int height, unsigned long ID, unsigned long prev_ID, unsigned int node_ID,
            unsigned int acb_height, int block_epoch, double time, int txn_cnt = 0);
        virtual ~cc_block();
        std::string block_2_str();
        void Clear();
        static cc_block* str_2_block(std::string str);
    };

    // 用于交换的
    class cc_exchange {
    public:
        unsigned int height; // 高度，也用来表示时刻
        unsigned long ID;
        unsigned long prev_ID; // 之前区块的ID 为0表示创始区块
        unsigned int node_ID; // 出块节点ID
        unsigned int acb_height; // 本轮中最后的acb块的高度
        int block_epoch; // 当前轮的出块数
        double time;
        std::vector<std::string> tx_prf_vec;// 上一个epoch中收集到的交易集合对应的pef


        cc_exchange(unsigned int height, unsigned long ID, unsigned long prev_ID, unsigned int node_ID,
            unsigned int acb_height, int block_epoch, double time);
        virtual ~cc_exchange();
        std::string block_2_str();
        static cc_exchange* str_2_block(std::string str);
    };

    //交易集
    class INF {
    public:
        std::string abs;
        const unsigned int node_ID;
        unsigned int height = NULL;
        std::vector<std::string> tx_prf_vec;

        INF(unsigned int node_ID);
        virtual ~INF();
        std::string inf_to_str();
        static INF* str_2_inf(std::string str);
        std::string getTxAbs();
        static std::string getTxAbs(std::string str);
    };

    //回执
    class receipt {
    public:
        const unsigned int sendID;//发送节点
        const unsigned int recvID; // 接收节点
        const unsigned int height;// 交易集所在的区块的高度
        std::vector<std::string> txs; // 交易集中的全部交易
        size_t tx_idx;
        std::string tx;
        std::string prf;

        receipt(const unsigned int sID, const unsigned int rID, const unsigned int h);
        std::string receipt_to_str();
        static receipt* str_to_receipt(std::string str);
        virtual ~receipt();
    };

    class sigclass {
    public:
        unsigned long ccb_ID;
        unsigned int sign_Node;
        unsigned int recv_Node;
        double time_Stamp;
        short int kind;

        sigclass(unsigned long cID,unsigned int sign, unsigned int recv, double time, short int k);
        virtual ~sigclass();
        std::string sig_to_str();
        static sigclass* str_to_sig(std::string str);
    };

    class sigclass2 {
        public:
        unsigned long ccb_id;
        
    };

    class staticticStruct // 用于进行统计
    {
    public:
        double time = 0;        //进行统计的时间
        int CCPT = 0;           //ccpt开销
        double ACC_storage = 0; //AC块所占据的存储开销
        double CCC_storage = 0; //CC块所占据的存储开销
        double PBC_storage = 0; //个人链所占据的存储开销

        staticticStruct() { return; };
        virtual ~staticticStruct() { ; };
    };
}

#endif // !__DEMO_BLOCK_H


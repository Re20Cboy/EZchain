#ifndef __DEMO_TRANSACTION_H
#define __DEMO_TRANSACTION_H

#include <sstream>
#include <string>
#include <map>
#include <set>
#include <unordered_map>
#include <malloc.h>

#include "block.h"

namespace ezchain {
    // 交易
    class TX {
    public:
        unsigned long tx_ID; // 交易ID
        unsigned long val; // 价值
        unsigned long owner_ID; // 发送方
        unsigned long recv_ID; // 接收方
        unsigned long acb_high = 0; //被哪个高度的ac块确认
        std::string prf_str;
        TX(unsigned long tID, unsigned long v, unsigned long oID, unsigned long rID);
        TX(std::string str);
        TX(TX* tx) {
            tx_ID = tx->tx_ID; // 交易ID
            val = tx->val; // 价值
            owner_ID = tx->owner_ID; // 发送方
            recv_ID = tx->recv_ID; // 接收方
            acb_high = tx->acb_high;
            prf_str = tx->prf_str;
        }

        TX* duo(TX* tx) {  return new TX(tx);};

        std::string tx_to_str() {
            std::string tx_str;
            tx_str += std::to_string(tx_ID);
            tx_str += ",";
            tx_str += std::to_string(val);
            tx_str += ",";
            tx_str += std::to_string(owner_ID);
            tx_str += ",";
            tx_str += std::to_string(acb_high);
            tx_str += ",";
            tx_str += std::to_string(recv_ID);
            tx_str += ";";
            tx_str += prf_str;
            return tx_str;
        }

        virtual ~TX() {
            prf_str.~basic_string();
        };
        // 检查交易的格式是否正确
        bool check(std::string tx_str);
    };

    // 交易证明，本质上是从上一个记录了价值转移的checkpoint开始的AC链上
    //所有和该价值相关的交易集的集合
    class Prf {
    public:
        unsigned long init_ID; // 初始持有者ID
        unsigned long init_high; // 创始块所在高度
        unsigned long val; // “价值”编号
        unsigned long tx_cnt;
        //    double amount; // 金额
        //  多个交易集
        std::vector<std::vector<TX *>> txs_vec;
        //  交易集所在区块高度
        std::vector<unsigned long> txs_h;
        //  用于初始化一个价值
        Prf(unsigned long iID, unsigned long v, unsigned long high = 0)
            :init_ID(iID), val(v), init_high(high) {
            tx_cnt = 0;
        };

        Prf(std::string str);
        std::string prf_to_str();
        void addtxs(std::vector<pc_block*>& pb_chain);
        void addtxs(std::vector<std::string>& pb_chain, unsigned long nodeID);
        int afterCC(unsigned long to);
        size_t tx_in_prf();

        virtual ~Prf() {
            std::vector<std::vector<TX*>> ().swap(txs_vec);
            std::vector<unsigned long> ().swap(txs_h);
        };

    };

    // 信息集合（交易集合和证明集合以及交易集的摘要，注意，摘要对应的是交易集而非Inf）
    class Inf {
    public:
        unsigned long owner_ID; // 发送方
        std::vector<TX> txs;
        std::vector<Prf> prfs; // 交易对应的证明的集合
        std::string abs;  // 交易集对应的摘要
        Inf(unsigned long oID, std::string a) :owner_ID(oID), abs(a) {};
        Inf(int oID, const char* a) {
            owner_ID = oID;
            std::string s(a);
            abs = s;
        };

        virtual ~Inf() {
            for (auto p : prfs) {
                p.~Prf();
            }
            std::vector<Prf>().swap(prfs);
            std::vector<TX>().swap(txs);
        };
    };

}
#endif



#include <sstream>
#include <string>
#include <map>
#include <set>
#include <unordered_map>
#include <malloc.h>
#include <iostream>

#include "transaction.h"
#include "global.h"
//#define light

namespace ezchain {
    TX::TX(unsigned long tID, unsigned long v, unsigned long oID, unsigned long rID) :tx_ID(tID), val(v), owner_ID(oID), recv_ID(rID) {
    };

    TX::TX(std::string str) {
        bool flag = true;
        size_t from = 0;
        size_t to = str.find_first_of(",");
        if (to == std::string::npos) flag = false;
        tx_ID = stoul(str.substr(from, to - from));
        from = to + 1;
        to = str.find_first_of(",", from);
        if (to == std::string::npos) flag = false;
        val = stoul(str.substr(from, to - from));
        from = to + 1;
        to = str.find_first_of(",", from);
        if (to == std::string::npos) flag = false;
        owner_ID = stoul(str.substr(from, to - from));
        from = to + 1;
        to = str.find_first_of(",", from);
        if (to == std::string::npos) flag = false;
        acb_high = stoul(str.substr(from, to - from));
        from = to + 1;
        to = str.find_first_of(";", from);
        if (to == std::string::npos) flag = false;
        recv_ID = stoul(str.substr(from, to - from));
        if (to != str.size() - 1 || !flag) {
            std::cout << "tx type Error" << std::endl << str << std::endl;
        }
        return;
    };

    // 检查交易的格式是否正确
    bool TX::check(std::string tx_str) {
        bool flag = true;
        size_t from = 0;
        size_t to = tx_str.find_first_of(",");
        if (to == std::string::npos) flag = false;
        from = to + 1;
        to = tx_str.find_first_of(",", from);
        if (to == std::string::npos) flag = false;

        from = to + 1;
        to = tx_str.find_first_of(",", from);
        if (to == std::string::npos) flag = false;

        from = to + 1;
        to = tx_str.find_first_of(",", from);
        if (to == std::string::npos) flag = false;

        from = to + 1;
        to = tx_str.find_first_of(";", from);
        if (to == std::string::npos) flag = false;

        if (to != tx_str.size() - 1 || !flag) {
            std::cout << "tx type Error" << std::endl << tx_str << std::endl;
            recordError(tx_type);
        }
        return flag;
    };

    // prf

    // 根据字符串还原一个价值
    Prf::Prf(std::string str) {
        tx_cnt = 0;
        //prf_str = str;
        size_t from = 0;
        size_t to = str.find_first_of(",", from);
        size_t vec_sz = stoul(str.substr(from, to - from));
        txs_vec.resize(vec_sz);
        txs_h.resize(vec_sz);
        from = to + 1;
        to = str.find_first_of(",", from);
        init_ID = stoul(str.substr(from, to - from));
        from = to + 1;
        to = str.find_first_of(",", from);
        init_high = stoul(str.substr(from, to - from));
        from = to + 1;
        to = str.find_first_of(";", from);
        val = stoul(str.substr(from, to - from));
        from = to + 1;
        for (size_t i = 0; i < vec_sz; i++) {
            size_t seg = str.find_first_of("/", from);
            while (from < seg) { // 录入交易集
                to = str.find_first_of(";", from);
                TX* t = new TX(str.substr(from, 1 + to - from));
                txs_vec.at(i).push_back(t);
                from = to + 1;
                tx_cnt++;
            }
            from = seg + 1;
            to = str.find_first_of("|", from);
            unsigned long h = stoul(str.substr(from, to - from));
            txs_h.at(i) = h;
            from = to + 1;
        }
        return;
    };

    /*
     * 根据prf输出对应的string格式用于方便传输message
     */
    std::string Prf::prf_to_str() {
        std::string prf_str;
        size_t sz = txs_vec.size();
        prf_str = std::to_string(sz);
        prf_str += ",";
        prf_str += std::to_string(init_ID);
        prf_str += ",";
        prf_str += std::to_string(init_high);
        prf_str += ",";
        prf_str += std::to_string(val);
        prf_str += ";";
        for (size_t i = 0; i < sz; i++) {
            for (size_t j = 0; j < txs_vec.at(i).size(); j++) {
                //if (txs_vec.at(i).at(j).check())
                    prf_str += txs_vec.at(i).at(j)->tx_to_str();
            }
            prf_str += "/";
            prf_str += std::to_string(txs_h.at(i));
            prf_str += "|";
        }
        prf_str += "-";
        prf_str += std::to_string(tx_cnt);
        if (prf_str == "") {
            recordError(error_type::empty_prf);
        }
        return prf_str;
    };

    //    发送者在发送证明之前调用，将接受到价值后到发送前这段时间内发送者所有的交易集附加到
    //    prf中(因为在次期间没有交易集包含本价值)
    void Prf::addtxs(std::vector<pc_block*>& pb_chain) {
        if (pb_chain.empty()) return;

        // 先找到已经记录的最后一个交易集所在的区块高度
        unsigned long last_high;
        if (txs_vec.empty()) {
            last_high = init_high;
        }
        else {
            size_t idx = txs_vec.size() - 1;
            last_high = txs_h.at(idx);
        }

        // 逆序遍历pb_chain,找到在该高度上的第一个交易集
        int pb_idx = pb_chain.size() - 1;
        bool flag = true;
        while (flag) {
            pc_block* b_ptr = pb_chain.at(pb_idx);

            // 因为同一个块上的所有相关交易集相邻，只需要找到第一个高度不足的交易集
            if (b_ptr->height < last_high || pb_idx == 0) {
                if (b_ptr->height < last_high)pb_idx++;
                while (pb_idx < pb_chain.size()) {
                    b_ptr = pb_chain.at(pb_idx);
                    std::vector<TX*> v;
                    for (auto it : b_ptr->txs) {
                        TX* tx = new TX(it);
                        v.push_back(tx);
                    }
                    if (v.empty()) {
                        pb_idx++;
                        continue;
                    }
                    txs_h.push_back(b_ptr->height);
                    txs_vec.push_back(v);
                    pb_idx++;
                }
                break;
            }
            pb_idx == 0 ? flag = false : pb_idx--;
        }
        tx_cnt = tx_in_prf();
        return;
    };

    //    发送者在发送证明之前调用，将接受到价值后到发送前这段时间内发送者所有的交易集附加到
    //    prf中(因为在次期间没有交易集包含本价值)
    void Prf::addtxs(std::vector<std::string>& pb_chain, unsigned long nodeID) {
        if (pb_chain.empty()) return;

        // 先找到已经记录的最后一个交易集所在的区块高度
        unsigned long last_high;
        if (txs_vec.empty()) {
            last_high = init_high;
        }
        else {
            size_t idx = txs_vec.size() - 1;
            last_high = txs_h.at(idx);
        }

        // 逆序遍历pb_chain,
        auto pb_idx = pb_chain.size() - 1;
        bool flag = true;
        while (flag) {
            const std::string key = pb_chain.at(pb_idx);
            std::string value;
            leveldb::Status status = PBDB->Get(leveldb::ReadOptions(), key, &value);
            assert(status.ok());
            pc_block b_ptr(value);
            key.~basic_string();
            value.~basic_string();

            // 因为同一个块上的所有相关交易集相邻，只需要找到第一个高度不足的交易集
            if (b_ptr.height < last_high || pb_idx == 0) {
                if (b_ptr.height < last_high)pb_idx++;
                while (pb_idx < pb_chain.size()) {
                    const std::string key = pb_chain.at(pb_idx);
                    std::string value;
                    leveldb::Status status = PBDB->Get(leveldb::ReadOptions(), key, &value);
                    assert(status.ok());
                    pc_block b_ptr(value);
                    std::vector<TX*> v;
                    for (auto it : b_ptr.txs) {
                        TX* tx = new TX(it);
                        v.push_back(tx);
                    }
                    if (v.empty()) {
                        pb_idx++;
                        continue;
                    }
                    txs_h.push_back(b_ptr.height);
                    txs_vec.push_back(v);
                    pb_idx++;
                }
                break;
            }
            pb_idx == 0 ? flag = false : pb_idx--;
        }
        tx_cnt = tx_in_prf();
        return;

    };

    /*
     *   持有者在每轮CC算法结束后调用，给定一个区间，如果prf中有交易集处于这一区间，
     *    选取其中最靠后的交易集，将其之前的交易集全部删除
     */
    int Prf::afterCC(unsigned long to) {// 给定本轮CC算法的起止区块高度
        if (txs_vec.empty()) return 0;
        size_t idx = txs_vec.size() - 1;
        // 至少保留一个交易集
        while (idx > 0) {
            unsigned long h = txs_h.at(idx);
            if (h < to) {
                // 删除该交易集之前的所有交易集
                txs_vec.erase(txs_vec.begin(), txs_vec.begin() + idx - 1);
                txs_h.erase(txs_h.begin(), txs_h.begin() + idx - 1);
                tx_cnt = tx_in_prf();
                if (txs_vec.empty() || *(txs_h.begin()) > to) {
                    recordError(after_cc);
                }
                return idx;
            }
            idx--;
        }
        tx_cnt = tx_in_prf();
        return idx;
    };

    // 统计prf中总共有多少条交易
    size_t Prf::tx_in_prf() {
        size_t cnt = 0;
        for (auto x : txs_vec) {
            cnt += x.size();
        }
        return cnt;
    };

}
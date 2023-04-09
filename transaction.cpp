
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

    // ��齻�׵ĸ�ʽ�Ƿ���ȷ
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

    // �����ַ�����ԭһ����ֵ
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
            while (from < seg) { // ¼�뽻�׼�
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
     * ����prf�����Ӧ��string��ʽ���ڷ��㴫��message
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

    //    �������ڷ���֤��֮ǰ���ã������ܵ���ֵ�󵽷���ǰ���ʱ���ڷ��������еĽ��׼����ӵ�
    //    prf��(��Ϊ�ڴ��ڼ�û�н��׼���������ֵ)
    void Prf::addtxs(std::vector<pc_block*>& pb_chain) {
        if (pb_chain.empty()) return;

        // ���ҵ��Ѿ���¼�����һ�����׼����ڵ�����߶�
        unsigned long last_high;
        if (txs_vec.empty()) {
            last_high = init_high;
        }
        else {
            size_t idx = txs_vec.size() - 1;
            last_high = txs_h.at(idx);
        }

        // �������pb_chain,�ҵ��ڸø߶��ϵĵ�һ�����׼�
        int pb_idx = pb_chain.size() - 1;
        bool flag = true;
        while (flag) {
            pc_block* b_ptr = pb_chain.at(pb_idx);

            // ��Ϊͬһ�����ϵ�������ؽ��׼����ڣ�ֻ��Ҫ�ҵ���һ���߶Ȳ���Ľ��׼�
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

    //    �������ڷ���֤��֮ǰ���ã������ܵ���ֵ�󵽷���ǰ���ʱ���ڷ��������еĽ��׼����ӵ�
    //    prf��(��Ϊ�ڴ��ڼ�û�н��׼���������ֵ)
    void Prf::addtxs(std::vector<std::string>& pb_chain, unsigned long nodeID) {
        if (pb_chain.empty()) return;

        // ���ҵ��Ѿ���¼�����һ�����׼����ڵ�����߶�
        unsigned long last_high;
        if (txs_vec.empty()) {
            last_high = init_high;
        }
        else {
            size_t idx = txs_vec.size() - 1;
            last_high = txs_h.at(idx);
        }

        // �������pb_chain,
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

            // ��Ϊͬһ�����ϵ�������ؽ��׼����ڣ�ֻ��Ҫ�ҵ���һ���߶Ȳ���Ľ��׼�
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
     *   ��������ÿ��CC�㷨��������ã�����һ�����䣬���prf���н��׼�������һ���䣬
     *    ѡȡ�������Ľ��׼�������֮ǰ�Ľ��׼�ȫ��ɾ��
     */
    int Prf::afterCC(unsigned long to) {// ��������CC�㷨����ֹ����߶�
        if (txs_vec.empty()) return 0;
        size_t idx = txs_vec.size() - 1;
        // ���ٱ���һ�����׼�
        while (idx > 0) {
            unsigned long h = txs_h.at(idx);
            if (h < to) {
                // ɾ���ý��׼�֮ǰ�����н��׼�
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

    // ͳ��prf���ܹ��ж���������
    size_t Prf::tx_in_prf() {
        size_t cnt = 0;
        for (auto x : txs_vec) {
            cnt += x.size();
        }
        return cnt;
    };

}
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
    // ����
    class TX {
    public:
        unsigned long tx_ID; // ����ID
        unsigned long val; // ��ֵ
        unsigned long owner_ID; // ���ͷ�
        unsigned long recv_ID; // ���շ�
        unsigned long acb_high = 0; //���ĸ��߶ȵ�ac��ȷ��
        std::string prf_str;
        TX(unsigned long tID, unsigned long v, unsigned long oID, unsigned long rID);
        TX(std::string str);
        TX(TX* tx) {
            tx_ID = tx->tx_ID; // ����ID
            val = tx->val; // ��ֵ
            owner_ID = tx->owner_ID; // ���ͷ�
            recv_ID = tx->recv_ID; // ���շ�
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
        // ��齻�׵ĸ�ʽ�Ƿ���ȷ
        bool check(std::string tx_str);
    };

    // ����֤�����������Ǵ���һ����¼�˼�ֵת�Ƶ�checkpoint��ʼ��AC����
    //���к͸ü�ֵ��صĽ��׼��ļ���
    class Prf {
    public:
        unsigned long init_ID; // ��ʼ������ID
        unsigned long init_high; // ��ʼ�����ڸ߶�
        unsigned long val; // ����ֵ�����
        unsigned long tx_cnt;
        //    double amount; // ���
        //  ������׼�
        std::vector<std::vector<TX *>> txs_vec;
        //  ���׼���������߶�
        std::vector<unsigned long> txs_h;
        //  ���ڳ�ʼ��һ����ֵ
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

    // ��Ϣ���ϣ����׼��Ϻ�֤�������Լ����׼���ժҪ��ע�⣬ժҪ��Ӧ���ǽ��׼�����Inf��
    class Inf {
    public:
        unsigned long owner_ID; // ���ͷ�
        std::vector<TX> txs;
        std::vector<Prf> prfs; // ���׶�Ӧ��֤���ļ���
        std::string abs;  // ���׼���Ӧ��ժҪ
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

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
        unsigned long N;  // �ڵ���
        unsigned long M;  // ίԱ���С
        double n_v;  // ÿ���ڵ�ĳ�ʼ�ʲ���
        double T;  // ���ڣ�epoch��
        double round = 600;  // �ֵ�Ԥ�ڼ��
        double k;  // ÿ���ڵ����ɽ��׵�����
        double abstract_size = 0.2;  // ժҪ��С
        int tx_size = 62.5;  // ���״�С
        int CCB_size = 1024; // CC���С
        bool useCC;

        double gama_1 = 10;
        double gama_2 = 10;
        double gama_3 = 10;
        double gama_4 = 10;
        
        std::deque<cMessage *>              Inf_cc; // ���ڴ洢�ȴ�CC�㷨�Ľ���
        std::vector<size_t>                 Inf_sz; // Inf_CC�ĸ�������
        std::set<std::string>               abs_set; // �����ռ�abstract
        std::map<std::string, cMessage*>    sig_set; // �����ռ�����ǩ��

        std::vector<std::string>                    tx_pool; //�ڵ�����͵Ľ���
        std::vector<ac_block*>              ac_chain; // ac��
        
        std::map<std::string, pc_block*>    pb_map; // ժҪ���׼��ԣ��洢���ͺ�ȴ�ȷ�ϵĽ���
        std::vector<std::string>              pb_chain; // �����Žڵ㷢���Ѿ��Ͽ�Ľ���
        std::vector<Prf*>                   val_prf;  // Ϊ���еĽ��׻���prf
        std::set<unsigned long>             committee; // ��ǰ��committee
        
        cMessage* pow = nullptr;
        cMessage* gTimer =  nullptr;
        ac_block* cur_ac = nullptr;// ��ǰ�ڵ��ӽ������һ����
        std::size_t ac_cur = 0;// ��¼�Ѿ���¼������ac��
        int gState = 0; // ��ʱʹ��
        unsigned long pID; // ��ǰ�ڵ��ӽ������һ�����ID
        unsigned long pHigh;// ��ǰ�ڵ��ӽ������һ����ĸ߶�
        bool in_committee = false; //
        bool in_CC = false; // ��ΪίԱ���ڽ���CC�㷨
        unsigned long leader_ID; // ��ǰepoch��Leader��ID
        unsigned long leader_ID_CC; //
        int block_epoch = 0; // ��ǰ�ֵĳ�����
        
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
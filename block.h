#ifndef __DEMO_BLOCK_H
#define __DEMO_BLOCK_H
#include <map>
#include <set>
#include <unordered_map>
#include <malloc.h>

//#include "transaction.h"

namespace ezchain {

    // personal chain ��
    class pc_block {
    public:
        unsigned long height = 0; // ��AC���ϵ�λ��
        //std::map<unsigned int, size_t> val_map; // ���ݼ�ֵ���Ѱ�Ҷ�Ӧ�Ľ���
        std::vector<std::string>  txs; //ÿ���ַ���ʾһ��txn
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

    // AC��
    class ac_block {
    public:
        const unsigned int height; // �߶ȣ�Ҳ������ʾʱ��
        const unsigned long ID;
        const unsigned long prev_ID;
        const unsigned int node_ID; // ����ڵ�ID
        const double time;
        unsigned int state = 0;
        ac_block* prev = nullptr;

        std::map<unsigned int, bool> node_filter; // ��¼���׼��ķ���ڵ�
        std::vector<std::string> A_vec; // �洢���׼���Ӧ��ժҪA_i(x)

        ac_block(unsigned int height, unsigned long ID, unsigned long prev_ID, unsigned int node_ID, double time);
        virtual ~ac_block();

        std::string block_2_str();
        static ac_block* str_2_block(std::string str);
        static void record();
    };

    // CC��,�洢������Ϊ��Ч���׵�index
    class cc_block {
    public:
        unsigned int height; // �߶ȣ�Ҳ������ʾʱ��
        unsigned long ID;
        unsigned long prev_ID; // ֮ǰ�����ID Ϊ0��ʾ��ʼ����
        unsigned int node_ID; // ����ڵ�ID
        unsigned int acb_height; // ����������acb��ĸ߶�
        int block_epoch; // ��ǰ�ֵĳ�����
        double time;
        int txn_cnt;
        cc_block* prev = nullptr;
        cc_block* next = nullptr;

        // ����������׼��Ƿ�����int = -1,����int ��ʾ���׼���Ӧ��fail_txn�е�����
        std::unordered_map<std::string, int> fail_txs; // ����ժҪ��¼���д���ʧ�ܽ��׵Ľ��׼�
        std::vector<std::vector<std::string>> fail_txn; // ���׼�-����

        cc_block(unsigned int height, unsigned long ID, unsigned long prev_ID, unsigned int node_ID,
            unsigned int acb_height, int block_epoch, double time, int txn_cnt = 0);
        virtual ~cc_block();
        std::string block_2_str();
        void Clear();
        static cc_block* str_2_block(std::string str);
    };

    // ���ڽ�����
    class cc_exchange {
    public:
        unsigned int height; // �߶ȣ�Ҳ������ʾʱ��
        unsigned long ID;
        unsigned long prev_ID; // ֮ǰ�����ID Ϊ0��ʾ��ʼ����
        unsigned int node_ID; // ����ڵ�ID
        unsigned int acb_height; // ����������acb��ĸ߶�
        int block_epoch; // ��ǰ�ֵĳ�����
        double time;
        std::vector<std::string> tx_prf_vec;// ��һ��epoch���ռ����Ľ��׼��϶�Ӧ��pef


        cc_exchange(unsigned int height, unsigned long ID, unsigned long prev_ID, unsigned int node_ID,
            unsigned int acb_height, int block_epoch, double time);
        virtual ~cc_exchange();
        std::string block_2_str();
        static cc_exchange* str_2_block(std::string str);
    };

    //���׼�
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

    //��ִ
    class receipt {
    public:
        const unsigned int sendID;//���ͽڵ�
        const unsigned int recvID; // ���սڵ�
        const unsigned int height;// ���׼����ڵ�����ĸ߶�
        std::vector<std::string> txs; // ���׼��е�ȫ������
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

    class staticticStruct // ���ڽ���ͳ��
    {
    public:
        double time = 0;        //����ͳ�Ƶ�ʱ��
        int CCPT = 0;           //ccpt����
        double ACC_storage = 0; //AC����ռ�ݵĴ洢����
        double CCC_storage = 0; //CC����ռ�ݵĴ洢����
        double PBC_storage = 0; //��������ռ�ݵĴ洢����

        staticticStruct() { return; };
        virtual ~staticticStruct() { ; };
    };
}

#endif // !__DEMO_BLOCK_H

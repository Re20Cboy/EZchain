#ifndef __DEMO_GLOBAL_H
#define __DEMO_GLOBAL_H

#include <iostream>
#include <string>
#include <map>
#include <Windows.h>

#include "block.h"
#include "node.h"
#include "msg.h"

#include <leveldb/db.h>

extern long NODENUM;// 节点的数量
extern int MNUM;
extern double EPOCHT;
extern int N_V; // 每个节点初始时 拥有的Value（资源）
extern double TXRATE; // 每个个节点产生交易的速率
extern bool USECC;
extern double ABS_SZ;  // 摘要大小
extern double TX_SZ;  // 交易大小
extern double CCB_SZ; // CC块大小

extern long MSG_ID;

extern int VAL_CNT;
extern unsigned long TX_CNT;
extern size_t TX_SEND_CNT;
extern long ABS_CNT;

extern int simulationTime;
extern double currentSimulationTime;
extern double delay;

//统计
extern int CCPT;           //CCPT开销(笔均通信开销)
extern double ACC_storage; //AC块所占据的存储开销
extern double CCC_storage; //CC块所占据的存储开销
extern double PBC_storage; //个人链所占据的存储开销
extern double RECORD_INTERVAL;

extern leveldb::DB* TXDB;
extern leveldb::DB* PRFDB;
extern leveldb::DB* PBDB;
extern leveldb::DB* INFDB;



extern std::string statistic_file;
extern std::string statistic_folder;

struct msgpool{
    int size;
    ezchain::cMessage* head;
    ezchain::cMessage* tail;
};

struct ACchain {
    int size;
    ezchain::ac_block* head;
    ezchain::ac_block* tail;
};

struct CCchain {
    int size;
    ezchain::cc_block* head;
    ezchain::cc_block* tail;
};

extern msgpool INF_POOL; // 存放待打包的交易
extern ACchain ACC; // AC链
extern CCchain CCC; // CC链

class tx_cc {
public:
    static int add(std::vector<unsigned long> &cnt, unsigned long x = 1);
    static unsigned long CCPT(std::vector<unsigned long>& cnt, unsigned long tx_cnt);
    static int sub(std::vector<unsigned long>& cnt, unsigned long x);
};

class TX_P_VAL {
public:
    std::vector<unsigned long> tx_num;
    TX_P_VAL();
    virtual ~TX_P_VAL();
    double get_mean(unsigned long node_num) const;
};

class simEvent {
    double time;
    int nodeID;
    ezchain::cMessage* msgP;
public:
    simEvent(int node, double t, ezchain::cMessage* msgP);
    virtual ~simEvent();
    double getTime() const { return this->time; };
    int getNodeID() const { return this->nodeID; };
    ezchain::cMessage* getMsg() const { return this->msgP; };
};

class simulation {
public:
    std::string command = "";
    double currentSimulationTime = 0;
    double simulationTime = 0;
    
    long nodeNum = 0;// 节点的数量
    int mNum = 0;
    double epochT = 0;
    int n_V = 0; // 每个节点初始时 拥有的Value（资源）
    double txRate = 0; // 每个个节点产生交易的速率
    bool useCC = false;
    std::vector<ezchain::node*> nodeLst; // 区块列表
    std::multimap<double, simEvent*> eList;// 事件列表
    ezchain::staticticStruct* sta = nullptr;

    simulation();
    simulation(double simTime, int n, int M, double T, int nV, double k, bool u)
        :simulationTime(simTime),nodeNum(n), mNum(M), epochT(T), n_V(nV), txRate(k), useCC(u) {
        return;
    };
    virtual ~simulation();

    void showParameter();
    int changeParameter(int idx);

    int setSimulationTime(std::string);
    int setnodeNum(std::string);
    int setmNum(std::string);
    int setepochT(std::string);
    int setn_V(std::string);
    int settxRate(std::string);
    int setuseCC(std::string);
};

extern enum msg_type {
    hello = 0,
    gen_TX = 1,
    hash = 2,
    acb = 3,
    inf_for_pack = 4,
    T_timer = 5,
    g1 = 6,
    g2 = 7,
    g3 = 9,
    g4 = 10,
    t_msg_type = 11,
    Inf_pack_fail = 12,
    ccb_1 = 13,   // 交流inf
    ccb_2 = 14,   // leader 发布初稿
    ccb_3 = 15,   // 第一次向全网广播
    ccb_4 = 16,
    ccb_5 = 17,
    sig = 18,
    light_Inf = 19,
    space = 20
};

extern enum error_type {
    tx_type = -1,
    prf_type = -2,
    recv_node = -3,
    init_high = -4,
    empty_prf = -5,
    double_spent = -6,
    prf_incomplete = -7,
    cross_CC = -8,
    wrong_owner = -9,
    inf_empty = -10,
    inf_abs = -11,
    acc_height = -12,
    not_spend = -13,
    acc_begin = -14,
    after_cc = -15
};

//产生一（a,b）的均匀分布
double random(double a, double b);

//泊松分布，Lamda为唯一的一个参数,均值和方差
double poisson(const double Lamda);

double randomExponential(double lambda);

//生成在[a,b]区间内均匀分布的随机整数
int intuniform(int a, int b);

int recordScalar(const char* c, double time);

int recordError(int type);

LPCWSTR stringToLPCWSTR(std::string orig);

bool FindOrCreateDirectory(std::string name);

LPCWSTR stringToLPCWSTR(const char* c);

#endif // !__DEMO_GLOBAL_H


#include <iostream>
#include <fstream>
#include <string>
#include <map>
#include <ctime>
#include <Windows.h>

#include "main.h"
#include "node.h"
#pragma warning(disable : 4996)

std::vector<ezchain::node*> nodeLst; // 区块列表
std::multimap<double, simEvent*> eList;// 事件列表
ezchain::staticticStruct* sta;


std::string hint_1 = "\t1,终止运行并进行统计。\n\t2,继续运行\n\t3,查看指定数据\n\t4,其他\n";
std::string default_command = "10200 100 20 2000 8 0.025 1";

// 输入参数依次为 持续时间、节点个数、委员会大小、CC算法周期、每个节点拥有的价值数、节点生成交易的速率和是否使用CC算法
int main(int argc, char** argv)
{
    std::cout << "Run EZchain Demo!";
    std::string command = "";
    int sim_cnt = 0;
    simulation* sim = new simulation(50300, 300, 40, 2000, 8, 0.01, true);
    while (getCommand(command,sim)) {
        // initialize simulation
        initialize(sim_cnt++);
        int ret = runSimulation();
        finish();
        std::cout << "运行结束，按任意键以进行新的模拟，或输入quit以退出\n";
        getline(std::cin, command);
    }
    delete sim;
    return 0;
}

double simTime() {
    return currentSimulationTime;
}

int scheduleAt(int node,double time, ezchain::cMessage* msg) {
    simEvent* e = new simEvent(node, time, msg);
    msg->setEvtTime(time);
    eList.insert(std::make_pair(time, e));
    //std::cout << "schedule msg " << msg->getKind() << " at " << time << std::endl;
    return 0;
}

bool getCommand(std::string& command, simulation* sim) {
    if (command == "quit") {
        return false;
    }

    std::cout << "当前参数设置如下\n";
    
    sim->showParameter();
    bool flag = true;
    while (flag) {
        std::cout << "请选择想要调整的参数的序号，或按回车结束调整" << std::endl;
        getline(std::cin, command);
        command == "" ? flag = true : flag = false;
        if (flag) {
            break;
        }
        int id = stoi(command);
        sim->changeParameter(id);
        flag = true;
    }
    std::cout << "当前参数设置如下, 按任意键开始运行" << std::endl;
    sim->showParameter();
    getline(std::cin, command);

    simulationTime = sim->simulationTime;
    NODENUM = sim->nodeNum;
    MNUM = sim->mNum;
    EPOCHT = sim->epochT;
    N_V = sim->n_V;
    TXRATE = sim->txRate;
    USECC = sim->useCC;
    return true;
}

int broadcast(ezchain::cMessage* msg, int from) {
    
    switch (msg->getKind())
    {
    case inf_for_pack: // 将待打包的交易集加入缓冲池
        if (INF_POOL.head == nullptr) {
            INF_POOL.head = msg;
            INF_POOL.tail = msg;
            INF_POOL.size++;
        }
        else {
            INF_POOL.tail->setNext(msg);
            INF_POOL.tail = msg;
            INF_POOL.size++;
        }
        //std::cout << "INF size " << INF_POOL.size << std::endl;
        break;
    case msg_type::acb:        
        for (auto n : nodeLst) {
            if (n->ID == from && msg->getKind() != ccb_5) {
                continue;
            }
            //为相应节点设定一个到达事件
            ezchain::cMessage* arrive_mag = msg->dup(MSG_ID++);
            scheduleAt(n->ID, simTime(), arrive_mag);
        }
        break;
    default:
        for (auto n : nodeLst) {
            if (n->ID == from && msg->getKind() != ccb_5) {
                continue;
            }
            //为相应节点设定一个到达事件
            ezchain::cMessage* arrive_mag = msg->dup(MSG_ID++);
            scheduleAt(n->ID, simTime() + random(0,delay), arrive_mag);
        }
        break;
    }
    return 0;
}

int send(ezchain::cMessage* msg, int from, int to)
{
    // 向所有节点进行广播
    if (to == -1) {
        broadcast(msg, from);
    }
    // 传送给特定节点
    else if (to < nodeLst.size() && to != from) {
        ezchain::cMessage* arrive_msg = msg->dup(MSG_ID++);
        scheduleAt(to, simTime() + random(0, delay), arrive_msg);
    }
    else return -1;
    return 0;
}

int createNet(std::vector<ezchain::node*>& nodeLst) {
    nodeLst.reserve(NODENUM);
    for (unsigned long i = 0; i < NODENUM; i++) {
        ezchain::node* n = new ezchain::node(i);
        nodeLst.push_back(n);
    }
    return 0;
}

int cancelEvent(ezchain::cMessage* event) {
    double evtTime = event->getEvtTime();
    long msgID = event->getID();
    std::map<double, simEvent*>::iterator eList_it = eList.find(evtTime);
    std::multimap<double, simEvent*>::size_type cnt = eList.count(evtTime);
    while (0 < cnt) {
        if (eList_it->second->getMsg()->getID() == msgID) {
            eList.erase(eList_it);
            return 0;
        }
        eList_it++; cnt--;
    }
    exit(-1);
    return -1;
}

int recordACC(ACchain ACC)
{
    std::fstream file(statistic_file, std::ios::out | std::ios::app);
    ezchain::ac_block* acp = ACC.tail;
    file << "block height,block ID,prev block ID,time,Abstract of Inf in block\n";
    while (acp != nullptr) {
        std::string str = std::to_string(acp->height); str += ',';
        str += std::to_string(acp->ID); str += ',';
        str += std::to_string(acp->prev_ID); str += ',';
        str += std::to_string(acp->time); str += ',';
        for (auto a : acp->A_vec) {
            str += a; str += ',';
        }
        str += '\n';
        file << str;
        ezchain::ac_block* temp = acp->prev;
        //delete acp;
        acp = temp;
    }
    file.close();
    return 0;
}

int recordCCC(CCchain CCC)
{
    std::fstream file(statistic_file, std::ios::out | std::ios::app);
    ezchain::cc_block* ccp = CCC.tail;
    file << "block height,block ID,prev block ID,time\n";
    while (ccp != nullptr) {
        std::string str = std::to_string(ccp->height); str += ',';
        str += std::to_string(ccp->ID); str += ',';
        str += std::to_string(ccp->prev_ID); str += ',';
        str += std::to_string(ccp->time); str += ',';
        str += '\n';
        file << str;
        ezchain::cc_block* temp = ccp;
        ccp = ccp->prev;
    }
    file.close();
    return 0;
}

int initialize(int sim_cnt) {
    VAL_CNT = 0; TX_CNT = 0; MSG_ID = 0; TX_SEND_CNT = 0; ABS_CNT = 0;
    INF_POOL.size = 0; INF_POOL.head = nullptr; INF_POOL.tail = nullptr;
    ACC.size = 0; ACC.head = nullptr; ACC.tail = nullptr;
    CCC.size = 0; CCC.head = nullptr; CCC.tail = nullptr;
    currentSimulationTime = 0;
    sta = new ezchain::staticticStruct();

    time_t now = time(0);
    char* time_ch = ctime(&now);
    srand((int)time(0));
    if(sim_cnt == 0 && FindOrCreateDirectory(statistic_folder)) statistic_file = statistic_folder + "\\" + statistic_file;
    std::fstream file(statistic_file, std::ios::out | std::ios::app);
    //  记录实验的参数
    file << time_ch << std::endl;
    file << "持续时间,节点个数,委员会大小,CC算法周期,初始价值数的期望,交易速率的期望,否使用CC算法\n";
    file << simulationTime << "," << NODENUM << "," << MNUM << "," << EPOCHT << "," << N_V << "," << TXRATE << "," << USECC << std::endl << std::endl;
    file << "时刻,CCPT,AC块所占据的存储开销,CC块所占据的存储开销,个人链所占据的存储开销\n";
    file.close();
    //std::string s;  getline(std::cin, s);

    createNet(nodeLst);
    return 0;
}

int finish() {
    // 记录实验的结果
    record();
    if (USECC != 0)  recordCCC(CCC);
    recordACC(ACC);
    
    //  清理
    for (auto n : nodeLst) {
        delete n; n = nullptr;
    }
    nodeLst.clear();
    eList.clear();
    delete sta;

    return 0;
}

int getNewCommand(std::string command, int type) {
    int opt = 0;
    switch(type){
    case 1: break;
    default: std::cout<<"Wrong command. please retype:\n" << hint_1;
        getline(std::cin, command);
        getNewCommand(command, 1);
        break;
    }
    return opt;
}

double record(double rtime) {
    //nodeLst.at(0)->statistic(CCPT, ACC_storage, CCC_storage, PBC_storage);
    nodeLst.at(0)->statistic(sta);
    std::fstream file(statistic_file, std::ios::out | std::ios::app);
    file << currentSimulationTime << "," << sta->CCPT << "," << sta->ACC_storage 
        << "," << sta->CCC_storage<< "," << sta->PBC_storage  << std::endl;;
    file.close();
    return rtime + RECORD_INTERVAL;
}

int runSimulation() {
    std::map<double, simEvent*>::iterator eList_it;
    double timeforrecord = RECORD_INTERVAL + (double)100;
    for (; !eList.empty();) {
        eList_it = eList.begin();
        currentSimulationTime = eList_it->first;
        if (currentSimulationTime > simulationTime) return 0;

        // 从事件队列中取出需要相应的事件，由对应的节点进行响应
        simEvent* event = eList_it->second;
        int nodeID = event->getNodeID();
        ezchain::cMessage* msg = event->getMsg();
        nodeLst.at(nodeID)->handleMessage(msg);
        // 每隔1000s统计一次
        if (currentSimulationTime > timeforrecord) timeforrecord = record(timeforrecord);
        delete eList_it->second; eList_it->second = nullptr;
        eList.erase(eList_it);
    }

    return -1;
}
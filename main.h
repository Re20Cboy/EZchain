#ifndef __DEMO_MAIN_H
#define __DEMO_MAIN_H

#include <iostream>
#include <string>
#include <map>

#include "msg.h"
#include "global.h"

// ����ģ��ʱ��
double simTime();
// ��ʱ��˳�򽫼ƻ��¼������¼���
int scheduleAt(int node, double time, ezchain::cMessage* msg);
// ��ȡ��������
bool getCommand(std::string& command, simulation* sim);
// ת����Ϣ
int send(ezchain::cMessage* msg, int from, int to = -1);
// �㲥��Ϣ
int broadcast(ezchain::cMessage* msg, int from);
// ȡ���ƻ��¼�
int cancelEvent(ezchain::cMessage* event);
// ��ʼ�������ͱ���
int initialize(int time = 0);
// ����ģ��
int runSimulation();
// ��ʵ�������м�¼
int finish();
// ÿ��һ��ʱ���¼һ��
double record(double time = 0);
//
int getNewCommand(std::string command,int type);

#endif // !__DEMO_MAIN_H

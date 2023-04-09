#ifndef __DEMO_MAIN_H
#define __DEMO_MAIN_H

#include <iostream>
#include <string>
#include <map>

#include "msg.h"
#include "global.h"

// 返回模拟时间
double simTime();
// 按时间顺序将计划事件插入事件表
int scheduleAt(int node, double time, ezchain::cMessage* msg);
// 获取参数设置
bool getCommand(std::string& command, simulation* sim);
// 转发消息
int send(ezchain::cMessage* msg, int from, int to = -1);
// 广播消息
int broadcast(ezchain::cMessage* msg, int from);
// 取消计划事件
int cancelEvent(ezchain::cMessage* event);
// 初始化参数和变量
int initialize(int time = 0);
// 运行模拟
int runSimulation();
// 对实验结果进行记录
int finish();
// 每隔一段时间记录一次
double record(double time = 0);
//
int getNewCommand(std::string command,int type);

#endif // !__DEMO_MAIN_H


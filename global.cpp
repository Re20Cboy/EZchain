#include <iostream>
#include <fstream>
#include <string>
#include <time.h>

#include "global.h"

long NODENUM = 0;// 节点的数量
int MNUM = 0;
double EPOCHT = 0;
int N_V = 0; // 每个节点初始时 拥有的Value（资源）
double TXRATE = 0; // 每个个节点产生交易的速率
bool USECC = false;
double ABS_SZ = 0.2;  // 摘要大小
double TX_SZ = 62.5;  // 交易大小
double CCB_SZ = 1024; // CC块大小

int VAL_CNT = 0;
unsigned long TX_CNT = 0;
size_t TX_SEND_CNT = 0;
long ABS_CNT = 0;

int simulationTime = 0;
double delay = 2;

int CCPT = 0;           //CCPT开销(笔均通信开销)
double ACC_storage = 0; //AC块所占据的存储开销
double CCC_storage = 0; //CC块所占据的存储开销
double PBC_storage = 0; //个人链所占据的存储开销
double RECORD_INTERVAL = 1000;

leveldb::DB* TXDB = nullptr;
leveldb::DB* PRFDB = nullptr;
leveldb::DB* PBDB = nullptr;
leveldb::DB* INFDB = nullptr;

msgpool INF_POOL = { 0,nullptr,nullptr };
ACchain ACC = { 0,nullptr,nullptr };
CCchain CCC = { 0,nullptr,nullptr };

long MSG_ID = 0;

double currentSimulationTime;

std::string statistic_file = "stastics.csv";
std::string statistic_folder = "result";

int tx_cc::add(std::vector<unsigned long>& cnt, unsigned long x) {
	if (cnt.empty()) {
		cnt.push_back(0);
	}
	if (LONG_MAX - x < cnt.back()) {
		cnt.push_back(x);
	}
	else cnt.back() += x;
	return 0;
}
int tx_cc::sub(std::vector<unsigned long>& cnt, unsigned long x) {
	while (!cnt.empty() && x > cnt.back()) {
		x -= cnt.back();
		cnt.pop_back();
	}
	if (cnt.empty()) {
		cnt.push_back(0);
	}
	else {
		cnt.back() -= x;
	}
	return 0;
}

unsigned long tx_cc::CCPT(std::vector<unsigned long>& cnt, unsigned long tx_cnt) {
	unsigned long ccpt = 0;
	for (auto x : cnt) {
		ccpt += x / tx_cnt;
	}
	return ccpt;
}

simulation::simulation()
{
	return;
}
simulation::~simulation()
{
	;
}
void simulation::showParameter()
{
	int cnt = 1;
	std::string uCC = this->useCC ? "true" : "false";
	std::cout << cnt++ << ". 持续时间\t\t" << this->simulationTime << std::endl;
	std::cout << cnt++ << ". 节点个数\t\t" << this->nodeNum << std::endl;
	std::cout << cnt++ << ". 委员会大小\t\t" << this->mNum << std::endl;
	std::cout << cnt++ << ". CC算法周期 \t\t" << this->epochT << std::endl;
	std::cout << cnt++ << ". 每个节点拥有的价值数 " << this->n_V << std::endl;
	std::cout << cnt++ << ". 节点生成交易的速率\t" << this->txRate << std::endl;
	std::cout << cnt++ << ". 是否使用CC算法\t" << uCC << std::endl;
	return;
}
int simulation::changeParameter(int idx)
{
	std::cout << "请输入新的参数值："<< std::endl;
	std::string value;
	getline(std::cin, value);
	switch (idx)
	{
	case 1: setSimulationTime(value); break;
	case 2: setnodeNum(value); break;
	case 3: setmNum(value); break;
	case 4: setepochT(value); break;
	case 5: setn_V(value); break;
	case 6: settxRate(value); break;
	case 7: setuseCC(value); break;
	default:
		break;
	}
	return 0;
}

int simulation::setSimulationTime(std::string str) {
	double t = stod(str);
	while (t < 0) {
		std::cout << "参数值不能小于0：" << std::endl;
		getline(std::cin, str);
		t = stod(str);
	}
	this->simulationTime = t;
	return 0;
}
int simulation::setnodeNum(std::string str) {
	auto t = stoul(str);
	while (t < 0) {
		std::cout << "参数值不能小于0：" << std::endl;
		getline(std::cin, str);
		t = stoul(str);
	}
	this->nodeNum = t;
	return 0;
}
int simulation::setmNum(std::string str) {
	auto t = stoul(str);
	while (t < 0 || t > nodeNum) {
		std::cout << "参数值不能小于0且不能大于总节点数："<< std::endl;
		getline(std::cin, str);
		t = stoul(str);
	}
	this->mNum = t;
	return 0;
}
int simulation::setepochT(std::string str) {
	auto t = stoi(str);
	while (t < 0) {
		std::cout << "参数值不能小于0：" << std::endl;
		getline(std::cin, str);
		t = stoi(str);
	}
	this->epochT = t;
	return 0;
}
int simulation::setn_V(std::string str) {
	auto t = stoi(str);
	while (t < 0) {
		std::cout << "参数值不能小于0：" << std::endl;
		getline(std::cin, str);
		t = stoi(str);
	}
	this->n_V = t;
	return 0;
}
int simulation::settxRate(std::string str) {
	double t = stod(str);
	while (t <= 0) {
		std::cout << "参数值不能小于或等于0：" << std::endl;
		getline(std::cin, str);
		t = stod(str);
	}
	this->txRate = t;
	return 0;
}
int simulation::setuseCC(std::string str) {
	bool flag = true;
	str == "false" ? this->useCC = false : (str == "true" ? this->useCC = true : flag = false);
	while (!flag) {
		std::cout << "请输入 true 或者 false 来选择是否使用 CC 算法" << std::endl;
		flag = true;
		str == "false" ? this->useCC = false : (str == "true" ? this->useCC = true : flag = false);
	}
	return 0;
}

simEvent::simEvent(int node, double t, ezchain::cMessage* msg)
{
	this->time = t;
	this->nodeID = node;
	this->msgP = msg;
}
simEvent::~simEvent()
{
	;
}

//产生一（a,b）的均匀分布
double random(double a, double b)
{
	//产生伪随机数
	double x = rand();
	return  a + (b - a) * (x + 1) / (RAND_MAX + 1);
}

//泊松分布，Lamda为唯一的一个参数,均值和方差
double poisson(const double Lamda)
{
	double  log1, log2;
	int x = -1;
	log1 = 0; log2 = -Lamda;
	do {
		log1 += log(random(0, 1));
		x++;
	} while (log1 >= log2);
	return  x > 0 ? x : 0;
}

double randomExponential(double lambda)
{
	double pV = 0.0;
	while (true)
	{
		pV = (double)rand() / (double)RAND_MAX;
		if (pV != 1)
		{
			break;
		}
	}
	pV = -lambda * log(1 - pV);
	return pV;
}

//生成在[a,b]区间内均匀分布的随机整数
int intuniform(int a, int b) {
	double x = random((double)a, (double)b);
	int res = trunc(x);
	// TODO: 负数部分
	x - res >= 0.5 ? res++ : res;
	return res;
}

int recordScalar(const char* c, double time) {
	std::string name = "Scalar record";
	if (FindOrCreateDirectory(statistic_folder)) name = statistic_folder + "\\" + name;
	std::fstream file(name, std::ios::out | std::ios::app);
	std::string str = c;
	file << str << "\t" << time << std::endl;
	file.close();
	return 0;
}

int recordError(int type) {
	std::string name = "Error record.csv";
	if (FindOrCreateDirectory(statistic_folder)) name = statistic_folder + "\\" + name;
	std::fstream file(name, std::ios::out | std::ios::app);
	std::string str = std::to_string(type);
	file << type << std::endl;
	file.close();
	return 0;
}


LPCWSTR stringToLPCWSTR(std::string orig)
{
	wchar_t* wcstring = 0;
	try
	{
		size_t origsize = orig.length() + 1;
		const size_t newsize = 100;
		size_t convertedChars = 0;
		if (orig == "")
		{
			wcstring = (wchar_t*)malloc(0);
			mbstowcs_s(&convertedChars, wcstring, origsize, orig.c_str(), _TRUNCATE);
		}
		else
		{
			wcstring = (wchar_t*)malloc(sizeof(wchar_t) * (orig.length() - 1));
			mbstowcs_s(&convertedChars, wcstring, origsize, orig.c_str(), _TRUNCATE);
		}
	}
	catch (std::exception e)
	{
	}
	return wcstring;
}

LPCWSTR stringToLPCWSTR(const char* c)
{
	std::string s(c);
	return stringToLPCWSTR(s);
}

bool FindOrCreateDirectory(std::string name)
{
	LPCWSTR pszPath = stringToLPCWSTR(name);
	WIN32_FIND_DATA fd;
	HANDLE hFind = ::FindFirstFile(pszPath, &fd);
	while (hFind != INVALID_HANDLE_VALUE)
	{
		if (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)
			return true;
	}
	if (!CreateDirectory(pszPath, NULL))
	{
		::MessageBox(NULL, pszPath, stringToLPCWSTR("创建目录失败"), MB_OK | MB_ICONERROR);
		return false;
	}
	return true;
}

TX_P_VAL::TX_P_VAL()
{
	;
}

TX_P_VAL::~TX_P_VAL()
{
	std::vector<unsigned long>().swap(tx_num);
	return;
}

double TX_P_VAL::get_mean(unsigned long node_num) const
{
	double ret = 0;
	for (auto n : tx_num) {
		ret += (double)n / (double)node_num;
	}
	return ret;
}

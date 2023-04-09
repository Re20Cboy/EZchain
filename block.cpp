#include <string>

#include "block.h"
#include "cryptography.hpp"
using namespace std;

namespace ezchain {
	ac_block::ac_block(unsigned int height, unsigned long ID, unsigned long prev_ID, unsigned int node_ID, double time)
		:height(height), ID(ID), prev_ID(prev_ID), node_ID(node_ID), time(time) {
		prev = nullptr;
	};

	ac_block::~ac_block() {
		std::vector<std::string>().swap(A_vec);
		std::map<unsigned int, bool>().swap(node_filter);
		delete prev; prev = nullptr;
	}
	string ac_block::block_2_str()
	{
		string ab_str = to_string(ID); ab_str += ',';
		ab_str += to_string(height); ab_str += ',';
		ab_str += to_string(prev_ID); ab_str += ',';
		ab_str += to_string(node_ID); ab_str += ',';
		ab_str += to_string(time); ab_str += "$";
		for (auto a : A_vec) {
			ab_str += a; ab_str += "$";
		}
		return ab_str;
	}
	ac_block* ac_block::str_2_block(string str)
	{
		
		unsigned long h; // 高度，也用来表示时刻
		unsigned long id;
		unsigned long prev_id;
		unsigned long node_id; // 出块节点ID
		double t;
		size_t from = 0;
		size_t to = str.find(',', from);
		id = stoul(str.substr(from, to - from));
		
		from = to + 1;
		to = str.find(',', from);
		h = stoul(str.substr(from, to - from));
		
		from = to + 1;
		to = str.find(',', from);
		prev_id = stoul(str.substr(from, to - from));
		
		from = to + 1;
		to = str.find(',', from);
		node_id = stoul(str.substr(from, to - from));
		
		from = to + 1;
		to = str.find("$", from);
		t = stod(str.substr(from, to - from));

		ac_block* ret = new ac_block(h, id, prev_id, node_id, t);

		from = to + 1;
		while (from < str.length()) {
			to = str.find("$", from);
			ret->A_vec.push_back(str.substr(from,to-from));
			from = to + 1;
		}

		return ret;
	}
	void ac_block::record() {
		return;
	}

	cc_block::cc_block(unsigned int height, unsigned long ID, unsigned long prev_ID, unsigned int node_ID,
		unsigned int acb_height, int block_epoch, double time, int txn_cnt)
		:height(height), ID(ID), prev_ID(prev_ID), node_ID(node_ID), acb_height(acb_height), block_epoch(block_epoch),
		time(time), txn_cnt(txn_cnt) {};

	cc_block::~cc_block() {
		std::vector<std::vector<std::string>>().swap(fail_txn);
		std::unordered_map<std::string, int>().swap(fail_txs);
		prev = nullptr;
		next = nullptr;
	}

	std::string cc_block::block_2_str()
	{
		string cc_str = to_string(ID); cc_str += ',';
		cc_str += to_string(height); cc_str += ',';
		cc_str += to_string(prev_ID); cc_str += ',';
		cc_str += to_string(node_ID); cc_str += ',';
		cc_str += to_string(acb_height); cc_str += ',';
		cc_str += to_string(block_epoch); cc_str += ',';
		cc_str += to_string(time); cc_str += ',';
		cc_str += to_string(txn_cnt); cc_str += "$";
		for (auto it : fail_txs) {
			cc_str += it.first; cc_str += ',';
			cc_str += to_string(it.second); cc_str += "$";
		}
		for (auto it_1 : fail_txn) {
			cc_str += "%";
			for (auto it_2 : it_1) {
				cc_str += it_2;
			}
		}
		return cc_str;
	}
	void cc_block::Clear()
	{
		this->fail_txn.clear();
		this->fail_txs.clear();
	}
	cc_block* cc_block::str_2_block(string str)
	{
		unsigned int h, nID, a_h;
		double t;
		int b_epoch,t_cnt,val;
		unsigned long pID, id;
		size_t from = 0;
		size_t to = str.find(',', from);
		id = stoul(str.substr(from, to - from));
		
		from = to + 1;
		to = str.find(',', from);
		h = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		pID = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		nID = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		a_h = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		b_epoch = stoi(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		t = stod(str.substr(from, to - from));

		from = to + 1;
		to = str.find("$", from);
		t_cnt = stoul(str.substr(from, to - from));

		cc_block* cc = new cc_block(h,id,pID,nID,a_h,b_epoch,t,t_cnt);

		from = to + 1;
		to = str.find("$", from);
		size_t pos = str.find("%");
		string s;
		pos == string::npos ? pos = str.length() : pos;
		while (from < pos) {
			to = str.find(',', from);
			s = str.substr(from, to - from);
			from = to + 1;
			to = str.find("$", from);
			val = stoul(str.substr(from, to - from));
			cc->fail_txs.insert(make_pair(s, val));
			from = to + 1;
		}
		while (pos < str.length()) {
			from = pos + 1;
			pos = str.find("%", pos + 1);
			pos == string::npos ? pos = str.length() : pos;
			vector<string> vec;
			while (from < pos ) {
				to = str.find("$", from)+1;
				s = str.substr(from, to - from);
				vec.push_back(s);
				from = to;
			}
			cc->fail_txn.push_back(vec);
		}
		return cc;
	}

	INF::INF(const unsigned int node_ID):node_ID(node_ID)
	{
		return;
	}

	string INF::getTxAbs(std::string str)
	{
		size_t from = str.find("$")+1;
		size_t to = str.find_last_of("$")+1;
		str = str.substr(from, to - from);
		string txs_str;
		to = str.find('\t', from);
		while (to != string::npos) {
			txs_str += str.substr(from, to - from);
			from = to + 1;
			to = str.find('\t', from);
		}
		txs_str = Cryptography::GetHash(txs_str.c_str(), txs_str.size());
		return txs_str;
	}
	string INF::getTxAbs()
	{
		string txs_str;
		for(auto str : this->tx_prf_vec) {
			size_t to = str.find(';');
			txs_str += str.substr(0, to+1);
		}
		txs_str = Cryptography::GetHash(txs_str.c_str(), txs_str.size());
		return txs_str;
	}
	INF::~INF()
	{
		std::vector<std::string>().swap(tx_prf_vec);
	}
	std::string INF::inf_to_str()
	{
		string str = to_string(node_ID); str += ',';
		str += to_string(tx_prf_vec.size()); str += "$";
		for (auto s : tx_prf_vec) {
			str += s;
		}
		str += abs; str += ',';
		str += to_string(height);
		return str;
	}
	INF* INF::str_2_inf(string str)
	{
		size_t from = 0;
		size_t to = str.find(',', from);
		unsigned long node_ID = stoul(str.substr(from,to-from));
		INF* ret = new INF(node_ID);

		from = to + 1;
		to = str.find("$", from);
		size_t sz = stoul(str.substr(from, to - from));

		for (from = to + 1; 0 < sz;sz--) {
			to = str.find("$", from) + 1;
			ret->tx_prf_vec.push_back(str.substr(from, to - from));
			from = to ;
		}
		if (from < str.length()) {
			to = str.find(',', from);
			ret->abs = str.substr(from, to - from);
			from = to + 1;
		}
		if (from < str.length())
			ret->height = stoul(str.substr(from));
		return ret;
	}
	std::string pc_block::block_2_str()
	{
		std::string str = std::to_string(height); str += "$";
		for (auto s : txs) {
			str += s; str += "\t";
		}
		str += "$";
		for (auto s : prfs) {
			str += s; str += "\t";
		}
		str += "$";
		str += txs_abstract;
		return str;
	}
	pc_block::pc_block(std::string str)
	{
		size_t from = 0;
		size_t to = str.find("$", from);
		height = stoul(str.substr(from, to - from));

		from = to + 1;
		size_t pos = str.find("$", from);
		while (from < pos) {
			to = str.find('\t', from);
			txs.push_back(str.substr(from, to - from));
			from = to + 1;
		}
		from = pos + 1;
		pos = str.find("$", from);
		while (from < pos) {
			to = str.find('\t', from);
			txs.push_back(str.substr(from, to - from));
			from = to + 1;
		}
		if(++pos < str.size())
			txs_abstract = str.substr(pos);
	}
	receipt::receipt(const unsigned int sID, const unsigned int rID, const unsigned int h):sendID(sID), height(h),recvID(rID)
	{
		return;
	}
	receipt::~receipt()
	{
		std::vector<std::string>().swap(txs);
	}

	std::string receipt::receipt_to_str()
	{
		string str = to_string(sendID); str += ',';
		str += to_string(recvID); str += ',';
		str += to_string(height); str += ',';
		str += to_string(tx_idx); str += "$";
		for (auto t : this->txs) {
			str += t; str += "$";
		}
		str += this->tx; str += '\t';
		str += this->prf;
		return str;
	}

	receipt* receipt::str_to_receipt(std::string str) {
		size_t from = 0;
		size_t to = str.find(',', from);
		unsigned long sID = stoul(str.substr(from, to - from));
		from = to + 1;
		to = str.find(',', from);
		unsigned long rID = stoul(str.substr(from, to - from));
		from = to + 1;
		to = str.find(',', from);
		unsigned long h = stoul(str.substr(from, to - from));
		from = to + 1;
		to = str.find("$", from);
		unsigned long idx = stoul(str.substr(from, to - from));
		receipt* ret = new receipt(sID,rID,h);
		from = to + 1;
		to = str.find("$", from);
		while (to != string::npos) {
			ret->txs.push_back(str.substr(from, to - from));
			from = to + 1;
			to = str.find("$", from);
		}
		to = str.find_last_of("$");
		from = to + 1;
		to = str.find_last_of('\t');
		ret->tx = str.substr(from, to - from);
		ret->prf = str.substr(to + 1);
		return ret;
	}
	
	cc_exchange::cc_exchange(unsigned int height, unsigned long ID, unsigned long prev_ID, unsigned int node_ID, 
		unsigned int acb_height, int block_epoch, double time)
		:height(height), ID(ID), prev_ID(prev_ID), node_ID(node_ID), acb_height(acb_height), block_epoch(block_epoch),
		time(time){}
	cc_exchange::~cc_exchange()
	{
		std::vector<std::string>().swap(tx_prf_vec);
	}
	std::string cc_exchange::block_2_str()
	{
		string cc_str = to_string(ID); cc_str += ',';
		cc_str += to_string(height); cc_str += ',';
		cc_str += to_string(prev_ID); cc_str += ',';
		cc_str += to_string(node_ID); cc_str += ',';
		cc_str += to_string(acb_height); cc_str += ',';
		cc_str += to_string(block_epoch); cc_str += ',';
		cc_str += to_string(time); cc_str += "$";
		for (auto it : tx_prf_vec) {
			cc_str += it;
		}
		return cc_str;
	}
	cc_exchange* cc_exchange::str_2_block(std::string str)
	{
		int val;
		size_t from = 0;
		size_t to = str.find(',', from);
		unsigned long id = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		unsigned int h = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		unsigned long pID = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		unsigned int nID = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		unsigned int a_h = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		int b_epoch = stoi(str.substr(from, to - from));

		from = to + 1;
		to = str.find("$", from);
		double t = stod(str.substr(from, to - from));

		cc_exchange* cc = new cc_exchange(h, id, pID, nID, a_h, b_epoch, t);
		from = to + 1;
		string s;
		while (from < str.length()) {
			to = str.find("$", from);
			s = str.substr(from, to - from);
			cc->tx_prf_vec.push_back(s);
			from = to + 1;
		}
		return cc;
	}
	
	sigclass::sigclass(unsigned long cID, unsigned int sign, unsigned int recv, double time, short int k)
	:ccb_ID(cID),sign_Node(sign), recv_Node(recv), time_Stamp(time), kind(k){}

	sigclass::~sigclass() {}

	std::string sigclass::sig_to_str() {
		string s_str = to_string(ccb_ID); s_str += ',';
		s_str += to_string(sign_Node); s_str += ',';
		s_str += to_string(recv_Node); s_str += ',';
		s_str += to_string(time_Stamp); s_str += ',';
		s_str += to_string(kind);
		return s_str;
	}

	sigclass* sigclass::str_to_sig(std::string str) {
		size_t from = 0;
		size_t to = str.find(',', from);
		unsigned long cID = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		unsigned int sign = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		unsigned int recv = stoul(str.substr(from, to - from));

		from = to + 1;
		to = str.find(',', from);
		double time = stod(str.substr(from, to - from));

		from = to + 1;
		int k = stoi(str.substr(from));
		return new sigclass(cID, sign, recv, time, k);
	}
}
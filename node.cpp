#include<vector>
#include<algorithm>
#include<iostream>
#include<stdio.h>
#include <fstream>
#include <string>
#include <math.h>

#include "node.h"
#include "global.h"
#include "main.h"
#include "cryptography.hpp"

//#define whole
//#define light

typedef std::string string;

std::vector<unsigned long> CNT;
//std::vector<unsigned long> TX_IN_PRF = {0};
TX_P_VAL* tx_p_val = new TX_P_VAL();

namespace ezchain {
	leveldb::DB* openTXDatabase( const std::string name) {
		leveldb::DB* db;
		leveldb::Options options;
		options.create_if_missing = true;
		leveldb::Status status = leveldb::DB::Open(options, name, &db);
		assert(status.ok());
		if (status.ok()) {
			std::cout << status.ToString() << std::endl;
		}
		else {
			std::cout << status.ToString() << std::endl;
		}
		return db;
	}



	node::node(const unsigned long ID):ID(ID){
		this->N = NODENUM;
		this->M = MNUM;
		this->T = EPOCHT;
		this->n_v = N_V;
		this->k = (double)1 / TXRATE;
		this->useCC = USECC;
		this->round = this->T / this->M;

		pID = 0;
		pHigh = 0;
		leader_ID_CC = N;
		leader_ID = leader_ID_CC;

		// ��ʼ���ڵ��ʲ���ÿ���ʲ�����Ӧȫ��Ψһ�ı��,���洢��Ӧ��֤��
		int temp = poisson(n_v);
		temp < 1 ? n_v = n_v + 0 : n_v = temp;
		//std::cout << "node " << this->ID << " is created with " << n_v << " val " << N_V;

				//����db
		if (TXDB == nullptr) {
			TXDB = openTXDatabase("tmp/txdb");
		}
		if (PRFDB == nullptr)
			PRFDB = openTXDatabase("tmp/prfdb");
		if (PBDB == nullptr)
			PBDB = openTXDatabase("tmp/pcdb");
		if (INFDB == nullptr)
			INFDB = openTXDatabase("tmp/infdb");
		

		for (temp = 0; temp < n_v; temp++) {
			//std::cout << "\t" << VAL_CNT<< std::endl;
			Prf *prf =  new Prf(ID, VAL_CNT, 0);
			this->val_prf.push_back(prf);
			tx_p_val->tx_num.push_back(0);
			VAL_CNT++;
		}

		// �������ɽ��׵Ķ�ʱ��
		cMessage* msg = new cMessage("gen_tx",gen_TX,MSG_ID++,this->ID);
		genTX(msg);

		//    ���ڼ���hash�Ķ�ʱ�ź�
		pow = new cMessage("pow", hash, MSG_ID++, this->ID);
		// TODO 
		double time = randomExponential(round * N);
		time < 0 ? time = round: (time > 9223372 ? time = 9223372 : time + 0);
		scheduleAt(this->ID, time, pow);

		//    ���ڽ���CC�㷨�Ķ�ʱ�ź�
		if (useCC) {
			cMessage* T_msg = new cMessage("CC_timer", T_timer, MSG_ID++, this->ID);
			scheduleAt(this->ID, T, T_msg);
		}
	}

	node::~node()
	{
		if (TXDB != nullptr) {
			delete TXDB; TXDB = nullptr;
		}
		if (PRFDB != nullptr) {
			delete PRFDB; TXDB = nullptr;
		}
		if (PBDB != nullptr) {
		delete PRFDB; TXDB = nullptr;
		}
		if (INFDB != nullptr) {
			delete INFDB; INFDB = nullptr;
		}

		if (pow != nullptr)
			delete pow; pow = nullptr;
		if(cb_ptr != nullptr)
			delete cb_ptr; cb_ptr = nullptr;
		if (Inf_collect != nullptr)
			delete Inf_collect; Inf_collect = nullptr;
		if(!tx_p_val->tx_num.empty())
			tx_p_val->tx_num.clear();
		if (!CNT.empty())
			std::vector<unsigned long>().swap(CNT);
		
		std::vector<size_t> ().swap(Inf_sz); // Inf_CC�ĸ�������
		std::vector<ac_block*> ().swap(ac_chain); // ac��
		for (auto pb : pb_map) {
			if(pb.second != nullptr)
			delete pb.second;
		}
		std::map<std::string, pc_block*>().swap(pb_map); // ժҪ���׼��ԣ��洢���ͺ�ȴ�ȷ�ϵĽ���
		for (auto pb : pb_chain) {
			pb.~basic_string();
		}
		std::vector<std::string>().swap(pb_chain);
		for (auto tx : tx_pool) {
			tx.~basic_string();
		}
		std::vector<std::string>().swap(tx_pool);

		for (auto p : val_prf) {
			if (p != nullptr)
				delete p;
		}
		std::vector<Prf *>().swap(val_prf);

		for (auto msg : Inf_cc) {
			delete msg; msg = nullptr;
		}
		Inf_cc.clear();
	}

	//��������¼�������
	void node::handleMessage(cMessage* msg) {
		short msgKind = msg->getKind();
		string msgName =  msg->getName();
		std::cout << "simulation time:\t" << simTime() << "\t\tevent type = " << msgName <<"\t\tfor node:\t" << this->ID<< std::endl;
		switch (msgKind)
		{
		case msg_type::gen_TX:		genTX(msg);				break;
		case msg_type::hash:		handlePow(msg);			break;
		case msg_type::acb:			handleACBlock(msg);		break;
		case msg_type::t_msg_type:	handleRecvtx(msg); 	break;
		case msg_type::T_timer:		handleTtimer(msg);		break;
		case msg_type::ccb_1:		collectInf(msg);		break;
		case msg_type::ccb_2:		handleCCB_2(msg);		break;
		case msg_type::ccb_3:		handleCCB_3(msg);		break;
		case msg_type::ccb_4:		handleCCB_4(msg);		break;
		case msg_type::ccb_5:		handleCCB(msg);			break;
		case msg_type::sig:			handleSig(msg);			break;
		case msg_type::g1:			handleGama_1(msg);      break;
		case msg_type::g2:			handleGama_2(msg);      break;
		case msg_type::g3:			handleGama_3(msg);		break;
		//case msg_type::g4:		handleGama_4(msg);      break;
		default:
			delete msg; msg = nullptr;
			break;
		}
		return;
	}

	/*
	* ����һ�����������ɽ���tx[��ţ���ֵ�������ߣ�������]�Ͷ�Ӧ��֤��prf
	*/
	int node::genTX(cMessage* msg) {

		if (!val_prf.empty()) {
			// ѡ��һ����ֵ��һ�����׶��󲢴�������
			size_t pos = val_prf.size() - 1;
			if (pos > 0) pos = intuniform(0, pos);
			Prf* p = val_prf.at(pos);
			unsigned long val = p->val;
			unsigned long recv_ID;
			while ((recv_ID = intuniform(0, N - 1)) == ID);
			TX tx(TX_CNT++, val, ID, recv_ID);
			//	����pbchain Ϊ��������֤��
			if (useCC && CCC.tail != nullptr)
				p->afterCC(CCC.tail->acb_height);
			p->addtxs(pb_chain,this->ID);
			tx_p_val->tx_num.at(p->val) = p->tx_cnt;
			tx.prf_str = p->prf_to_str();

			//д����
			const std::string  key = std::to_string(tx.tx_ID);
			std::string value = tx.tx_to_str();
			leveldb::Status status = TXDB->Put(leveldb::WriteOptions(), key, value);
			assert(status.ok());

			delete p; p = nullptr;
#ifdef test
			prf p(tx->prf_str);
			if (p.prf_to_str() != tx->prf_str) {
				recordError(error_typr::prf_type);
				// std::cout << tx.prf_str << std::endl << p.prf_to_str()<< std::endl;
			}
#endif
			tx_pool.push_back(key);
			//  �Ƴ���ֵ�Ͷ�Ӧ��prf
			val_prf.erase(val_prf.begin() + pos);
			//  TODO: ���ӽ���ʧ�ܺ󷵻�val�Ļ���
		}
		if (INF_POOL.size == 0 || val_prf.empty()) sendInf();
		
		// Ϊ��һ�η��������ɶ�ʱ��
		scheduleAt(this->ID, simTime() + poisson(k), msg);
		return 0;
	}

	// �����״��Ϊ���׼������͵����׳�
	int node::sendInf()
	{
		if (tx_pool.empty()) return 0;
		cMessage* i_msg = new cMessage("i_msg", inf_for_pack, MSG_ID++, this->ID);
		INF inf(this->ID);
		//pc_block* ptr = new pc_block();
#ifdef test
		std::set<unsigned long> se;
#endif
		while (!tx_pool.empty()) {
			auto tx_id = tx_pool.back();
			//������
			const std::string  key = tx_id;
			std::string value;
			leveldb::Status status = TXDB->Get(leveldb::ReadOptions(), key, &value);
			assert(status.ok());
			//std::cout << key << ":" << value << std::endl;

			TX tx(value);
			Prf p(value.substr(value.find(";")+1));
			if (p.prf_to_str() == "") {
				;
			}
			inf.tx_prf_vec.push_back(tx.tx_to_str() + p.prf_to_str() + "$");
			tx_pool.pop_back();
#ifdef test
			if (se.count(tx->val) > 0) recordScalar("dup tx", simTime());
			se.insert(tx.val);
#endif
		}
		TX_SEND_CNT += inf.tx_prf_vec.size();
		// �洢ժҪ-���׼���
		inf.abs = inf.getTxAbs();
		i_msg->setAbstract(inf.abs);
		//ptr->txs_abstract = inf.abs;
		//pb_map.insert(std::make_pair(inf.abs, ptr));

		const std::string  key = inf.abs;
		std::string value = inf.inf_to_str();
		leveldb::Status status = INFDB->Put(leveldb::WriteOptions(), key, value);
		assert(status.ok());

		string inf_data = inf.inf_to_str();
		i_msg->setData(inf_data);
		send(i_msg, this->ID);
		return 0;
	}

	/*
	*  ����hash��ʱ����������׳��еĽ��׼�����������
	*/
	int node::handlePow(cMessage* msg)
	{
		if (ACC.head == nullptr || pHigh == ACC.tail->height) {
			//  ���ɲ��㲥AC��
			cMessage* a_msg = new cMessage("acb", acb, MSG_ID++, this->ID);
			// ����AC��[�߶ȣ���ţ���һ��AC��ı�ţ��󹤱�ţ�ʱ���]
			ac_block* block = new ac_block(pHigh + 1, a_msg->getTreeId(), pID, this->ID, simTime());
			packandVerifyInf(block);
			string acb_data = block->block_2_str();
			
			// ����ACC
			block->prev = ACC.tail;
			if (ACC.head == nullptr) {
				block->prev = nullptr;
				ACC.head = block;
			}
			else block->prev = ACC.tail;
			ACC.tail = block;
			ACC.size++;
			// ����ίԱ��
			if (!in_committee) {
				in_committee = true;
				committee.insert(this->ID);
			}
			// �����ǰepochû��leader����Ϊleader
			if (leader_ID == N) {
				leader_ID = this->ID;
			}
			block_epoch++;
			// �㲥AC��
			a_msg->setData(acb_data);
			selfACBlock(block);
			send(a_msg, this->ID);
		}
		pID = ACC.tail->ID;
		pHigh = ACC.tail->height;
		// ���������������ɼ�ʱ��
		double time = randomExponential(round * N) + simTime();
		time < simTime() ? time = simTime() + round * N : (time > 9223372 ? time = 9223372 : time + 0);
		scheduleAt(this->ID, time, pow);
		return 0;
	}

	//�����յ������飬����pb����������һround�в����Ľ���
	int node::selfACBlock(ac_block* block) {
		unsigned long acb_high = block->height;
		ac_block* acp = ACC.tail;
		while (acp != nullptr && ac_cur < acp->height) {
			for (auto it = acp->A_vec.begin(); it != acp->A_vec.end(); ) {
				const std::string  key = *it;
				std::string value;
				leveldb::Status status = INFDB->Get(leveldb::ReadOptions(), key, &value);
				if (status.ok()) {
					INF* inf = INF::str_2_inf(value);
					// ���ÿ�ʽ��ף�֪ͨ���շ�������txn + prf��
					size_t sz = inf->tx_prf_vec.size();
					pc_block pcb(acb_high);
					if (sz == 0) {
						recordError(error_type::empty_prf);
					}
					std::vector<std::string> tx_vec;
					std::vector<std::string> prf_vec;
					for (auto str : inf->tx_prf_vec) {
						string tx_str = str.substr(0, str.find(';') + 1);
						string prf_str = str.substr(str.find(';') + 1);
						Prf p(prf_str);
						if (useCC && CCC.tail != nullptr)
							p.afterCC(CCC.tail->acb_height);
						p.addtxs(pb_chain, this->ID);
						tx_p_val->tx_num.at(p.val) = p.tx_cnt;
						tx_cc::add(CNT, p.tx_cnt);
						tx_vec.push_back(tx_str);
						prf_vec.push_back(p.prf_to_str());
					}
					for (int idx = 0; idx < tx_vec.size(); idx++) {
						TX tx(tx_vec.at(idx));
						cMessage* t_msg_i = new cMessage("receipt", t_msg_type, MSG_ID++, this->ID);
						receipt rec(this->ID, tx.recv_ID, acb_high);
						rec.prf = prf_vec.at(idx);
						rec.tx_idx = idx;
						rec.txs.assign(tx_vec.begin(), tx_vec.end());
						rec.tx = tx_vec.at(idx);
						string t_data = rec.receipt_to_str();

						t_msg_i->setData(t_data);
						send(t_msg_i, this->ID, tx.recv_ID);
						idx++;
					}
					std::vector<std::string>().swap(prf_vec);
					pcb.txs.assign(tx_vec.begin(), tx_vec.end());

					const std::string  key_2 = std::to_string(this->ID) + " " + std::to_string(pb_chain.size());
					std::string value = pcb.block_2_str();
					leveldb::Status status = PBDB->Put(leveldb::WriteOptions(), key_2, value);
					assert(status.ok());
					pb_chain.push_back(key_2);
					//it = acp->A_vec.erase(it);
					INFDB->Delete(leveldb::WriteOptions(), key);
				}
				
				// ����ժҪ�ҵ��ȴ�ȷ�ϵĽ��׼�
				// string s = *it;
//				auto itr = pb_map.find(s);
//				if (itr != pb_map.end()) {
//					// ���ÿ�ʽ��ף�֪ͨ���շ�������txn + prf��
//					size_t sz = itr->second->txs.size();
//					itr->second->height = acb_high;
//					if (itr->second->txs.empty()) {
//						recordError(error_type::empty_prf);
//					}
//					const std::string  key = std::to_string(this->ID) + " "+std::to_string(pb_chain.size());
//					std::string value = itr->second->block_2_str();
//					leveldb::Status status = PBDB->Put(leveldb::WriteOptions(), key, value);
//					assert(status.ok());
//					pb_chain.push_back(key);
//
//					for (size_t i = 0; i < sz; i++) {
//						cMessage* t_msg_i = new cMessage("receipt", t_msg_type, MSG_ID++, this->ID);
//						Prf* p = new Prf(itr->second->prfs.at(i));
//						TX* tx = new TX(itr->second->txs.at(i));
//						if (useCC && CCC.tail != nullptr)
//							p->afterCC(CCC.tail->acb_height);
//						p->addtxs(pb_chain,this->ID);
//						tx_p_val->tx_num.at(p->val) = p->tx_cnt;
//						tx_cc::add(CNT, p->tx_cnt);
//#ifdef test
//						std::cout << p.prf_to_str() << std::endl;
//						std::cout << tx_str << "*" << tx.recv_ID << std::endl;
//#endif
//						receipt rec(this->ID, tx->recv_ID, acb_high);
//						rec.prf = p->prf_to_str();
//						rec.tx_idx = i;
//						rec.txs.assign(itr->second->txs.begin(), itr->second->txs.end());
//						rec.tx = tx->tx_to_str();
//						string t_data = rec.receipt_to_str();
//						
//						t_msg_i->setData(t_data);
//						send(t_msg_i, this->ID, tx->recv_ID);
//						delete p; delete tx;
//						// std::cout << p.prf_to_str() <<std::endl << p.prf_to_str()<< std::endl << t_msg_i->getPrf()<< std::endl;
//					}
//					//it = acp->A_vec.erase(it);
//					pb_map.erase(itr);
//				}
				it++;
			}
			acp = acp->prev;
		}
		if (ACC.tail != nullptr)
			ac_cur = ACC.tail->height;
		return 0;
	}

	/*
	ͬ�����飬����pb����������һround�в����Ľ���
	*/
	int node::handleACBlock(cMessage* a_msg) {
		// �жϸ������Ƿ�Ϊ��ǰ���ڵĵ�һ��AC�飬����ǣ�������leader
		string data = a_msg->getData();
		ac_block* racb = ac_block::str_2_block(data);
		unsigned long send_ID = racb->node_ID;
		if (leader_ID == N && ACC.tail != nullptr) {
			leader_ID = send_ID;
		}
		committee.insert(send_ID);
		block_epoch++;
		//    ���������е�Inf������ժҪ�ȶ��Ƿ����Լ����͵ĵȴ������Ľ��ף�����У��������������֪ͨ���սڵ�
		selfACBlock(racb);

		// ������һround�в����Ľ���
		if (!tx_pool.empty() && INF_POOL.size == 0)sendInf();
		delete a_msg; a_msg = nullptr;
		cancelEvent(pow);
		if (ACC.tail != nullptr) {
			pID = ACC.tail->ID;
			pHigh = ACC.tail->height;
		}
		double time = randomExponential(round * N) + simTime();
		time <= simTime() ? time = simTime() + round * N : (time > 9223372 ? time = 9223372 : time + 0);
		scheduleAt(this->ID, time, pow);
		return 0;
	}

	// ��֤���׵���Ч�ԣ����A_i(x)����ʱ�洢inf��Inf_cc
	int node::packandVerifyInf(ac_block* block) {
		if(INF_POOL.size == 0){
			recordError(inf_empty);
		}
		while (INF_POOL.size > 0) {
			cMessage* i_msg = INF_POOL.head;
			INF_POOL.head = INF_POOL.head->getNextMsg();
			INF_POOL.size--;
			string inf_data = i_msg->getData();
			INF* inf = INF::str_2_inf(inf_data);
			string abs = i_msg->getAbstract();
			unsigned long oID = inf->node_ID;

			//tx_on_chain_cnt += i_msg->getTxsArraySize();
			if (verify(inf,abs)) {
				// ���������
				block->A_vec.push_back(inf->abs);

				if (block->node_filter.find(oID) == block->node_filter.end()) {
					block->node_filter.insert(std::make_pair(oID, true));
				}
				size_t sz = inf->tx_prf_vec.size();
				if (Inf_sz.empty()) {
					Inf_sz.push_back(sz);
				}
				else {
					Inf_sz.front() += sz;
				}
				Inf_sz.push_back(sz);
				inf->height = ACC.size;
				inf_data = inf->inf_to_str();
				i_msg->setData(inf_data);
				Inf_cc.push_back(i_msg);
				delete inf; inf = nullptr;
			}
			else { // δͨ�����
				recordScalar("Inf wrong", simTime());
				//i_msg->setKind(Inf_pack_fail);
				//send(i_msg, this->ID);
			}
		}
#ifdef test
		if(Inf_sz.empty()){
			recordScalar("inf_sz  ",block.A_vec.size());
		}
		else{
			recordScalar("inf_sz  ",simTime());
		}
#endif
		//  �Լ������Ľ���
		ABS_CNT += block->node_filter.size(); // ���׼�������
		// if(!Inf_sz.empty()) _tx_num_spzce = Inf_sz.front() + tx_pool.size();
		if (!tx_pool.empty())    sendInf();
		return 0;
	}

	// TODO:��֤inf
	bool node::verify(INF* inf, string abstract)
	{
#ifdef light
		return true;
#endif
		
		bool flag = true;
		// ��֤A_i(x)
		string inf_abs = inf->getTxAbs();
		if (inf_abs != abstract) {
			recordError(error_type::inf_abs);
			return false;
		}
		// ��֤���׼���û�зǷ����ף�GetOwner��
		for(auto str : inf->tx_prf_vec){
			size_t to = str.find_last_of("$");
			size_t from = str.find_first_of(';') + 1;
			str = str.substr(from,to-from);
			Prf* p = new Prf(str);
			if(!getprfOwner(p)){
				recordError(error_type::prf_type);
				return false;
			}
			p->~Prf();
		}
		return flag;
	}

	// ���ܽڵ��鲢ȷ�Ͻ��ף����¼�ֵ����Ӧ��prf
	int node::handleRecvtx(cMessage* tx_msg) {
		string t_data = tx_msg->getData();
		size_t from = t_data.find(';') + 1;
		string prf_str = t_data.substr(from);
		Prf* p = new Prf(prf_str);
		if(GetOwner(p, tx_msg, 0))
			val_prf.push_back(p);
		delete tx_msg; tx_msg = nullptr;
		return 0;
	}

/*
 * Proof
 * 1.�ҵ�~t���ڼ�ֵV_j���һ����CC�㷨��¼��ת��ʱ�̴���V_j��ת�ƴ�����
 * index = ~t
 * ��index <= i��iΪ��ǰV_j�Ѿ�������ת�ƴ�����
 *  w = u_index(��index��ת�Ʒ�����ʱ��)��conut = 0
 *  ���wʱ�̵��������Ƿ��¼�ҽ���¼һ��w��ת��
 *  ���� w <= u_index+1(����һ��ת�Ʒ�����ʱ��)�������
 */

 // TODO
	bool node::getprfOwner(Prf* prf) {
		return true;
	}
	bool node::getprfOwner(string tx_str, string prf_str, cMessage* c_msg, size_t idx) {
		return true;
	}
	bool node::checkAbstract(unsigned long prev_high, unsigned long high, unsigned long oID, std::vector<TX*> &txs, string &txs_abs){
		
		ac_block* acp = ACC.tail;
		while (acp->height != high) {
			acp = acp->prev;
			if (acp == nullptr)
				return false;
		}
		ac_block* ac_at_high = acp;
		if (prev_high < high) {
			std::vector<ac_block*> acc_vec;
			while (acp->height != prev_high) {
				if (acp->height < high) acc_vec.push_back(acp);
				acp = acp->prev;
				if (acp == nullptr)
					return false;
			}
			// ��� prev_high �� high ���Ƿ񲻴������� oID�Ľ��׼�
			for (auto ac_it : acc_vec) {
				if (ac_it->node_filter.find(oID) != ac_it->node_filter.end())
					return false;
			}
		}

		// ���ݽ��׼�����ժҪ,��AC���ϼ�¼��ժҪ���ж���
		string txs_str;
		for (auto t : txs) {
			txs_str += t->tx_to_str();
		}
		txs_abs = Cryptography::GetHash(txs_str.c_str(),txs_str.size());
		for (auto abs : ac_at_high->A_vec) {
			if (abs == txs_abs) return true;
		}
		return false;
	}

	// ���prf�ĸ�ʽ�Ƿ����
	bool node::prf_structure(Prf* prf) {
		bool flag = true;
		if (!flag) {
			recordError(prf_type);
		}
		return flag;
	}

	// ���սڵ����prf�жϼ�ֵ�ĳ�����,���������м�¼
	bool node::GetOwner(Prf* prf, cMessage* t_msg, int state) {
#ifdef light
		return true;
#endif // light

		//    bool flag = true;
		int type = 0; // ��¼���������
		// ����ʽ
		if (!prf_structure(prf)) {
			return false;
		}

		unsigned long val = prf->val;
		string t_data = t_msg->getData();
		receipt* rep = receipt::str_to_receipt(t_data);
		unsigned long sendID = rep->sendID;
		unsigned long last_height = rep->height; // ���һ�ν������ڵ�����
		string tx_str = rep->tx;
		TX cur_tx(tx_str);
		if (cur_tx.recv_ID != ID) {
			recordError(recv_node);
			return false;
		}

		// ��prf�м�¼�ĵ�һ�����׼���ʼ�����ý��׼����������Ƿ��Ѿ�����CC�㷨���
		// ���߸ÿ��Ƿ��Ǹü�ֵ�Ĵ�ʼ��(�����׼�����û�кϷ��Ŀ�ͷ)
		// TODO AC������μ�¼���ҵĴ�����Ϣ��
		std::vector<std::vector<TX*>>::iterator txs_it = prf->txs_vec.begin();// ��prf�м�¼�ĵ�һ�����׼���ʼ
		size_t idx = txs_it - prf->txs_vec.begin();
		unsigned long high = prf->txs_h.at(idx);// ��ý��׼����ڵ�AC��ĸ߶�
		cc_block* cc_it = CCC.tail;
		if (cc_it != nullptr) {
			//std::cout << simTime() << std::endl << high << std::endl << cc_it->acb_height << std::endl;
			if (high > cc_it->acb_height && prf->init_ID != (*txs_it->begin())->owner_ID) {
				recordError(init_high);
				delete rep; rep = nullptr;
				return false;
			}
			while (cc_it->prev != nullptr && cc_it->prev->acb_height >= high) {
				cc_it = cc_it->prev;
			}
			// ��ʱcc_itָ�������prf�е�һ�����׼����CC��
		}
		// ���ݳ��������α���prf�а����Ľ��׼�
		//    !!!�˴��Ľ��׼������漰����Ӧ��ֵ�Ľ��׾�Ӧ�������������CC��֮�󣬳��Ǹý��ױ���¼��ĳ��CC����
		unsigned long cnt, oID; // ��¼��ֵ��һ�����������еĽ��״���;��ǰ������ID
		while (txs_it != prf->txs_vec.end()) {
			if (txs_it->size() == 0) {
				recordError(empty_prf);
				txs_it++; continue;
			}
			std::vector<TX*>& prf_txs_vec = *txs_it;
			cnt = 0;
			oID = (*txs_it->begin())->owner_ID;
			// ���μ��ĳһ�������ߵ�ÿ�����׼�
			while (txs_it != prf->txs_vec.end() && oID == (*txs_it->begin())->owner_ID && cnt == 0) {
				idx = txs_it - prf->txs_vec.begin();
				auto prev_high = high;
				high = prf->txs_h.at(idx);
				string txs_abs;
				// ���prf�����ĺϷ��ԣ�����������)
				if (!checkAbstract(prev_high, high, oID, prf->txs_vec.at(idx), txs_abs)) {
					recordError(prf_incomplete);
					delete rep; rep = nullptr;
					return false;
				}
				// ���¼���
				while (high > prev_high && cc_it != nullptr && high > cc_it->acb_height) {
					cc_it = cc_it->next;
				}
				// ��齻�׼��е����н���
				for (auto tx : *txs_it) {
					if (tx->val == val) { // �����漰���ü�ֵ�Ľ���
						bool is_valid = true;
						if (cc_it != nullptr && cc_it->fail_txs.find(txs_abs) != cc_it->fail_txs.end()) { // ���CC�鿴�ý����Ƿ���Ч
							auto i = cc_it->fail_txs.find(txs_abs)->second;
							if (i != -1) {
								for (auto tx_str : cc_it->fail_txn.at(i)) {
									if (tx_str == tx->tx_to_str()){
										is_valid = false;
										break;
									}
								}
							}
							else { // �������׼�������Ч��
								break;
							}
						}
						// ������Ч�Ľ��ף���¼��ʹ�ô���
						is_valid ? cnt++: cnt;
					}
				}
				txs_it++;
			}
			//return true;
			if (cnt != 1) {
				if (cnt > 1) 
					recordError(double_spent);
				else recordError(not_spend);
				delete rep; rep = nullptr;
				return false;
			}
		}
		if (oID != sendID) {
			recordError(wrong_owner);
			delete rep; rep = nullptr;
			return false;
		}
		delete rep; rep = nullptr;
		return true;
	}

/*
 *  ����ΪCC�㷨
 *  1.��ʼ��CB_l��ίԱ���leader
 *  2.ȷ��ǰl-1��CC�㷨�Ѿ����
 *  3.���ݱ���AC�飬��ίԱ���ڹ㲥ǩ����inf���ȴ�gama_1
 *  4.���ݱ���AC����û���յ���inf����CB_l�������յ���inf��������н����Ƿ�Ϸ�
 *  5.ѡ��leader��leader�㲥ǩ���ı���CB_l������ÿ���ίԱ���ڰ���ǩ��������Ч
 *  ����leaderû���ڹ涨ʱ��gama_2������������������½���leaderѡ�٣�
 *  6.leader��ȫ���㲥��Ч��CB_l�᰸
 *  7.�ڹ涨ʱ��gama_3�ڣ�����ڵ���ԶԱ�������CB_l�е��������׽������ߣ��ṩproof��
 *  8.ίԱ����ÿ���ڵ������֤���ߵĺϷ��ԣ�GetOwner����+ǩ���������ӱ���CB_l���Ƴ����߳ɹ��Ľ���
 *  9.leader��ίԱ���ڹ㲥����CB_l���ٴ�����ǩ���󣨹涨ʱ��gama_4������ȫ���㲥��
 *  10.�յ���ЧCB_l�Ľڵ㽫�����ӵ�����CC����
 */

	// CC�㷨�ļ�ʱ��
	int node::handleTtimer(cMessage* T_msg) {
		// ����ڵ㱾����ίԱ���У�����CC�㷨
		in_CC = false;
		if (in_committee) {
			//recordScalar("in comm",simTime());
			initializeCC();
			broadcastInf();
		}
		in_committee = false; // ��ֹ��CC�ڼ�����µ�AC��
		leader_ID = N;
		block_epoch = 0;
		// ���Inf_cc �� Inf_sz
		for (auto c : Inf_cc) {
			if (c != nullptr) {
				delete c; c = nullptr;
			}
		}
		Inf_cc.clear();
		Inf_sz.clear();
		for (auto c : abs_set) {
			c.~basic_string();
		}
		abs_set.clear();
		for (auto c : sig_set) {
			if (c.second != nullptr) {
				delete c.second; c.second = nullptr;
			}
			c.first.~basic_string();
		}
		sig_set.clear();
		gState = 0;
		// �������ü�ʱ��
		scheduleAt(this->ID, simTime() + T, T_msg);
		return 0;
	}

	// leaderѡ��
	void node::getLeader(unsigned long cnt = 0) {
		ac_block* acp = ACC.tail;
		while (acp->height > cb_ptr->acb_height) {
			acp = acp->prev;
			if (acp == nullptr) {
				recordError(error_type::acc_height);
				exit(-1);
			}
		}
		cnt = cb_ptr->block_epoch - 1 - cnt;
		for (unsigned long i = 0; i < cnt; i++) {
			acp = acp->prev;
			if (acp == nullptr) {
				recordError(error_type::acc_height);
				exit(-1);
			}
		}
		leader_ID_CC = acp->node_ID;
		return;
	}

	// ��ʼ��CB_l,ȷ��ǰl-1��CC�㷨�Ѿ����
	int node::initializeCC() {
		in_CC = true;
		leader_ID_CC = leader_ID;

		Inf_collect = new cMessage("ccb-1",ccb_1,MSG_ID++, this->ID);
		//  TODO:wait for l-1;
		unsigned long h = 0;
		if (CCC.tail != nullptr) h = CCC.tail->height + 1;
		unsigned long cc_prevID;
		CCC.tail == nullptr ? cc_prevID = 0 : cc_prevID = CCC.tail->ID;
		unsigned long cc_ID = Inf_collect->getTreeId();
		if (cc_ID == 0) cc_ID++;
		cb_ptr = new cc_block(h, cc_ID, cc_prevID, ID, pHigh, block_epoch, simTime());
		getLeader();
		return 0;
	}

	// ���ݱ���AC������ίԱ���ڹ㲥ǩ����inf(��������һepoch���ռ���������)���ȴ�gama_1(��¼CCPT)
	int node::broadcastInf() {
		if (ACC.tail == nullptr) {
			recordScalar("empty acc", simTime());
			return -1;
		}
		if (Inf_sz.empty()) {
			recordScalar("empty Inf_CC", simTime());
			return -1;
		}
		size_t txs_size = Inf_cc.size();// ���׼��ĸ���
		size_t tx_size = Inf_sz.front(); // ���н��׼��а����Ľ�������

		//����Inf_cc��������׼�
		size_t idx = 0;
		size_t tx_cnt = 0;
		std::set<unsigned long> val_set;
		while (idx < txs_size) {
			cMessage* i_msg = Inf_cc.front(); Inf_cc.pop_front();
			string i_data = i_msg->getData();
			INF* inf = INF::str_2_inf(i_msg->getData());
			// ���׼���ժҪ����С��������AC��ĸ߶�
			size_t tx_sz = Inf_sz.at(idx + 1);
			cb_ptr->fail_txs.insert(std::make_pair(inf->abs,inf->height));
			cb_ptr->fail_txn.push_back(inf->tx_prf_vec);
			for (int i = 0; i < tx_sz; i++, tx_cnt++) {
#ifndef whole
				string prf_str = inf->tx_prf_vec.at(i);
				prf_str = prf_str.substr(prf_str.find(';') + 1);
				Prf p(prf_str);
				int vID = p.val;
				if (val_set.count(p.val) == 0) {
					val_set.insert(p.val);
					if (CCC.tail != nullptr && !p.txs_h.empty() && useCC) {
						p.afterCC(CCC.tail->acb_height);
						if (p.txs_h.front() < CCC.tail->acb_height)
							tx_cc::add(CNT,committee.size());
					}
				}
				p.~Prf();
#endif
			}
			delete inf; inf = nullptr;
			idx++;
		}
		string data = cb_ptr->block_2_str();
		Inf_collect->setData(data);

#ifdef whole
		cb_ptr->Clear();
		send(Inf_collect, this->ID);
#endif

#ifndef whole
		// lightģʽ�£�ֱ����leader����
		tx_cc::add(CNT, committee.size() * tx_cnt);
		delete Inf_collect; Inf_collect = nullptr;
		// recordScalar("leader",leader_ID_CC);
		if (leader_ID_CC == ID) {
			cb_ptr->txn_cnt = intuniform(0, 1);
			cb_ptr->fail_txn.clear();
			cb_ptr->fail_txs.clear();
			Inf_collect = sendCCblock(ccb_2);
			send(Inf_collect, this->ID);
		}
		else {
			//cMessage* p_msg = new cMessage("inf_collect", light_Inf, MSG_ID++, this->ID);
			//string data = cb_ptr->block_2_str();
			//p_msg->setData(data);
			//scheduleAt(this->ID, simTime() + gama_1+gama_2, p_msg);
			//cb_ptr->~cc_block();
		}
		// ���ö�ʱ�� gama_1������CB
		gState = 2;
		return 2;
#endif
		gState = 1;
		gTimer = new cMessage("g1_msg", g1, MSG_ID++, this->ID);
		scheduleAt(this->ID, simTime() + gama_1, gTimer);
		return 0;
	}

	// �ռ�����ίԱ���Ա�����Ľ��׼�����¼��ժҪ����齻�׼��н��׵ĺϷ��ԣ���¼�Ƿ�����
	int node::collectInf(cMessage* msg) {
		if (!in_CC) {
			delete msg; msg = nullptr;
			return -1;
		}
		string data = msg->getData();
		cc_block* cc = cc_block::str_2_block(data);
		size_t txs_sz = cc->fail_txs.size(); //���׼���
		size_t txn_sz = cc->fail_txn.size(); //�ܽ�����

		size_t idx = 0;
		size_t tx_cnt = 0;
		// ��ÿ�����׼�����¼��ժҪ
		for (auto p : cc->fail_txs) {
			string abs = p.first;
			abs_set.insert(abs);
		}
		std::vector<string> temp;
		for (auto t_vec : cc->fail_txn) {
			bool flag = true;
			string txs_str;
			for (auto t_str : t_vec) {
				size_t from = t_str.find(';');
				string tx_str = t_str.substr(0, from);
				size_t to = t_str.find_last_of("$");
				string prf_str = t_str.substr(from+1,to - from -1);
				unsigned long txcnt = stoul(prf_str.substr(prf_str.find_last_of("-") + 1));
				tx_cc::add(CNT, tx_cnt);
				txs_str += tx_str;
				// ��û��ͨ���Ľ��׼���CC��
				if (!getprfOwner(tx_str, prf_str, msg, idx)) {
					flag = false;
					cb_ptr->txn_cnt++;
					size_t txs_i;
					temp.push_back(tx_str);
				}
				
			}
			if (!flag) {
				string abs = Cryptography::GetHash(txs_str.c_str(), txs_str.size());
				size_t txs_i = cb_ptr->fail_txn.size();
				cb_ptr->fail_txs.insert(std::make_pair(abs,txs_i));
				cb_ptr->fail_txn.push_back(temp);
			}
			temp.clear();
		}
		delete msg; msg = nullptr;
		return 0;
	}

	// gama_1��ʱ������AC���ϵ�ժҪ��¼δ�յ��Ľ��׼�
	int node::handleGama_1(cMessage* msg) {
		if(!in_CC) return -1;
		//�������ֵ�AC�飬��û����gama_1���յ���ժҪ��¼��CC����
		ac_block* acp = ACC.tail;
		while (acp != nullptr && acp->height != cb_ptr->acb_height) {
			acp = acp->prev;
		}
		auto prev_high = (cb_ptr->prev == nullptr ? 0 : cb_ptr->prev->acb_height);
		while( acp != nullptr && acp->height > prev_high) {
			// ����AC���ϵ�ժҪ���ҵ�����abs_set�еģ��������CC��
			for (auto a_it : acp->A_vec) {
				if (this->ID != acp->node_ID && abs_set.find(a_it) == abs_set.end()) {
#ifdef test
					recordScalar("inf not found in CC", simTime());
#endif
					if (cb_ptr->fail_txs.find(a_it) == cb_ptr->fail_txs.end())
						cb_ptr->fail_txs.insert(std::make_pair(a_it, -1));
					else cb_ptr->fail_txs.at(a_it) = -1;
				}
			}
			acp = acp->prev;
		}
		if (cb_ptr->prev != nullptr &&  acp == nullptr) {
			recordError(error_type::acc_begin);
		}

		gState = 2;
		// �ж��Լ��Ƿ���leader�����������������CC��
		if (leader_ID_CC == this->ID) {
			Inf_collect = sendCCblock(ccb_2);
			send(Inf_collect, this->ID);
		}
		else {
			delete Inf_collect; Inf_collect = nullptr;
			abs_set.clear();
			// ���ü�ʱ��gama_2
			gTimer = new cMessage("g2_msg", g2, MSG_ID++, this->ID);
			scheduleAt(this->ID, simTime() + gama_2, gTimer);
		}
		delete msg; msg = nullptr;
		return 0;
	}

	// ���ͱ���CC��
	cMessage* node::sendCCblock(int kind) {
		// recordScalar("send ccb-2",simTime());
		cMessage* c_msg = new cMessage("leader draft",kind, MSG_ID++, this->ID);
		tx_cc::add(CNT, cb_ptr->txn_cnt);
		string data = cb_ptr->block_2_str();
		c_msg->setData(data);
		return c_msg;
	}


	// ��ʱ��gama_2������Leaderδ��ʱ���飬���½���ѡ��
	int node::handleGama_2(cMessage* msg) {
		gTimer = msg;
		// ��ίԱ����ѡ����һλ��Ϊleader
		if (gState != 2) {
			delete gTimer;
			gTimer = nullptr;
			return -1;
		}
		getLeader(1);
		// �������ü�ʱ��
		if (leader_ID_CC == ID) {
			recordScalar("g2", gState);
			sendCCblock(ccb_2);
		}
		else {
			// ���ü�ʱ��gama_2
			gTimer->setKind(g2);
			scheduleAt(this->ID, simTime() + gama_2, gTimer);
		}
		return 0;
	}


	// ����leader���᰸������
	int node::handleCCB_2(cMessage* c_msg) {
		string data = c_msg->getData();
		cc_block* cc = cc_block::str_2_block(data);
		if (!in_CC || leader_ID_CC != cc->node_ID) {
			delete c_msg; c_msg = nullptr;
			return -1;
		}
		string scalar = "CCB_2: " + std::to_string(this->ID);
		recordScalar(scalar.c_str(),simTime());
		bool flag = true;
		// ��������CCB�Ƚ� TODO

		if (flag) {
			signCCB(c_msg);
		}
		delete c_msg; c_msg = nullptr;
		delete cc; cc = nullptr;

		return 0;
	}

	// ��CCB����ǩ��������
	int node::signCCB(cMessage* c_msg) {
		//recordScalar("signCCB",simTime());
		cMessage* s_msg = new cMessage("sig",sig,MSG_ID++, this->ID);
		sigclass* sigp = new sigclass(c_msg->getID(),this->ID,leader_ID_CC,simTime(),c_msg->getKind()+1);
		string s_data = sigp->sig_to_str();
		string s_hash = Cryptography::GetHash(s_data.c_str(), s_data.size());
		s_msg->setData(s_data);
		s_msg->setAbstract(s_hash);
		send(s_msg, this->ID);
		delete sigp; sigp = nullptr;
		return 0;
	}

	// leader ����sigΪ����ǩ����BLS?��
	int node::handleSig(cMessage* s_msg) {
		string s_data = s_msg->getData();
		sigclass* sigp = sigclass::str_to_sig(s_data);
		if (leader_ID_CC != ID || sigp->recv_Node != ID || gState == 3 || gState == 5) {
			delete sigp; sigp = nullptr;
			return 0;
		}
		string sig = s_msg->getAbstract();
		if (sig_set.find(sig) == sig_set.end()) {
			sig_set.insert(std::make_pair(sig, s_msg));
		}
		string scalar = "sig set: " + std::to_string(sig_set.size()) + "\t" + std::to_string(committee.size() / 2);
		recordScalar(scalar.c_str(),this->ID);
		// ����ռ������㹻��ǩ��������֤����ǩ��,��ͨ�����㲥CCB
		if (sig_set.size() > committee.size() / 2 && verifyThreholdSig()) {
			gState < 3 ? gState = 3 : gState = 5;
			recordScalar("sig",leader_ID_CC);
			Inf_collect = sendCCblock(sigp->kind);
			// if(s_msg->getCcbkind() ==  ccb_2+1)
			send(Inf_collect, this->ID);
			tx_cc::add(CNT,cb_ptr->txn_cnt);

			if (sigp->kind == ccb_3) {
				gTimer = new cMessage("gama_3",g3,MSG_ID++, this->ID);
				scheduleAt(this->ID,simTime()+gama_3, gTimer);
			}
		}
		delete sigp; sigp = nullptr;
		return 0;
	}

	// ��������leader��CB���᰸����������漰�����Ľ���
	int node::handleCCB_3(cMessage* msg) {
		gState = 3;
		if (in_CC) {
			// if(gTimer->isScheduled())
			// cancelEvent(gTimer);
			gTimer = new cMessage("gama_3",g3,MSG_ID++, this->ID);
			scheduleAt(this->ID, simTime() + gama_3, gTimer);
		}
		//TODO ��������漰�����Ľ���
		string data = msg->getData();
		cc_block* cc = cc_block::str_2_block(data);
		int txn_cnt = cc->txn_cnt;
		tx_cc::add(CNT,txn_cnt);

		delete msg; msg = nullptr;
		delete cc; cc = nullptr;
		return 0;
	}

	// ������CB�᰸�����ߣ�����leader �����µ��᰸��ίԱ�����
	int node::handleGama_3(cMessage* msg) {
		if (!in_CC) {
			return -1;
		}
		gState = 4;
		// �ж��Լ��Ƿ���leader�����������������CC��
		sig_set.clear();
		if (leader_ID_CC == ID) {
			Inf_collect = sendCCblock(ccb_4);
			send(Inf_collect->dup(MSG_ID++), this->ID);
		}
		else {
			// ���ü�ʱ��gama_4
			gTimer = new cMessage("gama_4", g4, MSG_ID++, this->ID);
			scheduleAt(this->ID, simTime() + gama_4, gTimer);
		}
		delete msg; msg = nullptr;
		return 0;
	}

	// �ٴα���
	int node::handleCCB_4(cMessage* c_msg) {
		if (!in_CC) {
			delete c_msg; c_msg = nullptr;
			return -1;
		}
		//recordScalar("handle CCB_4",simTime());
		bool flag = true;
		// ��������CCB�Ƚ� TODO

		if (flag) {
			signCCB(c_msg);
		}
		delete c_msg; c_msg = nullptr;

		return 0;
	}

	// �������յ�CCB
	int node::handleCCB(cMessage* c_msg) {
		//ccb_msg* c_msg = (ccb_msg*)msg;
		string data = c_msg->getData();
		cc_block* cc = cc_block::str_2_block(data);
		if (this->ID == cc->node_ID && leader_ID_CC == this->ID) {
			if (CCC.head == nullptr) {
				CCC.head = cb_ptr; CCC.tail = cb_ptr;
				CCC.size++;
			}
			else if(CCC.tail->height < cb_ptr->height){
				CCC.tail->next = cb_ptr;
				cb_ptr->prev = CCC.tail;
				CCC.tail = cb_ptr;
				CCC.size++;
			}
			recordScalar("CCB size", CCC.size);
		}

		// ÿ���ڵ���Լ�������val������
		for (auto p_it : val_prf) {
			p_it->afterCC(cc->acb_height);
		}
		delete c_msg; c_msg = nullptr;
		delete cc; cc = nullptr;
		leader_ID_CC = N;
		gState = 0;
		committee.clear();
		for (auto c : abs_set) {
			c.~basic_string();
		}
		abs_set.clear();
		for (auto c : sig_set) {
			if (c.second != nullptr) {
				delete c.second; c.second = nullptr;
			}
			c.first.~basic_string();
		}
		sig_set.clear();
		gState = 0;
		in_CC = false;
		return 0;
	}

	// ��֤�ۺ�ǩ�� TODO
	bool node::verifyThreholdSig() {
		return true;
	}

	// ���������ͳ������
	int node::statistic(staticticStruct* sta)
	{
		sta->CCPT = tx_cc::CCPT(CNT, TX_SEND_CNT);
		sta->ACC_storage = ABS_SZ * ABS_CNT;
		useCC ? sta->CCC_storage = CCB_SZ * CCC.size: sta->CCC_storage = 0;
		sta->PBC_storage = tx_p_val->get_mean(N) * TX_SZ;
		return 0;
	}

}// namespace
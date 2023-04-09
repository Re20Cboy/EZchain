#include <vector>
#include <string>

#include "msg.h"
#pragma warning(disable:4996)

namespace ezchain {
	cMessage::cMessage(const char* name, short kind, const long ID, const int nodeID):msgName(name), ID(ID), TreeID(ID),nodeID(nodeID) {
		this->msgKind = kind;
		this->next = nullptr;
	}

	const char* cMessage::getName() const {
		return this->msgName;
	}

	short cMessage::getKind() const {
		return this->msgKind;
	}

	std::string cMessage::getData() const
	{
		return this->data->data;
	}

	double cMessage::getEvtTime() const
	{
		return this->evtTime;
	}

	int cMessage::getNodeID() const
	{
		return this->nodeID;
	}

	std::string cMessage::getAbstract() const
	{
		return this->abstract;
	}

	long cMessage::getID() const
	{
		return this->ID;
	}

	long cMessage::getTreeId() const
	{
		return this->TreeID;
	}

	cMessage* cMessage::getNextMsg() const
	{
		return this->next;
	}

	cMessage::cMessage(const cMessage& other, const long ID):msgName(other.getName()), ID(ID),TreeID(other.getTreeId()),nodeID(other.nodeID) {
		this->msgKind = other.getKind();
		this->next = other.getNextMsg();
		this->abstract = other.getAbstract();

		other.data->cnt++;
		this->data = other.data;
	}

	cMessage::cMessage(const cMessage& other, const long ID,const int nodeID) :msgName(other.getName()), ID(ID), TreeID(other.getTreeId()), nodeID(nodeID) {
		this->msgKind = other.getKind();
		this->next = other.getNextMsg();
		this->abstract = other.getAbstract();

		other.data->cnt++;
		this->data = other.data;
	}

	cMessage::~cMessage() {
		if(this->data != nullptr)
			this->data->subCnt();
	}
}
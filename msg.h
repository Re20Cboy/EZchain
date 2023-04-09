#ifndef __DEMO_MSG_H
#define __DEMO_MSG_H
#include <vector>
#include <string>

namespace ezchain {
    class msgData{
    public:
        size_t cnt;
        std::string data;
        msgData(std::string& d):data(d){
            cnt = 1;
        };
        virtual ~msgData() {
            data.~basic_string();
        }
        void subCnt() {
            if (cnt > 0)
                cnt--;
            else {
                this->~msgData();
            }
        }
    };

    class cMessage {
    protected:
        const char* msgName;
        const long ID;
        const long TreeID;
        const int nodeID;
        short msgKind;
        msgData* data = nullptr;
        //std::string data;
        std::string abstract;
        cMessage* next;
        double evtTime = 0;
    private:
        //void copy(const cMessage& other);

    protected:
        // protected and unimplemented operator==(), to prevent accidental usage
        //bool operator==(const cMessage&);

    public:
        cMessage(const char* name, short kind, const long ID, const int nodeID);
        cMessage(const cMessage& other, const long ID);
        cMessage(const cMessage& other, const long ID, const int nodeID);
        virtual ~cMessage();
        cMessage* dup(const long ID) const { return new cMessage(*this,ID); };

        int setKind(short kind) { msgKind = kind; return 0; };
        int setData(std::string& d) {
            if(this->data != nullptr) this->data->subCnt();
            this->data = new msgData(d); 
            return 0; 
        };
        int setAbstract(std::string& abs) { this->abstract = abs; return 0; };
        int setNext(cMessage* nextMsg) { this->next = nextMsg; return 0; };
        int setEvtTime(double time) { this->evtTime = time; return 0; };

        const char* getName() const;
        short getKind() const;
        long getID() const;
        long getTreeId() const;
        std::string getData() const;
        std::string getAbstract() const;
        cMessage* getNextMsg() const;
        double getEvtTime() const;
        int getNodeID() const;
    };
}

#endif // !__DEMO_MSG_H

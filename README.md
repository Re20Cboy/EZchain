# EZchain: A Secure Scalable Blockchain Protocol via Passive Sharding

======================================（Please skip to the next horizontal line to view the API and other documents）======================================
=======================================================（阅读API等说明文档请直接跳转至下一条横线处）==========================================================
EZchain is a layer-1 blockchain protocol that aims to "scale-out."
---
INTRODUCTION - We present EZchain, a scalable blockchain protocol via "passive sharding" with proven validity and security. We redesigned the Value-Centric Blockchains (VCB) framework to achieve passive sharding, which helps EZchain achieve higher security than traditional sharding protocols. With fixed initialization parameters, the expected value of EZchain's communication cost reaches a constant level, independent of the network's size. Moreover, EZchain node's storage cost without beacon chains also approaches a constant and does not change with the increase of network size and transactions. Cross-shard transactions, network sharding algorithms, and anti-Sybil attack verification are no longer needed in passive sharding, making EZchain concise and efficient.
---
EZchain是一个Layer-1层的区块链协议，旨在达到“无限扩展”的性能。
简介-我们提出了EZchain，这是一种通过“被动分片”实现的“无限扩展”区块链协议，其具有经验证和证明的有效性和安全性。我们重新设计了价值中心区块链（Value-Centric Blockchains，VCB）框架，以实现被动分片，这有助于EZchain实现比传统分片协议更高的安全性。在固定合适的初始化参数下，EZchain节点的通信开销可以达到常数水平，且与网络规模（节点数）无关。此外，在不考虑信标链的情况下，EZchain节点的存储成本也接近常数，并且不会随着网络规模和交易数量的增加而变化。被动分片不再需要处理跨分片交易、分片分割算法和抗女巫攻击验证，使EZchain更加简洁高效。
---

作者的话：EZchain是自19年就开始构思并完成主体设计的，遵从去中心化原教旨主义的区块链共识协议。它重点关注底层创新的共识算法，以达到在不可能三角（安全、去中心化、效率）中寻求突破。我们坚持高度去中心化的设计，并保证了“无限扩展”的性能。但EZchain主要针对交易场景，并且在应用层面可能存在未知的设计缺点，我们也诚恳邀请大家一起帮助我们完善EZchain的底层设计。感谢所有为去中心化作出过贡献的人们！

===========================================================================================================================================================
===========================================================================================================================================================


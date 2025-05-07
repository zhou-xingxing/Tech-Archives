一个很好的Raft入门动画演示网站
https://thesecretlivesofdata.com/raft/

Raft官方网站
https://raft.github.io/
# 解决什么问题
复制状态机
复制日志

# 算法限制

Raft算法的安全性建立在以下假设前提条件：
1. **节点是诚实的**：即不会恶意伪造信息，也不会伪造自己的身份。
2. **网络是非拜占庭模型**：即最多会出现延迟、分区、丢包，但不会篡改消息内容。


# Leader选举
## 挑选最好的Leader
最好的leader是有最新提交记录的节点，Candidate向其他节点发送VoteRequest时，会携带自己最新已提交日志的Term+Index，其他节点会与自己的进行比较，若Candidate已提交日志比自己的旧，则拒绝为其投票。

结果就是赢得选举的服务器可以保证比大多数投票者有更完整的日志记录。该机制保证了新Leader永远不会覆盖前任Leader已提交的日志。
## Term的作用
- 旧Leader故障恢复后，继续向其他节点广播消息，此时其他节点会响应新Term和新Leader ID，旧Leader收到响应后会转为Follower。
- 每个节点投票时都会记录它在该 term 中是否已经投过票，以防止在同一Term内给多个Candidate投票。
- 任何时候，只要一个节点接收到包含更高 Term 的消息（不管是来自 AppendEntries、RequestVote、InstallSnapshot 等 RPC），它必须立刻：
	1. 更新自己的 currentTerm 为该更高的 Term
	2. 重置为 Follower 状态（即使它当前是 Leader 或 Candidate）
	3. 清除已投票信息（voteFor = null）
	4. 如果是AppendEntries消息，则节点会重置自己的Leader为消息发送方
	5. 如果是RequestVote，且消息发送方的日志不比自己的旧，则为其投票



# 日志复制

## §5.4.2 的限制二

**Raft 的限制是：**
只能提交当前任期的 entry，并且需要多数派复制成功。防止旧 Leader 提交未被新 Leader 接受的日志，避免破坏一致性。

也就是：
- 旧任期写的 entry（即使被多数派复制），也不能被当前 Leader 提交，除非有后续的新 entry 跟着提交。
- Leader 只能在自己 term 内写的新 entry 达到多数派时，才能顺带提交前面的（旧 term）日志。
## 日志一致性检查
Follower每次接收新日志（AppendEntries RPC 请求）时都会检查自己前一条日志和Leader的是否一致（通过PrevLogIndex、PrevLogTerm ），若不一致则拒绝该请求，同时启动日志修复机制。
1. Leader 收到 Follower 的拒绝响应。
2. Leader 将该 Follower 的 “下一次要发送的日志索引”（nextIndex）回退，即 nextIndex--，然后再次发起 AppendEntries RPC请求。
4. 如果仍不匹配，Leader继续回退 nextIndex--，直到找到共同前缀。
5. Follower清空自己和Leader共同前缀之后的所有日志，再追加本次Leader发送的新日志。
```go
# nextIndex[follower]: Leader认为该Follower的日志应该从哪个索引开始追加
PrevLogIndex = nextIndex[follower] - 1
PrevLogTerm  = term of the log at PrevLogIndex
```
**最终目的**：让 Follower 的日志被 Leader 覆盖为一致状态。Leader永远不会回退自己的日志。

# 客户端交互
- 必须由Leader来处理客户端请求，如果客户端不知道Leader是谁，它会首先和任意一台服务器通信，这台服务器会告诉客户端谁是Leader。
- Leader将命令写入本地、复制到Follower、确定提交、然后在本地状态机执行完毕后，才会对客户端返回响应。
- 如果Leader收到请求后宕机，则会导致请求超时，这时客户端会重新发出请求到其他的服务器上，然后就会被重定向到新的Leader，由新的Leader再次处理该请求，直到命令被执行。
- 可能存在一种情况是Leader已经执行了请求，但在返回响应过程中响应丢失或Leader挂掉了。此时客户端会重新发送请求，解决这个问题的办法是给每一个请求加一个唯一ID，这个ID也会存在日志里，状态机在接受请求时会通过这个ID检查请求是否已经执行过了。（新Leader一定包含所有已提交日志，但这个请求可能已执行也可能还未执行）。
> **举个例子：**
>1. Leader 收到客户端请求，写日志条目 A  
>2. Leader 将日志条目 A 复制到多数派节点（包括 Follower）
>3. 一旦多数派确认写入，Leader 认为 A 已“**提交**”，并告诉 Follower 当前 commitIndex 到了 A
>4. 各 Follower 收到这个 commitIndex 更新，**但它们可能稍后才会真正“apply”到状态机**

## 只读操作
如何满足客户端的读请求且符合线性一致性（读操作必须返回最近一次提交的写操作数据）

一种简单的方法是将读看做另一种写，即Leader收到读请求后也写入一条日志并复制到其他Follower，但缺点是会对集群造成额外负担。
为此，Raft对Leader引入2条额外措施：
1. 为防止新Leader不知道日志提交的位置（新Leader一定包含已提交日志，但他可能不知道已经提交到哪了），在每个新Leader任期开始时会提交一个no-op空操作日志，一旦no-op日志已提交，则说明该日志之前的所有日志一定也已提交了。
2. 在处理只读请求之前，Leader会向所有Follower发送心跳以此确定自己还是Leader。

这2条措施确保Leader确信自己是Leader并且自己的日志提交信息是最新的（数据是最新的）。

# 集群成员变化
本质问题就是研究如何在不中断集群服务的前提下，避免在增删节点期间同时出现两个及以上 Leader。

# 日志压缩

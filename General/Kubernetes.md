# k8s集群架构
- 最基本的，K8s集群由控制面（Control Plane）和工作节点（Worker Node）组成，控制面管理着工作节点以及工作节点上运行的Pod，每个k8s集群至少需要一个工作节点来运行Pod。在生产环境中，控制面和工作节点一般都是高可用部署的。
## 控制面组件
理论上控制面组件也可以运行在工作节点上，不过更常见的是将控制面组件单独部署，专门部署控制面组件的节点也被称为控制节点（Master Node）
### kube-apiserver
- 负责接收所有API请求，用户kubectl以及其他控制面组件发出的请求都必须经过kube-apiserver
- 所有资源管理操作（创建、修改、查询、删除）都需要通过它进行，然后存储到etcd，以保证集群状态的一致性
- 负责验证请求的身份及权限，以及其他安全准入策略
- 被设计为无状态应用，可以水平扩容
### etcd
- 一个分布式键值数据库，在k8s中用来存储集群所有配置信息和状态数据
- 具备强一致性，即任何时候读到的数据都是最新的且一致的。因此牺牲了一定程度的可用性，即写入数据可能会有延迟。适用于k8s这种对数据准确性要求极高的系统。
### kube-scheduler
- 负责将新创建的Pod分配到合适的工作节点
- 调度决策的因素主要包括：资源需求、亲和性、节点状态以及其他自定义策略
- 需要注意的是，kube-scheduler只负责新Pod的调度，对于已分配节点的Pod，正常情况下k8s不会主动进行二次调度（因为调度Pod可能影响业务），除非节点发生故障，此时节点上的Pod可能会被驱逐重建（前提是它受 Deployment 或 ReplicaSet 控制），重建流程是 kube-controller-manager 先重建 Pod，然后由kube-scheduler 负责分配新 Node，最后kubelet 负责拉起 Pod

| 触发情况               | 组件                 | 处理方式                                           | 需要 kube-scheduler 重新调度？ |
| ------------------ | ------------------ | ---------------------------------------------- | ----------------------- |
| 节点宕机               | node-controller    | 驱逐 Pod → Deployment/ReplicaSet 创建新 Pod         | ✅ 需要调度                  |
| 资源不足               | kubelet            | 驱逐 Pod → Deployment/ReplicaSet 重建 Pod          | ✅ 需要调度                  |
| 手动删除 Pod           | kubectl delete pod | 直接删除 → Deployment/ReplicaSet 重建 Pod            | ✅ 需要调度（但可能原节点）          |
| DaemonSet Pod 驱逐   | kubelet            | 不会重新创建（DaemonSet 仅在特定 Node 上运行，除非节点恢复）         | ❌ 不需要                   |
| StatefulSet Pod 驱逐 | kubelet            | 自动重建 Pod（需等待 PersistentVolume 释放，可能需要手动干预清理残留） | ✅ 需要调度                  |
### kube-controller-manager
- 由多个控制器组成，但以单一进程形态运行（每个控制器都是其中一个协程）
- 每个控制器负责监控不同类型的资源，当资源状态发生变化时自动执行相应调整操作，确保k8s集群最终达到期望状态，控制器工作模式主要为：监听事件、计算差异、触发操作

kube-controller-manager通过WATCH机制（HTTP Long Polling）监听kube-apiserver
（1）kube-controller-manager 先通过 kube-apiserver 获取集群中所有的 Pod，并开启WATCH监听
（2）当Pod被删除时，kube-apiserver 更新 etcd，并通知所有 WATCH 该资源的组件
（3）kube-controller-manager 监听到 Pod 资源删除事件，执行相应的控制逻辑

> Long Polling 是应用层协议的策略，它通过延迟响应的方式实现“伪推送”（即客户端发起请求后，服务端会先将请求hold住，直到服务端有数据返回时才响应该请求），但每次数据返回后，客户端都要重新发起请求。

以下是常见的控制器类型

| 组件 | 监听资源 | 触发操作 |
|------|---------|----------|
| ReplicaSet Controller | Pod | 发现 Pod 不足时，创建新 Pod |
| Node Controller | Node | 发现 Node 失联，驱逐 Pod 并触发重新调度 |
| Job Controller | Job | 监测任务完成情况，失败时重试 |
| Endpoint Controller | Pod | 发现 Pod 被删除时，更新 Service 关联的 Endpoint |
## 工作节点组件



# k8s集群架构
- 最基本的，K8s集群由控制面（Control Plane）和工作节点（Worker Node）组成，控制面管理着工作节点以及工作节点上运行的Pod，每个k8s集群至少需要一个工作节点来运行Pod。在生产环境中，控制面和工作节点一般都是高可用部署的。
## 控制面组件
- 理论上控制面组件也可以运行在工作节点上，不过更常见的是将控制面组件单独部署，专门部署控制面组件的节点也被称为控制节点（Master Node）
- 控制面组件可以直接部署在节点上（物理机/虚拟机），以systemd形态运行；也可以作为Pod部署（Static Pod），由节点上的kubelet管理。在实际生产环境中更常见的部署方式是后者，前者较难实现高可用部署，需手动管理，缺乏自恢复能力
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
### kubelet
- 运行在k8s集群所有节点上（包括Master Node，因为控制面组件也可以以容器形态运行的），以守护进程的方式存在
- 负责接收调度指令创建和管理Pod，通过容器运行时来管理Pod里的容器以及监控容器状态

**Pod 创建流程**
1. kubelet 监听 kube-apiserver，发现有新的 Pod 调度到当前节点。
2. kubelet 解析 PodSpec，并通过 CRI（gRPC API）请求容器运行时（如 containerd）。
3. CRI 创建 Pod Sandbox，分配 IP，为 Pod 内容器创建共享网络环境。
4. CRI 创建容器，拉取镜像、挂载存储、执行容器进程。
5. kubelet 监控 Pod 和容器状态，并定期向 kube-apiserver 上报。

> #### 关于Pod、Pod Sandbox、容器的关系
> - Pod是 Kubernetes 的逻辑单元，包含一个 Pod Sandbox 和多个容器。
> - Pod Sandbox 是容器运行时创建的基础设施，用于为 Pod 中的 容器 提供共享环境。
> - 容器 是运行应用进程的实体。

> #### 关于Pod Sandbox
>- **Pod Sandbox 本质上是一个“占位符”**，其核心作用是**为 Pod 中的容器提供一个共享的、稳定的底层环境**，即使 Pod 内的所有应用容器终止，它依然会保持运行，直到整个 Pod 被删除
>- 在 Kubernetes 中，Pod Sandbox 通常通过一个极简的容器（称为 **"pause" 容器**）实现，其镜像大小只有几M，不含任何业务逻辑，几乎不会主动退出，唯一任务就是占住资源（如分配给Pod的IP）并维持命名空间
> - Kubernetes通过监控 Pod Sandbox 的状态来判断Pod是否存活。删除 Pod 时，Kubernetes 会先终止 Pod Sandbox，再清理所有关联的容器。

### 容器运行时
- 负责管理k8s集群中容器的运行和生命周期，直接与操作系统内核交互，提供容器运行所需的隔离环境
- k8s通过CRI（容器运行时接口）来支持不同的运行时实现，如 containerd、CRI-O

>#### 关于containerd和CRI-O
>- containerd由Docker中拆分出来，除k8s外还支持Docker Swam等其他容器编排平台
>- CRI-O专为CRI设计，只支持k8s，但是更轻量和高效

### kube-proxy
- kube-proxy 是 k8s 网络代理组件，运行在每个 Node 上，负责维护网络规则，使集群内的 Pod 之间能够通过 Service 进行通信
- 一般情况下kube-proxy是必须的，不过也有使用其他网络插件的替代方案

## 客户端工具
### kubectl
安装方式可参考：https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/

安装 kubectl 后，它默认会寻找 ~/.kube/config 并使用该配置连接 Kubernetes 集群
```shell
# 验证
kubectl cluster-info

# 基本使用格式，-A所有命名空间
kubectl <动作：get|create|delete> <资源类型：pod|deployment|node|service> <资源名> -A

# 启动一个代理服务，允许在本地访问 kube-apiserver，自动使用本机kubectl认证信息，适用于本地调试kube-apiserver
kubectl proxy
```

# 基本概念
## Pod
- k8s调度的基本单位，是一组紧密耦合的容器（一般是一个业务应用容器+监控、日志采集容器），Pod中的容器共享IP地址、存储卷、主机名等，这意味着相同Pod内的容器可以直接使用localhost:<端口>彼此访问
- 注意Pod中不同容器的文件系统还是互相隔离的，只不过可以挂载共享存储
![](attachments/Pasted%20image%2020250310234550.png)
常用命令
```shell
kubectl get pod <pod_name>
kubectl describe pod <pod_name>
kubectl logs [-f] <pod_name>
# 在容器上执行命令，这里是启动一个bash会话
kubectl exec -it <pod_name> -- bash
```

# K8s集群架构

- 最基本的，K8s集群由控制面（Control Plane）和工作节点（Worker Node）组成，控制面管理着工作节点以及工作节点上运行的Pod，每个k8s集群至少需要一个工作节点来运行Pod。在生产环境中，控制面和工作节点一般都是高可用部署的。

## 整体架构

![控制平面（kube-apiserver、etcd、kube-controller-manager、kube-scheduler）和多个节点。每个节点运行 kubelet 和 kube-proxy。](./Kubernetes.assets/kubernetes-cluster-architecture.svg)

| 组件       | 与谁通信   | 通信方式                                    | 谁主动发起？    |
| ---------- | ---------- | ------------------------------------------- | --------------- |
| API Server | etcd       | gRPC（读写）                                | API Server 主动 |
| Controller | API Server | HTTP Watch + List                           | Controller 主动 |
| Scheduler  | API Server | HTTP Watch（未调度 Pod）                    | Scheduler 主动  |
| Kubelet    | API Server | HTTP Watch（本节点 Pod/Node）+ 定期上报状态 | Kubelet 主动    |
| etcd       | —          | 被动响应                                    | 从不主动发起    |

- API Server 只会主动向 etcd 发起请求（读写集群状态）
- 所有 Watch 都是客户端（Controller/Scheduler/Kubelet）主动建立的长连接，API Server 只是在这个连接上“写入事件流”，并非主动发起新连接
- API Server 是唯一被允许直接读写 etcd 的组件（保证数据一致性），其他组件都是通过API Server来获取集群状态的
- 所有组件通过 API Server 异步协作
- Scheduler/Controller/Kubelet等组件不会同时 watch 多个 API Server，它通过单一 endpoint（通常是负载均衡器） 连接到 API Server 集群
  - 控制面组件和 kubelet 通常使用**内网 LB/VIP**；
  - kubectl 等外部工具可能通过**公网 LB**（需严格防火墙控制）


> **上层组件（如 scheduler、controller-manager）通过 API Server 的 watch 接口监听资源变化，而 API Server 内部会向 etcd 发起对应的 watch 请求，从而将 etcd 的变更事件“代理”给客户端。**

## 控制面组件

- 理论上控制面组件也可以运行在工作节点上，不过更常见的是将控制面组件单独部署，专门部署控制面组件的节点也被称为控制节点（Master Node）
- 控制面组件可以直接部署在节点上（物理机/虚拟机），以systemd形态运行；也可以作为Pod部署（Static Pod），由节点上的kubelet管理。在实际生产环境中更常见的部署方式是后者，前者较难实现高可用部署，需手动管理，缺乏自恢复能力
### kube-apiserver
- 负责接收所有API请求，用户kubectl以及其他控制面组件发出的请求都必须经过kube-apiserver
- 所有资源管理操作（创建、修改、查询、删除）都需要通过它进行，然后存储到etcd，以保证集群状态的一致性
- 负责验证请求的身份及权限，以及其他安全准入策略
- 被设计为无状态应用，可以水平扩容
### kube-controller-manager
- 负责维护集群的状态，使集群达到期望状态（不断对比“期望状态 vs 实际状态”）
- 由多个控制器组成，但以单一进程形态运行（每个控制器都是其中一个协程）
- 每个控制器负责监控不同类型的资源（Deployment / ReplicaSet / StatefulSet等），当资源状态发生变化时自动执行相应调整操作，确保k8s集群最终达到期望状态，控制器工作模式主要为：监听事件 -> 计算差异 -> 触发操作

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

### kube-scheduler

- 负责将新创建的Pod按预定的策略调度到合适的工作节点（只负责选址）
- 调度决策的因素主要包括：资源需求、亲和性、节点状态以及其他自定义策略
- 需要注意的是，**kube-scheduler只负责新Pod的调度，对于已分配节点的Pod，正常情况下k8s不会主动进行二次调度**（因为调度Pod可能影响业务），除非节点发生故障，此时节点上的Pod可能会被驱逐重建（前提是它受 Deployment 或 ReplicaSet 控制），重建流程是 kube-controller-manager 先重建 Pod，然后由kube-scheduler 负责分配新 Node，最后kubelet 负责拉起 Pod

| 触发情况             | 组件               | 处理方式                                                     | 需要 kube-scheduler 重新调度？ |
| -------------------- | ------------------ | ------------------------------------------------------------ | ------------------------------ |
| 节点宕机             | node-controller    | 驱逐 Pod → Deployment/ReplicaSet 创建新 Pod                  | ✅ 需要调度                     |
| 资源不足             | kubelet            | 驱逐 Pod → Deployment/ReplicaSet 重建 Pod                    | ✅ 需要调度                     |
| 手动删除 Pod         | kubectl delete pod | 直接删除 → Deployment/ReplicaSet 重建 Pod                    | ✅ 需要调度（但可能原节点）     |
| DaemonSet Pod 驱逐   | kubelet            | 不会重新创建（DaemonSet 仅在特定 Node 上运行，除非节点恢复） | ❌ 不需要                       |
| StatefulSet Pod 驱逐 | kubelet            | 自动重建 Pod（需等待 PersistentVolume 释放，可能需要手动干预清理残留） | ✅ 需要调度                     |

### etcd

- 一个分布式键值数据库，在k8s中用来存储集群所有配置信息和资源的状态数据
- 具备强一致性，即任何时候读到的数据都是最新的且一致的。因此牺牲了一定程度的可用性，即写入数据可能会有延迟。适用于k8s这种对数据准确性要求极高的系统。

### 工作流程举例

以部署一个 Nginx的 ReplicaSet 为例

```
kubectl 
   ↓ (1. POST)
API Server → etcd（持久化 ReplicaSet）
   ↓ (2. Watch)
Controller Manager（ReplicaSet Controller）
   ↓ (3. 创建 Pod)(POST)
API Server → etcd（持久化 Pod）
   ↓ (4. Watch)
Scheduler（发现未调度 Pod）
   ↓ (5. 绑定 Node)(PATCH)
API Server → etcd（更新 Pod 的 nodeName）
   ↓ (6. Watch)
Kubelet（在目标节点上启动容器）
   ↓ (7. 上报状态)(PATCH)
Kubelet → API Server（更新 Pod 状态）
```





## 工作节点组件

### kubelet
- 运行在k8s集群所有节点上（包括Master Node，因为控制面组件也可以以容器形态运行的），以守护进程的方式存在
- 负责接收调度指令创建和管理Pod，维护Pod的生命周期，通过容器运行时来管理Pod里的容器以及监控容器状态

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

- 负责Service 到 Pod 的流量转发
- kube-proxy 是 k8s 网络代理组件，运行在每个 Node 上，负责维护网络规则，使集群内的 Pod 之间能够通过 Service 进行通信
- 一般情况下kube-proxy是必须的，不过也有使用其他网络插件的替代方案

### CNI

- 负责Pod之间的网络通信
- 给Pod分配IP，维护Pod和Pod之间的路由，建立跨节点通信
- 是k8s必需的组件

# 基本概念

## Pod

- k8s调度的基本单位，是一组紧密耦合的容器（一般是一个业务应用容器+监控/日志采集容器），**Pod中的容器共享IP地址、存储卷、主机名等**，这意味着相同Pod内的容器可以直接使用`localhost:<端口>`彼此访问
- 共享资源的容器组，可以看成一个逻辑主机
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
## Namespace

- 一种逻辑隔离机制，将同一物理集群划分为相互隔离的组
- 允许不同项目、不同环境共用一个物理集群且互不干扰
- 同一命名空间中的资源名称（仅针对作用域是命名空间级的资源）需唯一，不同命名空间的资源则无此要求

# 网络模型

## 不使用Service

### 直接使用 Pod IP

**Pod 有自己的 Pod IP，可以直接访问该 IP + 容器端口**

- Pod IP **不是固定**的（重建就变了）
- 不同节点之间的路由要靠 CNI，否则不通
- 从集群外部不能直接访问

### port-forward

- 通过 kubectl，把**本地端口**（执行kubectl的客户端主机）映射到 Pod 内部端口。

- 仅仅是 *本地转发*，不能给其他客户端用，一般只用于本地调试

### **HostNetwork模式**

- **Pod 直接使用宿主机网络**，没有独立的Pod IP
- Pod里监听的端口==宿主机的端口

### HostPort模式

- Pod 的容器端口映射到宿主机的某个端口，Pod 依然有自己独立的 Pod IP（与 hostNetwork 不同）
- 类似于 Docker 的`docker run -p 30080:80`

## 使用Service

每个Pod都有自己的IP，这个IP可能来自CNI（k8s网络插件）创建的虚拟网络中的IP，也可能直接使用Node IP（如果Pod配置了hostNetwork: true）。

Pod之间可以通过Pod IP直接访问，前提是网络策略运行。但问题在于Pod是不稳定的，可能会随着扩缩容被删除或新建，此时Pod IP也有可能随之改变，因此最佳实践是永远不要直接依赖Pod IP去实现服务间通信。

Service的作用是**为一组动态变化的 Pod 提供稳定的访问入口和负载均衡**，使得客户端无需感知后端Pod的IP变化。

Service有四种类型：

| 类型         | 作用                                                         | 适用场景                 |
| ------------ | ------------------------------------------------------------ | ------------------------ |
| ClusterIP    | Service默认类型，仅在集群内部提供访问                        | 内部通信                 |
| NodePort     | 通过每个 Node 的 IP 和固定端口暴露 Service，适用于集群外访问 | 简单外部访问             |
| LoadBalancer | 依赖云服务商（AWS、GCP、Azure）的负载均衡器暴露 Service，适用于集群外访问 | 生产环境+云负载均衡      |
| ExternalName | 将 Service 映射到外部域名，如 mydb.example.com               | Pod访问集群外的服务或API |

> 关于ClusterIP 

- 是 ​Service 资源分配的虚拟 IP（VIP），仅在集群内部可达
- 特性：
  -  稳定性：Service 创建后，ClusterIP 在生命周期内固定不变（除非删除重建）
  -  负载均衡：流量通过 ClusterIP 访问时，会被自动分发到后端多个 Pod

> 关于ExternalName

主要用于 K8s 集群内部的 Pod 访问集群外部的服务，Pod访问 ExternalName 类型的 Service 时，K8s 直接返回外部服务的域名，本质上ExternalName就是一个DNS别名（CNAME解析）。典型应用场景包括：

- 访问云厂商提供的数据库或 API（如 AWS RDS）
- 集群内部服务需要访问企业内部 DNS 解析的服务

**为什么使用ExternalName访问外部服务，而不是直接使用外部服务的域名？**

- 防止因外部服务域名发生变化而导致必须修改代码
- 使Pod可以以同样的 Service 方式访问 K8s 内外部服务，统一架构
- 便于未来可能的服务迁移，如外部服务迁移到K8s内部，此时只需要把Service类型从ExternalName改为ClusterIP即可
- 可以使用**Istio、Envoy**等流量管理功能，为外部服务添加一层额外防护

### NodePort VS HostPort

看上去都可以通过`NodeIP:Port`的方式访问Pod

但最明显的区别：

- HostPort不会允许在一个Node中有多个相同的Pod，因为会报端口冲突
- NodePort允许在一个Node中有多个相同的Pod，且可以由kube-proxy实现负载均衡

# K8s部署





# 客户端工具

## kubectl

安装方式可参考： https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/

安装 kubectl 后，它默认会寻找 ~/.kube/config 并使用该配置连接 Kubernetes 集群

```shell
 # 验证
kubectl cluster-info

# 基本使用格式，-A所有命名空间，-o wide输出更多详细信息，-o json以JSON格式输出信息，-n指定命名空间（只要不是default都需要显示指定）
kubectl <动作：get|create|delete|patch> <资源类型：pod|deployment|node|service> <资源名> <flags: -A|-o wide|-o json|-n [namespace]>

# 启动一个代理服务，允许在本地访问 kube-apiserver，自动使用本机kubectl认证信息，适用于本地调试kube-apiserver
kubectl proxy
```

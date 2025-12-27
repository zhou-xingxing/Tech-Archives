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
- 共享资源的容器组，可以看成一个**逻辑主机**
- 注意Pod中不同容器的文件系统还是互相隔离的，只不过可以挂载共享存储

### Pod中容器的资源隔离程度

> Pod 中的容器并不是每个都有“完整独立”的 Linux namespace；有些Linux namespace是Pod级共享的，有些是容器级独立的

| Namespace 类型 | 是否共享（默认）     | 说明                                                       |
| -------------- | -------------------- | ---------------------------------------------------------- |
| Network        | ✅ 共享               | 所有容器共用一个网络栈（IP、端口等）                       |
| UTS            | ✅ 共享               | 主机名一致                                                 |
| IPC            | ✅ 共享               | 可通过 IPC 机制通信                                        |
| PID            | ❌ 不共享（可选共享） | 默认各自有独立进程视图                                     |
| Mount          | ❌ 不共享             | 每个容器有自己的文件系统挂载点（但可通过 volume 共享目录） |
| User           | ❌ 通常不共享         | 各自的用户/组 ID 映射                                      |

**Pod 是“网络/主机视角一致，进程/文件隔离”的折中模型**

cgroups也是容器级的，所以Pod中的容器可以各自单独设置CPU和内存的使用配额。

每个Pod里都有一个pause根容器，它负责承载 Pod 级别的 Linux Namespace（尤其是网络），让 Pod 内的所有业务容器能够共享同一个运行环境。

![](attachments/Pasted%20image%2020250310234550.png)
常用命令

```shell
kubectl get pod <pod_name>
kubectl describe pod <pod_name>
kubectl logs [-f] <pod_name>
# 在容器上执行命令，这里是启动一个bash会话
kubectl exec -it <pod_name> -- bash
```
### Pod生命周期

> **Kubernetes 把 Pod 当成“资源共享单元”，但把容器当成“失败与重启的最小单元”。**

#### Pod创建

以部署一个Nginx的 ReplicaSet 为例

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

#### Pod启动

在同一个 Pod 里，一个容器启动失败只会重启这个容器本身，不会影响到Pod内其他容器，容器启动失败不等于Pod需要被重建。

Init container 失败是个例外，它失败会阻塞整个Pod，其他容器均不会启动。

#### Pod终止

todo

#### 容器探针

- livenessProbe

用于探测容器是否处于存活（正常运行）状态，如果探测失败，kubelet会杀死容器，并根据该容器重启策略执行下一步动作。

> 如果容器中的进程能够在遇到问题或不健康的情况下自行崩溃，则不一定需要存活探针。
>
> Kubernetes（准确来说应该是容器运行时） 会持续监控 Pod 中每个容器的**主进程（PID 1）是否还在运行**：
>
> - 如果容器主进程非正常退出(exit code ≠ 0)→ Kubernetes 认为容器“失败”，根据重启策略决定下一步动作。
> - 但如果容器主进程没有退出，但实质已无法正常工作了（卡住、资源耗尽），此时就需要使用存活探针。

- readinessProbe

用于探测容器是否已准备好接受请求，如果探测失败，则不会将该Pod加入Service，或将该Pod从已加入的Service中移除。

只有当一个 Pod 中**所有容器的就绪探针都成功**，该 Pod 才会被标记为“就绪”（Ready），即有一个容器就绪探针失败，该Pod也不会加入Service。

- startupProbe

指示容器中的应用是否已经启动。如果提供了启动探针，则所有其他探针都会被 禁用，直到此探针成功为止。如果启动探测失败，kubelet将杀死容器， 而容器依其重启策略进行重启。

### Pod调度

默认情况下，Scheduler会为Pod计算出最合适节点。

#### nodeName

将Pod调度到指定名字的Node上。

#### nodeSelector

将Pod调度到具有指定标签的Node上。

#### 亲和性调度

亲和性功能由两种类型的亲和性组成：

1. 节点亲和性`nodeAffinity`功能类似于 `nodeSelector` ，但它的表达能力更强，并且允许你指定软规则。

**requiredDuringSchedulingIgnoredDuringExecution**

必须满足的调度条件，且如果条件在Pod已经调度后不满足了，Pod仍将继续运行。

**preferredDuringSchedulingIgnoredDuringExecution**

尽量满足的调度条件，如果找不到合适的节点，Scheduler仍会调度该Pod。如果条件在Pod已经调度后不满足了，Pod仍将继续运行。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-node-affinity
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: topology.kubernetes.io/zone
            operator: In
            values:
            - antarctica-east1
            - antarctica-west1
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: another-node-label-key
            operator: In
            values:
            - another-node-label-value
  containers:
  - name: with-node-affinity
    image: registry.k8s.io/pause:2.0
```

>如果你在与 nodeAffinity 类型关联的 nodeSelectorTerms 中指定多个条件， 只要其中一个 `nodeSelectorTerms` 满足（各个条件按逻辑或操作组合）的话， Pod 就可以被调度到节点上。

> 如果你在与 `nodeSelectorTerms` 中的条件相关联的单个 `matchExpressions` 字段中指定多个表达式， 则只有当所有表达式都满足（各表达式按逻辑与操作组合）时，Pod 才能被调度到节点上。

2. Pod 亲和性`podAffinity`和反亲和性`podAntiAffinity`允许你根据其他 Pod 的标签来约束 Pod，其语义为：如果 X 上已经运行了一个或多个满足规则 Y 的 Pod， 则这个 Pod 应该（或者在反亲和性的情况下不应该）运行在 X 上。 这里的 X 可以是节点、机架、云提供商可用区或地理区域或类似的拓扑域， Y 则是 Kubernetes 尝试满足的规则。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-pod-affinity
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: security
            operator: In
            values:
            - S1
        topologyKey: topology.kubernetes.io/zone
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: security
              operator: In
              values:
              - S2
          topologyKey: topology.kubernetes.io/zone
  containers:
  - name: with-pod-affinity
    image: registry.k8s.io/pause:2.0
```

topologyKey的常见值有：**（topologyKey支持自定义）**

- kubernetes.io/hostname 节点级
- topology.kubernetes.io/zone 可用区级
- topology.kubernetes.io/region region级

#### 污点与容忍度

污点Taint作用于节点，容忍度Toleration作用于Pod。污点和容忍度相互配合，可以避免 Pod 被分配到不合适的节点上。

**污点**

```shell
# 给node1打污点
kubectl taint nodes node1 key1=value1:NoSchedule
# 给node1去除污点
kubectl taint nodes node1 key1=value1:NoSchedule-
```

PreferNoSchedule: 尽量不调度。

NoSchedule: 明确不调度。

NoExecute: 明确不调度且驱逐现在节点上已有的不具备容忍度的Pod。

控制平面会根据节点状况自动添加污点（如 `not-ready`、`unreachable`）

**容忍度**

以下例子说明：该Pod可以被调度到打了`dedicated=gpu:NoExecute`污点的Node上

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  containers:
    - name: cuda-app
      image: nvidia/cuda:12.0-base
      command: ["sleep", "3600"]
  tolerations:
    - key: "dedicated"
      operator: "Equal" ## 可以是Equal或者Exists
      value: "gpu"
      effect: "NoExecute"
      tolerationSeconds: 300  ## 仅 NoExecute 生效，5分钟后再被驱逐
```

特殊情况：

- 如果 `key` 为空且为 `Exists`，则匹配所有污点

- 如果 `effect` 为空，则匹配指定 `key` 的所有效果
- 如果Pod设置了`tolerationSeconds`，则允许Pod运行一段时间后再驱逐，如果没设置`tolerationSeconds`则Pod可以一直在该节点上运行

#### 如何实现Pod独占节点

1. 给节点加`Taint`：确保其他Pod不会调度到该节点上。
2. 给Pod加`Toleartion`：使Pod能被允许被调度到该节点上。
3. 给Pod加`nodeSelector`或`nodeAffinity`：使Pod定向调度到该节点上。

## Namespace

- 一种逻辑隔离机制，将一个物理集群划分为资源名称、权限、配额相互隔离的组
- 允许不同项目、不同环境共用一个物理集群且互不干扰
- 同一命名空间中的资源名称（仅针对作用域是命名空间级的资源）需唯一，不同命名空间的资源则无此要求
- 命名空间可设定资源配额，实现不同租户的资源用量管控

k8s集群在启动后，会默认创建4个命名空间

```
dafault: 用户未指定命名空间时，资源默认创建在此。
kube-system: k8s的系统组件所在的命名空间。
kube-public: 全局可读的命名空间，通常包含集群信息ConfigMap（如cluster-info），用于引导节点加入集群。
kube-node-lease: 每个Node对应一个Lease对象，kubelet每秒更新一次Lease，控制平面通过Lease判断节点是否失联。
```

- 注意！k8s namespace**默认不隔离网络**，根据k8s的网络模型，Pod跨Namespace天然可通信，网络隔离靠**NetworkPolicy + 支持的 CNI**

## Label

允许用户给k8s资源对象添加自定义标识（以键值对形式），可以在创建对象时添加，后续也可随时修改或删除。

k8s支持2种标签选择算符：基于等值的和基于集合的

### 基于等值的

```
environment = production
tier != frontend
```

- 第一个筛选带有environment标签且值为production的资源
- 第二个筛选带有tier标签且值不为frontend的，**以及不带有trie标签**的资源

### 基于集合的

```
environment in (production, qa)
tier notin (frontend, backend)
partition
!partition
```

- 第一个筛选带有environment标签且值为production或qa的资源
- 第二个筛选带有tier标签且值不为frontend或backend的，**以及不带有trie标签**的资源
- 第三个筛选带有partition标签的资源，值任意
- 第四个筛选不带有partition标签的资源

如果明确希望筛选带有tier标签且值不为frontend或backend的，需使用

```
tier!=frontend,tier
```

## 工作负载

 

 



# 网络模型

Kubernetes 对网络有以下强制性要求（无论使用 Flannel、Calico、Cilium 等 CNI 插件）：

“All containers can communicate with all other containers without NAT.”

“All nodes can communicate with all containers (and vice versa) without NAT.”

这意味着：

任意 Pod ↔ Pod（无论是否同节点）可以直接通信；
任意 Node ↔ Pod（包括 Master 和 Worker）可以直接通信；
所有通信都使用 真实 IP（无 NAT）。

## 不使用Service

### 直接使用 Pod IP（默认）

**Pod 有自己的 Pod IP，可以直接访问该Pod IP + 容器端口（containerPort）**

- Pod IP **不是固定**的（重建就变了）
- 不同节点之间的路由要靠 CNI，否则不通
- 从集群外部不能直接访问，`Pod->Pod`或`Node->Pod`是可以的
- 有些生产环境启用了额外的网络安全策略，可能不允许从Node访问Pod

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





# K8s使用

## kubectl

安装方式可参考： https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/

安装 kubectl 后，它默认会寻找 ~/.kube/config 并使用该配置连接 Kubernetes 集群

```shell
 # 验证
kubectl cluster-info

# 基本使用格式，-A所有命名空间，-o wide输出更多详细信息，-o json以JSON格式输出信息，-n指定命名空间（只要不是default都需要显示指定），-w持续监听模式
kubectl <动作：get|create|delete|patch|describe> <资源类型：pod|deployment|node|service> <资源名> <flags: -A|-o wide|-o json|-n [namespace]|-w>

# 启动一个代理服务，允许在本地访问 kube-apiserver，自动使用本机kubectl认证信息，适用于本地调试kube-apiserver
kubectl proxy

# 进入pod里的容器，如果只有一个容器可省略-c
kubectl exec busybox-pod -c busybox -it -- sh
```

## metadata VS spec

> **metadata 是“控制面用来管理对象的字段”，spec 是“数据面用来运行对象的字段”**

```
metadata: 你是谁，对象的“身份信息”
spec: 你要怎么工作，对象的“期望状态 / 行为”
```

所以，Pod 的标签（labels）属于 Pod 的 metadata，而Deployment 的标签选择器（selector）属于 Deployment 的 spec。

## Pod YAML

### 容器启动命令

> [!IMPORTANT]
>
> 如果Pod YAML里只设置了command，那么Dockerfile里的ENTRYPOINT和CMD都会被覆盖（本人实际测试的结论）

| Dockerfile                        | k8s Pod YAML                              | 最终执行命令                  |
| --------------------------------- | ----------------------------------------- | ----------------------- |
| `ENTRYPOINT ["ep"]` `CMD ["cmd"]` | 未设置 `command`/`args`                      | `["ep", "cmd"]`         |
| `ENTRYPOINT ["ep"]` `CMD ["cmd"]` | 只设 `command: ["k8s-cmd"]`                 | `["k8s-cmd"]`           |
| `ENTRYPOINT ["ep"]` `CMD ["cmd"]` | 只设 `args: ["k8s-arg"]`                    | `["ep", "k8s-arg"]`     |
| `ENTRYPOINT ["ep"]` `CMD ["cmd"]` | `command: ["k8s-ep"]` `args: ["k8s-arg"]` | `["k8s-ep", "k8s-arg"]` |

### 容器使用资源限制

limits: 限制容器能使用的最大资源

requests: 容器启动所需要的最小资源，否则无法调度

| 场景                               | 行为                                                       |
| ---------------------------------- | ---------------------------------------------------------- |
| **只设 `requests`，不设 `limits`** | `limits` 默认 = 节点可用资源上限（危险！可能耗尽节点资源） |
| **只设 `limits`，不设 `requests`** | `requests` 自动 = `limits`（保守策略）                     |
| **都不设**                         | 容器可无限制使用节点资源（**强烈不推荐**）                 |
| **内存超限**（Gi、Mi、G、M）       | 容器被 OOMKilled（Exit Code 137）                          |
| **CPU 超限**（整数小数均可）       | 容器被限流（throttled），但不会被杀                        |







## Helm


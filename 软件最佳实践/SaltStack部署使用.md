# 安装部署
## 1. 根据需要安装对应组件
- 参考： https://docs.saltproject.io/salt/install-guide/en/latest/topics/install-by-operating-system/linux-deb.html
- 安装前检查：Master节点已开放4505和4506两个端口

|Port|Type|Description|
|---|---|---|
|4505|Event Publisher/Subscriber port (publish jobs/events)|Constant inquiring connection|
|4506|Data payloads and minion returns (file services/return data)|Connects only to deliver data|
- 以Ubuntu系统为例
```shell
# Ensure keyrings dir exists
mkdir -p /etc/apt/keyrings
# Download public key
curl -fsSL https://packages.broadcom.com/artifactory/api/security/keypair/SaltProjectKey/public | sudo tee /etc/apt/keyrings/salt-archive-keyring.pgp
# Create apt repo target configuration
curl -fsSL https://github.com/saltstack/salt-install-guide/releases/latest/download/salt.sources | sudo tee /etc/apt/sources.list.d/salt.sources
sudo apt update
# master node
sudo apt-get install salt-master
# minion node
sudo apt-get install salt-minion
```
- saltstack各核心组件

| **组件**         | **作用**    | **功能描述**                          |
| -------------- | --------- | --------------------------------- |
| Salt Master    | 主控端       | 负责管理所有 Minion，发布命令，接收执行结果，存储配置等   |
| Salt Minion    | 受控端       | 运行在被管理的服务器上，监听 Master 指令并执行操作     |
| Salt SSH       | 无代理管理     | 允许通过 SSH 远程控制服务器，无需安装 Minion 组件   |
| Salt Syndic    | 多级 Master | 支持分层架构，允许多个 Master 级联，适用于大规模分布式环境 |
| Salt Cloud     | 云实例管理     | 自动创建、配置和管理云服务器（AWS、GCP、Azure 等）   |
| Salt API       | REST 接口   | 通过 HTTP API 远程调用 SaltStack，实现系统集成 |
## 2. 配置
参考： https://docs.saltproject.io/en/latest/ref/configuration/index.html
### master节点
- 默认配置文件位置：`/etc/salt/master`
- 可以通过在`/etc/salt/master.d`目录下创建`.conf` 结尾的文件添加自定义配置
### minion节点
- 默认配置文件位置：`/etc/salt/minion`
- 可以通过在`/etc/salt/minion.d`目录下创建`.conf` 结尾的文件添加自定义配置
#### 配置master节点IP和minion ID
```config
master: 192.0.2.20
id: minion_1
```
## 3. 接受秘钥
在minion节点配置master节点IP和minion ID后，重启salt-minion服务，此时minion节点会向master节点发送自己的秘钥
```shell
# master节点执行
# 查看所有秘钥
salt-key -L
# 接受指定minion节点秘钥
salt-key -a <minion_ID>
# 拒绝指定minion节点秘钥
salt-key -r <minion_ID>
# 删除指定minion节点秘钥
salt-key -d <minion_ID>
# 检测与minion节点连接是否正常，test.version 是 SaltStack 内置的执行模块
salt '*' test.version
```

附：salt常见执行模块

| 模块名 | 作用 |
|--------|------|
| cmd | 远程执行 Shell 命令，如 cmd.run |
| file | 管理文件和目录，如 file.write、file.copy |
| pkg | 软件包管理，如 pkg.install、pkg.remove |
| service | 服务管理，如 service.start、service.restart |
| user | 用户管理，如 user.add、user.delete |
| group | 组管理，如 group.add、group.delete |
| network | 网络管理，如 network.interfaces |
| test | 测试模块，如 test.ping、test.version |
| grains | 获取系统信息，如 grains.items |
| pillar | 获取 Pillar 变量，如 pillar.get |
| sys | 查询 Salt 内部信息，如 sys.list_modules |
| state | 执行 Salt State，如 state.apply |

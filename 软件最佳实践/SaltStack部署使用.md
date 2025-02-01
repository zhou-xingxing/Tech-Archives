# 安装部署
>salt标准部署架构是C-S模式，但也提供了类似Ansible的从节点无client连接方式（通过ssh）
## 1. 根据需要安装对应组件
- 参考： https://docs.saltproject.io/salt/install-guide/en/latest/topics/install-by-operating-system/linux-deb.html
- 安装前检查：Master节点已开放4505和4506两个端口
![](attachments/Pasted%20image%2020250201111340.png)

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

# 使用
## salt常见执行模块

| 模块名     | 作用                                   |
| ------- | ------------------------------------ |
| cmd     | 远程执行 Shell 命令，如 cmd.run              |
| file    | 管理文件和目录，如 file.write、file.copy       |
| pkg     | 软件包管理，如 pkg.install、pkg.remove       |
| service | 服务管理，如 service.start、service.restart |
| user    | 用户管理，如 user.add、user.delete          |
| group   | 组管理，如 group.add、group.delete         |
| network | 网络管理，如 network.interfaces            |
| test    | 测试模块，如 test.ping、test.version        |
| grains  | 获取系统信息，如 grains.items                |
| pillar  | 获取 Pillar 变量，如 pillar.get            |
| sys     | 查询 Salt 内部信息，如 sys.list_modules      |
| state   | 执行 Salt State，如 state.apply          |
## QuickStart Demo
### 远程执行shell命令
```shell
# 对指定minion节点执行shell命令
salt '*' cmd.run 'df -h'
```
### 部署并启动Nginx
#### 前置知识
SaltStack 中 **State** 和 **Pillar** 是两个核心概念，分别用于 **定义自动化任务** 和 **存储配置数据**。它们的关系可以类比 **程序代码** 和 **配置文件**：
- **State**
Salt State（状态）用于 **定义和管理系统配置**，本质上是 **声明式基础设施自动化**。它的作用类似于 **Ansible Playbook** 或 **Terraform 配置文件**
- **Pillar**
Pillar 是 SaltStack 的全局配置管理工具，用于 **存储敏感信息或自定义变量**（类似 Ansible 的 vars 或 group_vars）

#### 目录结构
```txt
/srv/salt/
├── top.sls          # 目标匹配，state.apply命令默认读取该文件
├── init.sls         # 主要 State 文件（安装、配置、启动 Nginx）
└── files/
    ├── nginx.conf.j2  # Nginx 配置文件模板
    └── index.html.j2  # Nginx 首页文件模板

/srv/pillar
|-- top.sls # state.apply命令默认读取该文件
|-- nginx.sls
```
- Salt 默认使用`/srv/salt/`作为 State 文件的根目录，这个路径可以在 Salt Master 配置文件中修改
- Salt默认使用`/srv/pillar/`作为Pillar文件的根目录，这个路径可以在 Salt Master 配置文件中修改
```yaml
# /srv/salt/top.sls
base:
# 所有 Minion 都会应用 init.sls
  '*':
    - init
```

```yaml
# /srv/salt/init.sls

# 安装 Nginx
install-nginx:
  pkg.installed:
    - name: nginx

# 部署 Nginx 配置（使用 Jinja2 模板）
deploy-nginx-config:
  file.managed:
    - name: /etc/nginx/nginx.conf
    - source: salt://files/nginx.conf.j2 # salt://指file_roots目录，默认为/srv/salt/
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - context:
        server_name: "{{ pillar['nginx_server_name'] }}"
    - require: # 确保以下任务先执行
      - pkg: install-nginx

# 部署 Nginx 首页（使用 Jinja2 模板）
deploy-index-html:
  file.managed:
    - name: /var/www/html/index.html
    - source: salt://files/index.html.j2
    - user: www-data
    - group: www-data
    - mode: 644
    - template: jinja
    - context:
        site_name: "{{ pillar['nginx_site_name'] }}"
    - require:
      - pkg: install-nginx

# 启动并启用 Nginx 服务
enable-nginx:
  service.running:
    - name: nginx #会自动解析nginx对应的系统服务，所以不需要指定.service后缀
    - enable: True
    - watch: # 监听指定的文件变化，若变化则重启Nginx服务
      - file: deploy-nginx-config
      - file: deploy-index-html
```

```yaml
# /srv/pillar/top.sls
base:
  '*':
    - nginx # 所有 Minion 都会加载 nginx.sls 里的 Pillar 变量
```

```yaml
# /srv/pillar/nginx.sls
nginx_server_name: "example.com"
nginx_site_name: "Welcome to My Nginx Server!"
```

nginx.conf.j2和index.html.j2文件内容省略

- 执行salt state
```shell
# 测试模式（不实际修改）
salt '*' state.apply test=True
# 执行
salt '*' state.apply
```
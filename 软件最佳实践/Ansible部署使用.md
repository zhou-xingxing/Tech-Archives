# 安装部署
- 以Ubuntu系统为例
```shell
sudo apt update
# software-properties-common是一个管理 PPA（Personal Package Archive，个人软件包存档）的工具包，提供 add-apt-repository 命令
sudo apt install software-properties-common
# 添加 Ansible 官方 PPA 源
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install ansible
# 验证
ansible --version
```
> 附：什么是PPA？
> PPA 是 Ubuntu 提供的一个**第三方软件仓库**，通常由软件开发者、社区或企业维护，允许提供官方仓库未包含的软件，或者提供更**新版本**的软件。
# 使用
## 配置要控制的主机
 1. 编辑配置文件，通常位于`/etc/ansible/hosts`
```config
# 定义了1个主机组和其中的2台主机
[appServers]
113.44.240.123
49.4.115.42
```
2. 执行`ansible-inventory --list -y` ，以 **YAML 格式** 显示当前 Ansible 清单（inventory）中的主机和组信息
3. 在控制节点执行`ssh-keygen`生成SSH公私钥，然后将公钥复制到slave节点上`/root/.ssh/authorized_keys`
```shell
ssh-keygen
ssh-copy-id root@slaveNode_address
```
4. 控制节点执行`ansible all -m ping -u root`命令检测连通性是否正常
## QuickStart Demo
参考： https://docs.ansible.com/ansible/latest/getting_started/index.html
### inventory

> 定义Ansible要控制的节点列表

https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html
- /etc/ansible/hosts：适用于全局的 Ansible 设置，通常由系统管理员维护，默认会被 Ansible 读取
- inventory.ini：适用于特定项目，存放在项目目录中，方便携带、调整和版本管理，优先级高于默认配置。可以是ini格式也可以是yaml格式
![图片](attachments/Pasted_image_20250126163344.png)
### 远程执行shell命令
```shell
#对指定清单文件中的主机组执行shell命令
ansible web_servers -i inventory.ini -m shell -a "df -h"
```
### playbook

| 概念        | 说明                                             |
| --------- | ---------------------------------------------- |
| Playbook  | 定义要执行的自动化任务脚本                                  |
| Play      | 任务执行单元，确定主机和任务                                 |
| Hosts     | 目标主机，在哪些服务器上执行任务                               |
| Tasks     | 具体的操作步骤(如安装包、修改配置等)                            |
| Module    | 提供执行任务的功能模块(如 yum, copy)                       |
| Handlers  | 仅在发生变化时执行的任务(如重启服务)                            |
| Variables | 在 Playbook 中定义的变量                              |
| Templates | 用于动态生成配置文件                                     |
| Roles     | 结构化组织任务的方式，将任务、变量、文件、模板等组件模块化，从而提高playbook的复用性 |
| Tags      | 选择性地执行特定任务                                     |
#### 部署并启动Nginx
##### 目录结构
```
ansible_demo/  # 项目根目录
├── ansible.cfg         # Ansible 配置文件
├── inventory.ini       # 主机清单（Inventory）
├── playbook.yml        # Ansible Playbook
├── files/              # 存放静态文件
│   ├── index.html      # 示例网页文件
├── templates/          # 存放 Jinja2 模板文件
│   ├── nginx.conf.j2   # Nginx 配置模板
```
##### ansible.cfg
**配置文件的读取顺序：**
1. 当前目录中的 ansible.cfg
2. 用户主目录中的 ~/.ansible.cfg
3. 最后是全局配置文件 /etc/ansible/ansible.cfg

> **注意：命令行参数的优先级高于所有配置文件**
```ini
# 自定义的config分组名，对Ansible实际运行无意义
[defaults]
# 指定inventory文件位置
inventory = inventory.ini
```
##### inventory.ini
**库存文件的读取顺序：**
1. 环境变量 ANSIBLE_INVENTORY
2. 配置文件 ansible.cfg
3. 默认库存文件 /etc/ansible/hosts

> **注意：命令行参数的优先级高于所有配置文件**
```ini
# 定义一个主机组，可以包含多个主机
[web_servers]
# 指定要控制的主机，执行任务的用户，ssh连接要使用的私钥位置
1.95.50.185 ansible_user=root ansible_ssh_private_key_file=~/.ssh/id_rsa
```
##### playbook.yml
```yml
# 定义play
- name: Setup Web Server
  hosts: web_servers
  become: yes  # 使用 sudo 权限执行任务
  # 设置变量信息
  vars:
    nginx_port: 80
    server_name: "localhost"
	# 定义task
  tasks:
    # 安装 Nginx 包
    - name: Install Nginx
      apt:
        name: nginx
        state: present
      notify: Restart Nginx  # 安装完成后触发重启服务

    # 部署 Nginx 配置文件
    - name: Deploy Nginx Configuration
      template:
        src: templates/nginx.conf.j2  # j2 模板源文件
        dest: /etc/nginx/nginx.conf   # 目标配置文件位置
      notify: Restart Nginx  # 配置更改后触发重启服务

    # 部署网站首页
    - name: Deploy Web Page
      copy:
        src: files/index.html
        dest: /var/www/html/index.html
        mode: '0644'  # 设置文件权限

    # 确保 Nginx 服务启动并设置开机自启
    - name: Start and Enable Nginx
      service:
        name: nginx
        state: started    # 启动服务
        enabled: yes      # 设置开机自启

  # 定义处理器，被调用时会重启 Nginx
  handlers:
    - name: Restart Nginx
      service:
        name: nginx
        state: restarted
```
**关键点：**

1. become：用于非root用户执行任务时提权（使用sudo执行），如果已经在ansible_user中指定了root用户则不需要该属性
2. template 和 file（或 copy）的主要区别在于**是否需要动态渲染文件**，模板文件用于动态渲染，通常包含 Jinja2 变量，在复制到目标主机前会被 Ansible 处理，模板里的变量的值来自Ansible变量系统（环境变量、命令行参数、playbook/inventory/ansible.cfg文件中定义等）
3. handlers 和 notify ：用于处理特定任务完成后触发其他操作的机制，使用 notify 来指定哪些 handlers 在任务执行后被触发，要注意的是，只有任务执行成功且对目标主机状态做了更改后才会触发handler（可以使用changed_when: true来强制触发）
4. tasks里的`apt`、`copy`、`service`都属于Ansible 提供的预定义模块，用于执行常见的操作，每个模块都有其自定义的参数
5. Ansible强调的是主机的最终状态，而不关心过程，这一点和Terraform等IaC理念相似，因此其所有module被设计成能够判断主机当前的状态，并根据需要进行操作，通过这种方式实现了**幂等性**，playbook无论成功执行多少次，其最终结果都是一致的

##### files/index.html

```html
<!DOCTYPE html>
<html>
<head><title>Welcome to Ansible Nginx!</title></head>
<body>
    <h1>Hello from Ansible-managed server!</h1>
</body>
</html>
```

##### templates/nginx.conf.j2

```nginx
# 定义事件模块配置
events {
  # 设置单个 worker 进程的最大并发连接数
  worker_connections 1024;
}

# HTTP 服务器配置块
http {
  # 定义虚拟主机配置
  server {
    # 监听端口，使用变量配置
    listen {{ nginx_port }};    
    # 配置服务器域名，使用变量配置
    server_name {{ server_name }};
    # 配置根路径的访问规则
    location / {
      # 设置网站根目录路径
      root /var/www/html;
      # 设置默认首页
      index index.html;
    }
  }
}
```

##### playbook相关命令

| 检查内容       | 命令                                           | 作用                       |
| ---------- | -------------------------------------------- | ------------------------ |
| 语法检查       | ansible-playbook playbook.yml --syntax-check | 检查语法错误                   |
| 变量检查       | ansible-playbook playbook.yml --list-vars    | 列出 Playbook 使用的变量        |
| 主机清单检查     | ansible-playbook playbook.yml --list-hosts   | 预览 Playbook 作用的主机        |
| 任务检查       | ansible-playbook playbook.yml --list-tasks   | 列出 Playbook 中的任务         |
| 仅模拟执行      | ansible-playbook playbook.yml --check        | 运行 Playbook 但不修改系统       |
| 文件变更预览     | ansible-playbook playbook.yml --check --diff | 预览 template 或 copy 变更    |
| 代码规范检查     | ansible-lint playbook.yml                    | 检查 Ansible Playbook 代码质量 |
| 运行playbook | ansible-playbook playbook.yml                | 执行定义好的playbook           |


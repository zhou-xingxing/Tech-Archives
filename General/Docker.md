# 安装部署
可参考： https://docs.docker.com/engine/install/
## 以Ubuntu为例
### APT安装
1. 卸载可能存在的旧packages
```shell
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done

rm -rf /var/lib/docker/
```

> Docker Engine 将**containerd** 和 **runc** 作为一个整体（bundle）进行打包，并称其为 **containerd.io**，如果之前单独安装过这两个组件，要先卸载它们，以避免与 Docker 中自带的版本产生冲突。

- **containerd** 是一个高层次的容器管理工具，处理容器生命周期的各个方面，像是镜像管理、容器调度等。
- **runc** 是低级容器运行时，负责容器的实际启动和执行，直接与操作系统交互，使用 Linux 内核的 **namespace**、**cgroups**、**seccomp** 等技术来提供容器的隔离性、资源限制等功能。
- **containerd**接收用户请求，调用 **runc** 来实际创建和运行容器。

2. 添加仓库源并手动安装相关packages
```shell
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

```shell
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

3. 验证
```shell
systemctl status docker.service
sudo docker -v
sudo docker info
# 注意有可能因为网络原因导致镜像拉取失败
sudo docker run hello-world
```
### 纯手工安装
> 安装前卸载旧package以及安装后验证可参考上节

1. 进入 [`https://download.docker.com/linux/ubuntu/dists/`](https://download.docker.com/linux/ubuntu/dists/)
2. 在`对应操作系统版本目录/pool/stable/` 下载以下packages
- `containerd.io_<version>_<arch>.deb`
- `docker-ce_<version>_<arch>.deb`
- `docker-ce-cli_<version>_<arch>.deb`
- `docker-buildx-plugin_<version>_<arch>.deb`
- `docker-compose-plugin_<version>_<arch>.deb`
3. 手动安装
```shell
sudo dpkg -i ./containerd.io_<version>_<arch>.deb \
  ./docker-ce_<version>_<arch>.deb \
  ./docker-ce-cli_<version>_<arch>.deb \
  ./docker-buildx-plugin_<version>_<arch>.deb \
  ./docker-compose-plugin_<version>_<arch>.deb
```

## 配置
Linux系统中主要配置文件位于 `/etc/docker/daemon.json`， 如果没有则新建
### 修改默认镜像源
1. 在`/etc/docker/daemon.json`加入以下内容
注意：很多云厂商的镜像源通常只允许其云内服务器访问
```json
{
   "registry-mirrors": [
   "https://mirror.ccs.tencentyun.com"
  ]
}
```
2. 执行`sudo systemctl restart docker.service`重启Docker服务
### 允许Docker被非root用户管理

> Docker 守护进程绑定到 Unix 套接字而非 TCP 端口，默认 Unix 套接字由 root 用户拥有，其他用户需用 sudo 访问。但该Unix套接字也允许docker用户组的用户访问，所以非root用户如果想直接运行docker命令需加入docker用户组
```shell
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
# 此时不用加sudo应该也能运行
docker run hello-world
```

# 常用命令
## 镜像类
```shell
# tag默认是latest
docker pull <镜像名>:<标签> 
docker images
# -f强制删除正在使用的镜像
docker rmi [-f] <镜像名或ID> 
# 根据当前容器创建镜像，-c参数用于设置容器启动时的默认执行命令
docker container commit -m "message" [-c <命令>] <容器名> <新镜像名>
# 查看镜像历史
docker image history <镜像名>
# 根据Dockerfile构建镜像
docker build -t <镜像名:标签> <镜像构建的上下文目录>

# 查看镜像详细信息
docker inspect <镜像ID>
# 将镜像导出为本地文件
docker save -o <output_file>.tar <image_name>:<tag>
# 将本地文件加载为镜像
docker load -i <output_file>.tar
```
## 容器类
```shell
docker run [参数] <镜像名>
# docker run -d --name my-nginx -p 8080:80 -v /data:/usr/share/nginx/html nginx:alpine

# 查看指定容器日志 -f代表follow 滚动更新
docker logs -f <container_name_or_id>

# 重启容器，此种方式可保留容器内被手动修改的可写层
docker restart <container_name_or_id>

# 强制删除容器，否则需要先停止容器才能删除
docker rm -f <container_name_or_id>
```
核心参数：
- `-d`: 后台运行（detached mode）
- `--name`: 指定容器名称
- `-p`: 端口映射（格式 `宿主机端口:容器端口`）
- `-v`: 数据卷挂载（格式 `宿主机目录:容器目录`）
- `-e`: 设置环境变量（如 `-e MYSQL_ROOT_PASSWORD=123`）
- `--restart`: 重启策略（`always`, `on-failure`）
- `--network`: 指定容器网络
- `--memory:`设置使用内存限制（--memory="512m"）
- `--cpus:`设置使用CPU限制（--cpus="0.5"）
- `--mount:`提供更多高阶功能的数据卷挂载（如限定读写模式）

```shell
docker start <容器ID或名称> 
docker ps [-a]
docker stop <容器ID或名称> 
docker restart <容器ID或名称> 
docker rm [-f] <容器ID或名称> 
# -i:打开标准输入, -t:分配伪终端
docker exec -it <容器ID或名称> /bin/bash
```
# Dockerfile
主要用途：定义如何构建一个Docker镜像
## Docker镜像的分层架构
Dockerfile 中的每一行指令都会生成一个新的镜像层，Docker 会缓存每一层，这意味着如果Dockerfile 没有更改，或者构建上下文没有变化，Docker 在后续构建时会复用这些缓存的层，这样可以加速构建过程。但如果某一层发生了变化（例如，RUN 命令中更改了文件或安装了新的依赖），后续所有层都必须重新构建。

为了优化镜像大小和构建速度，建议：
- **合并多个 RUN 指令到一行，这样可以减少层数**。
- **将经常变化的 COPY 和 ADD 放在 Dockerfile 的最后**（尤其是经常变化的源代码目录），因为每次发生变化都会导致后续所有层重新构建。

## Demo
### 构建一个Python应用镜像
构建前文件目录结构如下
```yaml
src/ # 要构建为镜像的源代码目录
  --> app.py # 应用程序源代码
  --> Dockerfile
  --> pip.conf # pip源配置文件
  --> requirements.txt # python依赖包
```
Dockerfile内容如下：
```Dockerfile
# 指定镜像的基础镜像，slim镜像去掉了一些不必要的操作系统工具和文件，体积更小
FROM python:3.10-slim
# 指定容器内的工作目录，所有接下来的 COPY、RUN、CMD 等命令都会在这个目录下执行
WORKDIR /usr/local/app
# 将本地文件复制到容器内工作目录
COPY ./requirements.txt ./
# 将本地文件复制到容器内指定目录，这里是为了配置构建镜像时使用的pip源，加快python依赖下载速度
COPY ./pip.conf /etc/pip.conf
# 安装python依赖，注意是在构建镜像时安装，而不是运行容器时再安装
# 清理缓存，减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt && rm -rf /root/.cache

# 把可能经常变化的源代码目录放到Dockerfile后面，使前序步骤的layer缓存可以充分利用
COPY ./app.py ./
# 暴露容器的5000端口
EXPOSE 5000
# 指定容器启动时执行的命令
CMD ["python3", "app.py"]
```

执行镜像构建命令
```shell
# 在当前目录根据Dockerfile(默认)构建镜像，-t指定镜像名和标签
docker build -t python-web-app:v1 .
# 验证
docker images
# 运行容器
docker run -d -p 80:5000 python-web-app:v1
```
![](attachments/Pasted%20image%2020250216133022.png)


# Docker网络模式
## bridge网络
Docker会在宿主机上创建一个`bridge`网络（默认网关172.17.0.1/16）。在不显式指定网络模式情况下，容器均使用`bridge`网络，每个容器会被分配`bridge`网络内的一个IP地址，这使得容器之间可以通过`bridge`网络互相通信。

docker0 是宿主机上的虚拟网桥设备，它将容器网络流量与宿主机的物理网络接口进行连接。容器与宿主机之间通过NAT实现端口映射。所有从容器发出的请求都需要通过宿主机的docker0网桥转发。
![](attachments/Pasted%20image%2020250216151740.png)
除了默认的bridge网络，也可以通过`docker network create <mynetwork>`命令创建自定义的bridge网络，该命令会在宿主机内添加一个新的虚拟网桥并分配一个地址段，使用`docker run --network <mynetwork>`命令可指定容器加入自定义的网络

- 默认的bridge网络不会为每个容器自动创建 DNS 解析，既容器之间默认不能通过名称互相访问
- 而在自定义创建的bridge网络中，会为每个容器自动创建DNS解析，容器之间可通过容器名互相访问
# Docker 持久化存储

## Bind Mounts
将本地文件目录挂载到容器文件目录，更适合本地开发，即本地修改代码后用容器的环境运行。在实际生产环境中很少使用，因为在有容器编排调度的情况下（如k8s），容器基本不会固定运行在某个宿主机上。而且这种方式无法避免其他程序对相同的本地文件目录做操作。

Use bind mounts when you need to be able to access files from both the container and the host.

## Named Volumes
实际大规模生产环境中更推荐使用这种，原因如下：
- **自动化管理**：Docker 会自动管理 Volume 的生命周期，免去了手动管理宿主机目录的麻烦。数据存储位置由 Docker 内部管理，用户无需关心，也规避了其他用户或程序直接操作宿主机文件系统的风险。
- **可扩展性和灵活性**：Docker Volumes 支持使用自定义卷驱动程序，允许将数据存储在不同的后端存储中（如云存储、NFS、分布式存储等），更容易进行跨节点共享和管理。

Volumes are not a good choice if you need to access the files from the host, as the volume is completely managed by Docker.

- 如果将一个非空volume挂载到容器内非空文件目录，则容器内原文件会被遮挡
- 如果将一个空volume挂载到容器内非空文件目录，则容器内原文件默认会被复制到volume，除非指定`volume-nocopy`选项

Docker 支持多种 **Volume Driver**，允许用户将容器数据存储到不同存储后端（local, NFS, tmpfs）

### Volume的备份与恢复
Docker Volume无法直接做到备份、迁移、恢复，但可以借助宿主机文件系统进行中转，大致步骤如下：
1. 进入容器A内部，将Volume里的文件拷贝到宿主机本地
2. 在宿主机本地进行文件备份、迁移
3. 进入容器B内部，将迁移后的本地文件拷贝到Volume内
```shell
# 将 /data 目录（即 volume 的内容）压缩成 backup.tar 文件，并保存到宿主机的当前目录
docker run --rm -v my_volume:/data -v $(pwd):/backup ubuntu tar cvf /backup/backup.tar /data

scp backup.tar user@remote_host:/destination

docker volume create my_new_volume
# 解压 backup.tar 到容器内的 /data 目录，即新的volume中
docker run --rm -v my_new_volume:/data -v /destination:/backup ubuntu tar xvf /backup/backup.tar -C /data
```

# Docker Compose
主要用途：定义如何运行多个容器，可以理解为运行一个App Stack

- Docker Compose 会自动创建一个自定义的bridge网络，并将所有定义在 Compose 文件中的服务容器都连接到这个网络中，这使得容器之间**可以通过容器名互相访问**
- 如果多次执行同一 Docker Compose 文件但Compose定义并未修改，则容器状态不会发生变化且不会被重复创建；若Compose定义已经发生了修改，则再次运行Docker Compose时容器也会进行相应更新并重启

## Demo
### Nginx+Flask+Redis
使用Nginx作为负载均衡器轮询后面两个Web应用，并使用Redis实现请求计数。

[跳转到配套代码](./Docker_代码/nginx-flask-redis)

**文件目录结构如下：**
```txt
compose.yml
web/
  --> app.py
  --> requirements.txt
  --> Dockerfile
  --> pip.conf
nginx/
  --> Dockerfile
  --> nginx.conf
```
**compose.yml**
```yaml
# 定义服务
services:
  redis: # 服务（容器）名
    image: redis # 使用官方redis镜像
    ports:
      - '6379:6379' # 设置端口映射
  web1:
    restart: on-failure # 设置重启策略
    build: ./web # 指定镜像构建的上下文目录
    hostname: 'web1' # 设置容器内主机名（非容器名）
    ports:
      - '81:5000' # 设置端口映射
  web2:
    restart: on-failure
    build: ./web
    hostname: 'web2'
    ports:
      - '82:5000'
  nginx:
    build: ./nginx
    ports:
    - '80:80'
    depends_on: # 确保容器启动顺序
    - web1
    - web2
```

进入项目根目录，执行以下命令启动容器们
```shell
# 默认查找并使用当前目录的docker-compose.yml or docker-compose.yaml or compose.yml文件
# --build 强制重新构建镜像  -d 容器后台运行
docker compose up -d --build
# 查看日志
docker compose logs -f [service]
# 停止容器
docker compose stop
# 停止并删除容器、网络
docker compose down
# 停止并删除容器、网络、存储卷
docker compose down --volume
```
![](attachments/Pasted%20image%2020250217235357.png)
# Docker与Jenkins联动

#todo 



# 问题答疑

1. 如果Docker镜像中包含Linux操作系统，那么这个容器使用的是宿主机内核还是容器内操作系统的内核？
	答：Docker容器**始终使用宿主机的内核**，Docker镜像实际上只包含了操作系统的**用户空间**部分，比如
	• **文件系统**：/bin, /lib, /etc等。
	• **系统工具**：如bash, apt, yum。
	• **运行环境**：如glibc, libstdc++等库文件。
	• 例如，一个Ubuntu镜像实际上是Ubuntu的用户空间，包含Ubuntu的软件包管理器apt，但它**不包含内核**

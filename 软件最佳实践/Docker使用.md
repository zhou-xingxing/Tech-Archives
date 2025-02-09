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
docker -v
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
5. 在`/etc/docker/daemon.json`加入以下内容
注意：很多云厂商的镜像源通常只允许其云内服务器访问
```json
{
   "registry-mirrors": [
   "https://mirror.ccs.tencentyun.com"
  ]
}
```
6. 执行`sudo systemctl restart docker.service`重启Docker服务
# 常用命令
## 镜像类
```shell
# tag默认是latest
docker pull <镜像名>:<标签> 
docker images
# -f强制删除正在使用的镜像
docker rmi [-f] <镜像名或ID> 
```
## 容器类
```shell
docker run [参数] <镜像名>
# docker run -d --name my-nginx -p 8080:80 -v /data:/usr/share/nginx/html nginx:alpine
```
核心参数：
- `-d`: 后台运行（detached mode）
- `--name`: 指定容器名称
- `-p`: 端口映射（格式 `宿主机端口:容器端口`）
- `-v`: 数据卷挂载（格式 `宿主机目录:容器目录`）
- `-e`: 设置环境变量（如 `-e MYSQL_ROOT_PASSWORD=123`）
- `--restart`: 重启策略（`always`, `on-failure`）
- `--network`: 指定容器网络

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
## Demo
### 构建一个Python应用镜像
#todo 
- [ ]  构建一个Python应用镜像

# Docker Compose
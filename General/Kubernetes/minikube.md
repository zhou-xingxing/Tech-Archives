一个轻量级Kubernetes发行版，可以快速启动一个单节点k8s集群，方便开发者学习和测试
# 启动
minikube最常见的是以Docker方式启动k8s集群，此时其会先拉取 KICBase（Kubernetes-In-Container Base） Docker镜像，然后启动一个Docker容器，里面运行着k8s集群的各个控制面组件

如果在运行`minikube start`时提示因网络原因无法自动拉取KICBase镜像，可以先手动拉取国内镜像源的镜像，然后再指定minikube使用该镜像
```shell
# 虽然这个镜像地址能公开访问，但阿里云的docker镜像源本身是不对外开放的
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kicbase:v0.0.46

# 由于本人在做实验时用的是腾讯云服务器，所以这里填的是腾讯云的docker镜像源地址
minikube start --force --base-image='registry.cn-hangzhou.aliyuncs.com/google_containers/kicbase:v0.0.46' --docker-opt registry-mirror=https://mirror.ccs.tencentyun.com
```
使用kubectl查看k8s集群所有命名空间里的资源
```shell
alias kubectl="minikube kubectl --"
kubectl get all -A
```

## 示例
在纯外网环境下
```shell
ubuntu@VM-0-13-ubuntu:~$ minikube start
😄  minikube v1.37.0 on Ubuntu 22.04 (amd64)
✨  Automatically selected the docker driver. Other choices: ssh, none

🧯  The requested memory allocation of 1931MiB does not leave room for system overhead (total system memory: 1931MiB). You may face stability issues.
💡  Suggestion: Start minikube with less memory allocated: 'minikube start --memory=1931mb'

📌  Using Docker driver with root privileges
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🚜  Pulling base image v0.0.48 ...
💾  Downloading Kubernetes v1.34.0 preload ...
    > preloaded-images-k8s-v18-v1...:  337.07 MiB / 337.07 MiB  100.00% 7.50 Mi
    > gcr.io/k8s-minikube/kicbase...:  488.51 MiB / 488.52 MiB  100.00% 7.00 Mi
🔥  Creating docker container (CPUs=2, Memory=1931MB) ...
🐳  Preparing Kubernetes v1.34.0 on Docker 28.4.0 ...
🔗  Configuring bridge CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Enabled addons: storage-provisioner, default-storageclass
💡  kubectl not found. If you need it, try: 'minikube kubectl -- get pods -A'
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```
## 访问
**在 Minikube 使用 Docker 驱动时，Node 的 IP 就是 `kicbase` 容器的 IP 地址。**

一种访问方式是通过kubectl客户端本机的端口转发功能
```shell
# 监听来自所有IP的请求，把本机的30099端口转发到指定service的80端口
kubectl port-forward --address 0.0.0.0 svc/nginx-service 30099:80
```

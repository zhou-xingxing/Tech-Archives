一个轻量级Kubernetes发行版，可以快速启动一个单节点k8s集群，方便开发者学习和测试
# 启动
minikube最常见的是以Docker方式启动k8s集群，此时其会先拉取 KICBase（Kubernetes-In-Container Base） Docker镜像，然后启动一个Docker容器，里面运行着k8s集群的各个控制面组件

如果在运行`minikube start`时提示因网络原因无法自动拉取KICBase镜像，可以先手动拉取国内镜像源的镜像，然后再指定minikube使用该镜像
```shell
# 虽然这个镜像地址能公开访问，但阿里云的docker镜像源本身是不对外开放的
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kicbase:v0.0.46

# 由于本人在做实验时用的是腾讯云服务器，所以这里填的是腾讯云的镜像源地址
minikube start --force --base-image='registry.cn-hangzhou.aliyuncs.com/google_containers/kicbase:v0.0.46' --docker-opt registry-mirror=https://mirror.ccs.tencentyun.com
```
使用kubectl查看k8s集群所有命名空间里的资源
```shell
kubectl get all -A
```

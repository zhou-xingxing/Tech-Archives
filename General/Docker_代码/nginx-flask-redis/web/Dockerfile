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

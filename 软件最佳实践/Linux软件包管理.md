# DEB
#todo
- [ ] DEM包离线导出与安装

# RPM
**查看 RPM 包的依赖项**
如果你已经安装了该 RPM 包，可以使用以下命令查看其依赖项：
```shell
rpm -qR package_name
```
如果你有一个未安装的 RPM 包文件，你可以使用 -qpR 选项来查询该 RPM 包文件的依赖项：
```shell
rpm -qpR /path/to/package.rpm
```
# Yum
## yum源更新
```shell
cd /etc/yum.repos.d/
vim <.repo文件>
# 清理缓存
yum clean all
# 重建缓存
yum makecache
# 验证
```
## yum源配置项

| 配置项         | 作用                                                   |
| ----------- | ---------------------------------------------------- |
| [repo_id]   | 仓库 ID，用于唯一标识该 YUM 仓库，例如 [base]、[epel]                |
| name=       | 仓库名称，用于描述该仓库，显示在 yum repolist 命令的输出中                 |
| baseurl=    | 仓库地址，用于指定 RPM 包的下载地址                                 |
| mirrorlist= | 镜像列表地址，YUM 会自动选择最快的镜像源下载，baseurl 和 mirrorlist 只能使用一个 |
| enabled=    | 是否启用该仓库，1 代表启用，0 代表禁用                                |
| gpgcheck=   | 是否启用 GPG 校验，1 表示启用，0 表示禁用                            |
| gpgkey=     | GPG 公钥文件地址，用于验证 RPM 包的来源是否合法                         |
| priority=   | 设置仓库优先级（需要 yum-plugin-priorities 插件），值越小优先级越高        |

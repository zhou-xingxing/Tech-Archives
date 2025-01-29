**查看 RPM 包的依赖项**
如果你已经安装了该 RPM 包，可以使用以下命令查看其依赖项：
```shell
rpm -qR package_name
```
如果你有一个未安装的 RPM 包文件，你可以使用 -qpR 选项来查询该 RPM 包文件的依赖项：
```shell
rpm -qpR /path/to/package.rpm
```

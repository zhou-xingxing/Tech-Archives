# Python虚拟环境
虚拟环境的本质是 ​**创建一个轻量级的隔离目录**，其核心原理是：
1. ​**共享基础解释器**：  
    虚拟环境中的 `python` 可执行文件通常是 ​**符号链接**​（或硬链接）指向系统安装的某个 Python 解释器。
    - 例如，`.venv/bin/python` → `/usr/bin/python3.11`（Linux/macOS）
    - 因此，虚拟环境本身不复制完整的 Python 解释器代码，节省磁盘空间
2. ​**隔离依赖与配置**：
    - ​独立 `site-packages` 目录：存放项目安装的第三方包，与全局环境隔离
    - ​独立环境变量：如 `PYTHONPATH`、`PATH`
    - ​独立配置文件：如 `pyvenv.cfg` 定义环境行为（如是否继承全局包）
	 - 生成一个环境激活脚本
	
```shell
# 创建一个新的虚拟环境
python3 -m venv <虚拟环境名>
# 激活虚拟环境
source venv/bin/activate
# 退出虚拟环境
deactivate
# 查看当前使用的 Python 解释器路径，若虚拟环境正常激活则路径应位于venv/bin下
which python
# 列出已安装的 Python 包
pip list
# 将已安装的包及其版本号导出到 requirements.txt 文件
pip freeze > requirements.txt
# 从 requirements.txt 文件安装所有包
pip install -r requirements.txt
# 将requirements.txt里的包下载到本地指定目录
pip download -r requirements.txt -d ./packages
# 根据requirements.txt从本地目录安装包
pip install --no-index --find-links=./packages -r requirements.txt
```

# Python多版本管理
安装不同版本的 Python 本质上是 ​**下载并安装对应版本的 Python 解释器**。每个版本的 Python 解释器包含：
- ​**核心运行时**：执行 Python 代码的二进制文件（如 `python3.8`、`python3.11`）。
- ​**标准库**：如 `os`、`sys`、`json` 等内置模块。
- ​**工具链**：如 `pip`（包管理工具）、`idle`（简易 IDE）等。
## PyEnv
https://github.com/pyenv/pyenv?tab=readme-ov-file#installation
### 安装部署
```shell
# macos
brew install pyenv

# linux
curl -fsSL https://pyenv.run | bash
# 或
git clone https://github.com/pyenv/pyenv.git ~/.pyenv

```
### 设置环境变量
如果用的是zsh就写入.zshrc文件
```shell
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init - zsh)"' >> ~/.bashrc

source .bashrc
```
### 使用
```shell
# 查看当前已安装的python版本
pyenv versions
# 安装指定版本的python
pyenv install <version>
# 设置全局python版本
pyenv global <version>
# 查找指定python版本的安装目录
pyenv prefix <version>
# 卸载指定版本的python
pyenv uninstall <version>

# 修改下载python时使用的镜像源
export PYTHON_BUILD_MIRROR_URL_SKIP_CHECKSUM=1
export PYTHON_BUILD_MIRROR_URL="https://mirrors.huaweicloud.com/python"

```

# Python快速搭建文件服务器
```shell
# 将当前目录作为文件服务器并指定端口
python -m http.server <port> 

# 客户端获取指定文件
wget http:x.x.x.x:<port>/<文件路径>
```
# Python快速搭建文件服务器（可浏览器访问）
```shell
python3 -m venv ~/uploadenv
cd ~/uploadenv
source ~/uploadenv/bin/activate
pip install uploadserver

python3 -m uploadserver 8000
```
另一台主机即可直接使用浏览器访问：http://ip:8000 实现文件上传下载。

# Python包管理工具-uv
使用Rust编写的Python项目和包管理工具，号称速度极快
https://docs.astral.sh/uv/
## 项目管理
```shell
# 初始化一个新项目
uv init <project>
# 运行脚本或命令
uv run <py script or command>
# 安装Python依赖
uv add <package> --index=https://pypi.tuna.tsinghua.edu.cn/simple
# 设置默认pypi镜像源
export UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
# 删除Python依赖
uv remove <package>
# 升级Python依赖
uv lock --upgrade-package <package>
# 根据uv.lock或pyproject.toml安装依赖，替代pip install -r requirements.txt
uv sync
# 项目打包，生成dist/xx.tar.gz和dist/xx.wheel文件
uv build
```
在使用uv第一次运行项目时，uv会自动创建一个虚拟环境，以及其他依赖管理、版本管理文件
```shell
.
├── .venv
│   ├── bin
│   ├── lib
│   └── pyvenv.cfg
├── .python-version
├── README.md
├── main.py
├── pyproject.toml
└── uv.lock
```
- pyproject.toml: 项目描述信息及依赖信息，可手动修改
- .python-version: 告诉uv使用什么版本的Python创建虚拟环境，可手动修改
- uv.lock: 包含项目确切依赖信息以及包之间依赖关系的锁定文件，不可手动修改
> **pyproject.toml** 是 **“你想要什么”**，声明依赖的 **范围**，但不会锁定具体版本。
> **uv.lock** 是 **“你实际用的是什么”**，锁定 **确切版本**，确保环境一致。

使用`uv run`命令时，会自动激活虚拟环境并使用虚拟环境中的Python运行项目，**如果不使用`uv run`运行Python脚本或命令，记得要先激活虚拟环境**
## 环境管理
```shell
# 安装指定版本的Python
uv python install 3.10 3.11 3.12
# 展示当前可用的Python版本
uv python list
# 指定当前目录使用的Python版本
uv python pin 3.11
# 创建虚拟环境
uv venv
# 创建指定Python版本的虚拟环境
uv venv --python 3.12.0
# 虽然可以使用环境变量修改安装Python时使用的镜像源，但目前还没找到国内有可用的镜像源
# 默认是github上的地址
export UV_PYTHON_INSTALL_MIRROR=https://github.com/astral-sh/python-build-standalone/releases/download
```

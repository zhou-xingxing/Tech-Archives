# 多版本管理
## PyEnv
https://github.com/pyenv/pyenv?tab=readme-ov-file#installation
### 安装
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
pyenv install --list
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
## 虚拟环境
```shell
# 创建一个新的虚拟环境
python3 -m venv <虚拟环境名>
# 激活虚拟环境
source ./bin/activate
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


# opencode 离线安装指南（Linux）

## 第一步：下载对应版本的二进制包和安装脚本

### 1. 确认系统环境

在目标机器上执行以下命令：

```bash
# 检查操作系统和架构
uname -s  # 应输出: Linux
uname -m  # x86_64/aarch64

# 检查 C 库类型（Linux 必需）
ldd --version  # 包含 "musl" → 需要 musl 版本, 包含 "GNU" → 不需要 musl 版本

# 检查 AVX2 支持（Linux 必需）
grep avx2 /proc/cpuinfo  # 无输出 → baseline 版，有输出 → 不需要 baseline 版
```

### 2. 使用浏览器手动下载二进制包

```bash
https://github.com/anomalyco/opencode/releases/
```
#### 版本选择对照表
| 架构 | CPU | C 库 | 下载文件名 |
|------|-----|------|-----------|
| x86_64 | 支持 AVX2 | glibc | `opencode-linux-x64.tar.gz` |
| x86_64 | 旧 CPU | glibc | `opencode-linux-x64-baseline.tar.gz` |
| x86_64 | 支持 AVX2 | musl | `opencode-linux-x64-musl.tar.gz` |
| x86_64 | 旧 CPU | musl | `opencode-linux-x64-baseline-musl.tar.gz` |
| ARM64 | 支持 AVX2 | glibc | `opencode-linux-arm64.tar.gz` |
| ARM64 | 支持 AVX2 | musl | `opencode-linux-arm64-musl.tar.gz` |

### 3. 下载安装脚本

```bash
curl -L https://opencode.ai/install -o install_opencode.sh
```

> **注意**：在有网络的机器上下载后，通过 U 盘/scp/ftp 等方式传输到内网机器。

---

## 第二步：离线安装
### 传输二进制包和安装脚本
将下载好的 `opencode-linux-x64.tar.gz` 和 `install_opencode.sh` 传输到要安装的机器上。

### 解压二进制包

```bash
```bash
mkdir -p opencode_extracted
tar -xzf opencode-linux-x64.tar.gz -C opencode_extracted/
```

解压后会得到 `opencode` 可执行文件。

### 运行安装脚本

```bash
chmod +x install_opencode.sh
./install_opencode.sh --binary ./opencode_extracted/opencode
```

安装选项说明：

| 选项 | 说明 |
|------|------|
| `--binary <路径>` | 从本地二进制文件安装（必需） |
| `--no-modify-path` | 不自动修改 shell 配置文件 |
| `-h, --help` | 显示帮助信息 |

---

## 第三步：验证安装

### 1. 检查环境变量

```bash
# 查看 opencode 是否在 PATH 中
which opencode
# 预期输出: /home/<用户名>/.opencode/bin/opencode

# 检查 PATH 包含安装目录
echo $PATH | grep ".opencode/bin"
```

### 2. 验证版本

```bash
opencode --version
# 预期输出: 1.2.10（或你下载的版本号）
```

### 3. 测试运行

```bash
# 进入任意项目目录
cd /path/to/your/project

# 运行 opencode
opencode
```

---

## 常见问题

### 1. 命令未找到 (command not found)

```bash
# 手动添加环境变量
echo 'export PATH=$HOME/.opencode/bin:$PATH' >> ~/.bashrc  # bash
echo 'export PATH=$HOME/.opencode/bin:$PATH' >> ~/.zshrc   # zsh
source ~/.bashrc  # 或 source ~/.zshrc
```

### 2. 权限不足

```bash
# 确保文件可执行
chmod +x $HOME/.opencode/bin/opencode
```

### 3. 缺少解压工具

```bash
# Ubuntu/Debian
sudo apt-get install tar

# CentOS/RHEL
sudo yum install tar

# Alpine
apk add tar
```

---

## 附录：版本命名规则

| 后缀 | 含义 |
|------|------|
| `-baseline` | 兼容旧 CPU（不支持 AVX2） |
| `-musl` | 使用 musl libc（Alpine Linux） |
| `-arm64` | ARM64 架构 |
| `-x64` | x86_64 架构 |

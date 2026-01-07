#!/bin/bash

# ================= 配置区域 =================
# 建议使用较新的 Go 版本以支持最新的 BN256 库
GO_VERSION="1.21.5"
NODE_VERSION="18.x"
PROJECT_DIR="research-ioporacle-main" # 你的项目解压后的目录名

echo ">>> 🚀 开始部署 IOP Oracle 环境 (Pure Go / BN256 版)..."

# 1. 更新系统并安装基础工具 (去掉了复杂的编译库)
echo ">>> [1/5] 更新系统基础库..."
sudo apt-get update
# python3-venv 和 python3-tk 是为了你的 GUI 界面
sudo apt-get install -y build-essential wget git unzip curl python3-venv python3-tk

# 2. 安装 Go 语言 (这是 BN256 的运行基础)
echo ">>> [2/5] 安装 Go $GO_VERSION..."
if ! command -v go &> /dev/null; then
    wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz
    sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz
    
    # 配置环境变量 (写入 .bashrc 确保下次登录有效)
    # 注意：如果你的 shell 是 zsh，请改为 .zshrc
    if ! grep -q "/usr/local/go/bin" ~/.bashrc; then
        echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    fi
    # 临时生效以便当前脚本使用
    export PATH=$PATH:/usr/local/go/bin
    
    rm go${GO_VERSION}.linux-amd64.tar.gz
    echo "✅ Go 安装完成: $(go version)"
else
    echo "✅ Go 已存在: $(go version)"
fi

# 3. 安装 Node.js 和 Truffle (智能合约环境)
echo ">>> [3/5] 安装 Node.js & Truffle..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION} | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# 检查 Truffle
if ! command -v truffle &> /dev/null; then
    echo "正在全局安装 Truffle..."
    sudo npm install -g truffle
else
    echo "✅ Truffle 已存在"
fi

# 4. 解压项目并自动配置依赖
echo ">>> [4/5] 配置项目代码..."
# 如果有压缩包，先解压
if [ -f "iop_project_pack.zip" ]; then
    echo "检测到压缩包，正在解压..."
    unzip -o iop_project_pack.zip
fi

# 进入合约目录安装 NPM 依赖
if [ -d "$PROJECT_DIR/ioporaclecontracts" ]; then
    cd "$PROJECT_DIR/ioporaclecontracts"
    echo "--- 正在安装合约依赖 (npm install) ---"
    npm install
    cd ../..
fi

# 进入节点目录下载 Go 依赖 (关键步骤：自动下载 BN256)
if [ -d "$PROJECT_DIR/ioporaclenode" ]; then
    cd "$PROJECT_DIR/ioporaclenode"
    echo "--- 正在下载 Go 依赖 (go mod tidy) ---"
    # 这里会自动下载 BN256 等所有 go.mod 里定义的包
    go mod tidy
    cd ../..
fi

# 5. 配置 Python GUI 环境
echo ">>> [5/5] 配置 Python GUI 环境..."
cd "$PROJECT_DIR" || { echo "❌ 找不到项目目录 $PROJECT_DIR"; exit 1; }

# 重建虚拟环境
rm -rf venv 
python3 -m venv venv
source venv/bin/activate

echo "正在安装 GUI 依赖..."
pip install --upgrade pip
# 安装你的 GUI 必需库
pip install customtkinter packaging

echo "========================================================"
echo "🎉🎉🎉 环境部署完成 (BN256 Ready)！ 🎉🎉🎉"
echo "========================================================"
echo "请执行以下步骤启动："
echo "1. source ~/.bashrc  (加载 Go 环境)"
echo "2. cd $PROJECT_DIR"
echo "3. source venv/bin/activate (激活 Python 环境)"
echo "4. python manager_gui.py"
echo "========================================================"

#!/bin/bash

#############################################
# BBS论坛 - Linux一键部署脚本
# 支持Ubuntu/Debian/CentOS系统
# 使用国内镜像源加速安装
#############################################

set -e  # 遇到错误立即退出

echo "===================================="
echo "BBS论坛 - Linux一键部署脚本"
echo "===================================="
echo ""

# 颜色输出函数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 默认端口设置
DEFAULT_HTTP_PORT=8080
HTTP_PORT=${1:-$DEFAULT_HTTP_PORT}  # 支持命令行参数传入端口号

log_info "使用端口: $HTTP_PORT"
echo "提示: 如需自定义端口，请使用: sudo bash $0 <端口号>"
echo ""

# 检测系统类型
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        log_error "无法检测系统类型"
        exit 1
    fi
    log_info "检测到系统: $OS $OS_VERSION"
}

# 配置 Ubuntu/Debian 国内镜像源
configure_apt_mirror() {
    if [[ "$OS" != "ubuntu" && "$OS" != "debian" ]]; then
        return 0
    fi

    log_info "配置 APT 国内镜像源（清华大学）..."

    # 备份原源
    if [ ! -f /etc/apt/sources.list.bak ]; then
        cp /etc/apt/sources.list /etc/apt/sources.list.bak
    fi

    # Ubuntu 24.04 LTS (noble)
    if [[ "$OS" == "ubuntu" && "$OS_VERSION" == "24.04" ]]; then
        cat > /etc/apt/sources.list << 'EOF'
# 清华大学镜像源
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ noble main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ noble-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ noble-backports main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ noble-security main restricted universe multiverse
EOF
    # Ubuntu 22.04 LTS (jammy)
    elif [[ "$OS" == "ubuntu" && "$OS_VERSION" == "22.04" ]]; then
        cat > /etc/apt/sources.list << 'EOF'
# 清华大学镜像源
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse
deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-security main restricted universe multiverse
EOF
    # Debian 12 (bookworm)
    elif [[ "$OS" == "debian" && "$OS_VERSION" == "12" ]]; then
        cat > /etc/apt/sources.list << 'EOF'
# 清华大学镜像源
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib non-free non-free-firmware
deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware
EOF
    else
        log_warn "未找到 $OS $OS_VERSION 的预配置镜像源，跳过"
        return 0
    fi

    log_info "APT 镜像源配置完成"
}

# 配置 CentOS/RHEL 国内镜像源
configure_yum_mirror() {
    if [[ "$OS" != "centos" && "$OS" != "rhel" ]]; then
        return 0
    fi

    log_info "配置 YUM 国内镜像源（阿里云）..."

    # CentOS 7/8
    if [ -f /etc/yum.repos.d/CentOS-Base.repo ]; then
        # 备份原配置
        cp /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bak 2>/dev/null || true

        # CentOS 7
        if grep -q "centos/7" /etc/os-release 2>/dev/null || [ "$OS_VERSION" == "7" ]; then
            cat > /etc/yum.repos.d/CentOS-Base.repo << 'EOF'
# 阿里云 CentOS 7 镜像
[base]
name=CentOS-7 - Base - mirrors.aliyun.com
baseurl=https://mirrors.aliyun.com/centos/7/os/$basearch/
gpgcheck=1
gpgkey=https://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

[updates]
name=CentOS-7 - Updates - mirrors.aliyun.com
baseurl=https://mirrors.aliyun.com/centos/7/updates/$basearch/
gpgcheck=1
gpgkey=https://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

[extras]
name=CentOS-7 - Extras - mirrors.aliyun.com
baseurl=https://mirrors.aliyun.com/centos/7/extras/$basearch/
gpgcheck=1
gpgkey=https://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
EOF
        fi
    fi

    log_info "YUM 镜像源配置完成"
}

# 获取公网IP
get_public_ip() {
    log_info "获取公网IP地址..."
    PUBLIC_IP=$(curl -s --connect-timeout 5 ifconfig.me || curl -s --connect-timeout 5 icanhazip.com || echo "未检测到")
    if [ -n "$PUBLIC_IP" ]; then
        log_info "公网IP: $PUBLIC_IP"
    else
        log_warn "无法获取公网IP"
    fi
}

# 安装Python3 (使用国内源)
install_python() {
    # 检查 Python3 是否已安装
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        log_info "Python3已安装: $PYTHON_VERSION"
    else
        log_info "开始安装Python3..."

        case $OS in
            ubuntu|debian)
                apt-get update
                apt-get install -y python3 python3-pip python3-venv
                ;;
            centos|rhel)
                yum install -y python3 python3-pip python3-devel python3-venv
                ;;
            *)
                log_error "不支持的系统: $OS"
                exit 1
                ;;
        esac

        log_info "Python3安装完成"
    fi

    # 确保 venv 相关包已安装（Ubuntu 24 需要额外安装）
    log_info "检查并安装 venv 模块..."
    case $OS in
        ubuntu|debian)
            apt-get install -y python3-venv python3.12-venv python3-full 2>/dev/null || \
            apt-get install -y python3-venv python3-full || true
            ;;
        centos|rhel)
            yum install -y python3-venv || true
            ;;
    esac

    log_info "Python3 和 venv 模块安装完成"
}

# 更新软件包缓存
update_package_cache() {
    log_info "更新软件包缓存..."

    case $OS in
        ubuntu|debian)
            apt-get update -qq
            ;;
        centos|rhel)
            yum makecache -q
            ;;
    esac

    log_info "软件包缓存更新完成"
}

# 配置pip国内镜像源
configure_pip_mirror() {
    log_info "配置pip国内镜像源（清华大学）..."
    mkdir -p ~/.pip
    cat > ~/.pip/pip.conf << EOF
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 120
EOF
    log_info "pip镜像源配置完成"
}

# 安装Node.js (使用国内源)
install_nodejs() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_info "Node.js已安装: $NODE_VERSION"
        return 0
    fi

    log_info "开始安装Node.js 18 LTS..."

    case $OS in
        ubuntu|debian)
            # 使用NodeSource官方镜像（国内加速）
            curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
            apt-get install -y nodejs
            ;;
        centos|rhel)
            curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
            yum install -y nodejs
            ;;
        *)
            log_error "不支持的系统: $OS"
            exit 1
            ;;
    esac

    log_info "Node.js安装完成: $(node --version)"
}

# 配置npm国内镜像源
configure_npm_mirror() {
    log_info "配置npm国内镜像源（淘宝）..."
    npm config set registry https://registry.npmmirror.com
    log_info "npm镜像源配置完成"
}

# 安装Nginx编译依赖
install_nginx_build_deps() {
    log_info "安装Nginx编译依赖..."

    case $OS in
        ubuntu|debian)
            apt-get install -y build-essential libpcre3-dev zlib1g-dev libssl-dev wget
            ;;
        centos|rhel)
            yum groupinstall -y "Development Tools"
            yum install -y pcre-devel zlib-devel openssl-devel wget
            ;;
        *)
            log_error "不支持的系统: $OS"
            exit 1
            ;;
    esac

    log_info "Nginx编译依赖安装完成"
}

# 从国内源下载并编译安装Nginx到项目目录
install_nginx() {
    # 在函数开始时获取绝对路径，避免 cd 后路径变化
    local SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    NGINX_DIR="$PROJECT_ROOT/nginx"
    LINUX_NGINX_DIR="$NGINX_DIR/linux_nginx"
    NGINX_VERSION="1.24.0"

    # 检查是否已安装
    if [ -f "$LINUX_NGINX_DIR/sbin/nginx" ]; then
        log_info "Nginx已安装在项目目录: $LINUX_NGINX_DIR"
        log_info "版本: $($LINUX_NGINX_DIR/sbin/nginx -v 2>&1)"
        return 0
    fi

    log_info "开始从国内源下载并编译安装Nginx..."
    log_info "项目根目录: $PROJECT_ROOT"
    log_info "Nginx安装目录: $LINUX_NGINX_DIR"

    # 创建目录结构
    mkdir -p "$LINUX_NGINX_DIR"
    mkdir -p "$NGINX_DIR/conf"
    mkdir -p "$NGINX_DIR/logs"
    mkdir -p "$NGINX_DIR/tmp"

    # 安装编译依赖
    install_nginx_build_deps

    # 保存当前目录
    local CURRENT_DIR="$PWD"

    # 下载Nginx源码（使用国内镜像）
    NGINX_TAR_DIR="$NGINX_DIR/nginx-src"
    mkdir -p "$NGINX_TAR_DIR"
    cd "$NGINX_TAR_DIR"

    if [ ! -f "nginx-$NGINX_VERSION.tar.gz" ]; then
        log_info "下载Nginx $NGINX_VERSION 源码（优先使用国内镜像）..."
        # 尝试多个国内镜像源
        DOWNLOADED=false
        for MIRROR in \
            "https://mirrors.huaweicloud.com/nginx" \
            "https://mirrors.aliyun.com/nginx" \
            "https://mirrors.tuna.tsinghua.edu.cn/nginx" \
            "https://nginx.org/download"
        do
            log_info "尝试镜像: $MIRROR"
            if wget --timeout=30 --tries=2 "$MIRROR/nginx-$NGINX_VERSION.tar.gz"; then
                DOWNLOADED=true
                log_info "下载成功: $MIRROR"
                break
            fi
        done

        if [ "$DOWNLOADED" = false ]; then
            log_error "Nginx源码下载失败，所有镜像源均不可用"
            cd "$CURRENT_DIR"
            exit 1
        fi
    fi

    # 解压并编译
    log_info "解压Nginx源码..."
    rm -rf "nginx-$NGINX_VERSION"
    tar -xzf "nginx-$NGINX_VERSION.tar.gz"
    cd "nginx-$NGINX_VERSION"

    log_info "配置Nginx编译选项..."
    log_info "安装前缀: $LINUX_NGINX_DIR"
    ./configure --prefix="$LINUX_NGINX_DIR" \
        --with-http_ssl_module \
        --with-http_gzip_static_module \
        --with-http_realip_module \
        --with-threads \
        --error-log-path="$NGINX_DIR/logs/error.log" \
        --http-log-path="$NGINX_DIR/logs/access.log" \
        --pid-path="$NGINX_DIR/logs/nginx.pid" \
        --lock-path="$NGINX_DIR/logs/nginx.lock" \
        --http-client-body-temp-path="$NGINX_DIR/tmp/client_body" \
        --http-proxy-temp-path="$NGINX_DIR/tmp/proxy" \
        --http-fastcgi-temp-path="$NGINX_DIR/tmp/fastcgi" \
        --http-uwsgi-temp-path="$NGINX_DIR/tmp/uwsgi" \
        --http-scgi-temp-path="$NGINX_DIR/tmp/scgi"

    log_info "编译Nginx (使用$(nproc)个CPU核心)..."
    make -j$(nproc)

    log_info "安装Nginx到项目目录..."
    make install

    # 创建临时目录
    mkdir -p "$NGINX_DIR/tmp/client_body"
    mkdir -p "$NGINX_DIR/tmp/proxy"
    mkdir -p "$NGINX_DIR/tmp/fastcgi"
    mkdir -p "$NGINX_DIR/tmp/uwsgi"
    mkdir -p "$NGINX_DIR/tmp/scgi"

    # 复制公共配置文件到 conf 目录
    log_info "复制配置文件到公共配置目录..."
    CONF_SRC="$PROJECT_ROOT/nginx/nginx-1.29.3/conf"
    if [ -d "$CONF_SRC" ]; then
        cp -f "$CONF_SRC/mime.types" "$NGINX_DIR/conf/" 2>/dev/null || true
        cp -f "$CONF_SRC/fastcgi_params" "$NGINX_DIR/conf/" 2>/dev/null || true
        cp -f "$CONF_SRC/fastcgi.conf" "$NGINX_DIR/conf/" 2>/dev/null || true
        cp -f "$CONF_SRC/scgi_params" "$NGINX_DIR/conf/" 2>/dev/null || true
        cp -f "$CONF_SRC/uwsgi_params" "$NGINX_DIR/conf/" 2>/dev/null || true
        log_info "配置文件复制完成"
    else
        log_warn "未找到源配置目录: $CONF_SRC，跳过复制"
    fi

    # 返回原目录
    cd "$CURRENT_DIR"

    # 验证安装
    if [ ! -f "$LINUX_NGINX_DIR/sbin/nginx" ]; then
        log_error "Nginx安装失败，未找到: $LINUX_NGINX_DIR/sbin/nginx"
        exit 1
    fi

    log_info "Nginx编译安装完成: $LINUX_NGINX_DIR"
    log_info "版本: $($LINUX_NGINX_DIR/sbin/nginx -v 2>&1)"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."

    # 检测防火墙类型
    if command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL firewalld
        firewall-cmd --permanent --add-port=$HTTP_PORT/tcp
        firewall-cmd --reload
        log_info "firewalld防火墙已配置（开放$HTTP_PORT端口）"
    elif command -v ufw &> /dev/null; then
        # Ubuntu/Debian ufw
        ufw allow $HTTP_PORT/tcp
        ufw --force enable
        log_info "ufw防火墙已配置（开放$HTTP_PORT端口）"
    else
        log_warn "未检测到防火墙，请手动开放$HTTP_PORT端口"
    fi
}

# 配置Nginx
configure_nginx() {
    log_info "配置Nginx反向代理..."

    PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
    NGINX_DIR="$PROJECT_ROOT/nginx"
    LINUX_NGINX_DIR="$NGINX_DIR/linux_nginx"
    CONF_DIR="$NGINX_DIR/conf"

    # 确保配置目录存在
    mkdir -p "$CONF_DIR"
    mkdir -p "$NGINX_DIR/logs"

    # 修复目录权限，确保 nginx 可以访问
    log_info "修复目录权限..."
    # 给 home 目录添加执行权限，允许其他用户进入
    chmod +x "$HOME" 2>/dev/null || true
    # 给项目目录及子目录添加读取和执行权限
    chmod -R a+rX "$PROJECT_ROOT/frontend/dist" 2>/dev/null || true
    chmod -R a+rX "$PROJECT_ROOT/backend/uploads" 2>/dev/null || true
    chmod -R a+X "$PROJECT_ROOT" 2>/dev/null || true
    log_info "目录权限修复完成"

    # 生成nginx.conf配置文件（使用绝对路径）
    cat > "$CONF_DIR/nginx.conf" << EOF
# Nginx配置文件 - Linux部署版本
# 生成时间: $(date '+%Y-%m-%d %H:%M:%S')

# 以root用户运行（解决/home目录权限问题）
user root;

# 工作进程数，建议设置为CPU核心数
worker_processes auto;

# 错误日志路径
error_log $NGINX_DIR/logs/error.log;

# PID文件路径
pid $NGINX_DIR/logs/nginx.pid;

events {
    # 每个工作进程的最大连接数
    worker_connections 1024;
}

http {
    include       $CONF_DIR/mime.types;
    default_type  application/octet-stream;

    # 访问日志路径
    access_log $NGINX_DIR/logs/access.log;

    # 开启高效文件传输
    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;

    # 连接超时时间
    keepalive_timeout  65;

    # 请求体大小限制（用于文件上传）
    client_max_body_size 20m;

    # 开启gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml font/truetype font/opentype
               application/vnd.ms-fontobject image/svg+xml;

    # 前端服务器配置
    server {
        listen $HTTP_PORT;
        server_name _;

        # 前端静态文件路径
        root $PROJECT_ROOT/frontend/dist;
        index index.html;

        # 前端路由支持
        location / {
            try_files \$uri \$uri/ /index.html;
        }

        # 代理后端API
        location /api/ {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;

            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 静态文件上传目录
        location /uploads/ {
            alias $PROJECT_ROOT/backend/uploads/;
            expires 7d;
            add_header Cache-Control "public, immutable";
        }

        # 禁止访问隐藏文件
        location ~ /\. {
            deny all;
        }

        # 错误页面
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   $LINUX_NGINX_DIR/html;
        }
    }
}
EOF

    # 创建符号链接到 nginx 安装目录的配置
    ln -sf "$CONF_DIR/nginx.conf" "$LINUX_NGINX_DIR/conf/nginx.conf" 2>/dev/null || true
    ln -sf "$CONF_DIR/mime.types" "$LINUX_NGINX_DIR/conf/mime.types" 2>/dev/null || true

    # 测试配置
    log_info "测试Nginx配置..."
    "$LINUX_NGINX_DIR/sbin/nginx" -t -c "$CONF_DIR/nginx.conf"

    log_info "Nginx配置完成"
    log_info "配置文件位置: $CONF_DIR/nginx.conf"
}

# 创建systemd服务
create_systemd_service() {
    log_info "创建systemd服务..."

    PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

    cat > /etc/systemd/system/mybbs.service << EOF
[Unit]
Description=BBS Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_ROOT/backend
ExecStart=$PROJECT_ROOT/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable mybbs

    log_info "systemd服务创建完成"
}

# 安装后端依赖
install_backend_deps() {
    log_info "[1/6] 安装后端依赖..."

    BACKEND_ROOT="$(cd "$(dirname "$0")/../backend" && pwd)"
    cd "$BACKEND_ROOT"

    log_info "后端目录: $BACKEND_ROOT"

    # 检查虚拟环境是否完整（不只是目录存在）
    VENV_VALID=false
    if [ -d "venv" ]; then
        if [ -f "venv/bin/activate" ] && [ -f "venv/bin/python" ]; then
            log_info "虚拟环境已存在且完整"
            VENV_VALID=true
        else
            log_warn "虚拟环境目录存在但不完整，将重新创建..."
            rm -rf venv
        fi
    fi

    # 创建虚拟环境
    if [ "$VENV_VALID" = false ]; then
        log_info "创建Python虚拟环境..."

        # 直接尝试使用 venv 创建虚拟环境
        if python3 -m venv venv 2>&1; then
            log_info "虚拟环境创建成功"
        else
            log_warn "venv 创建失败，尝试其他方法..."

            # 清理失败的 venv 目录
            rm -rf venv

            # 尝试使用 virtualenv (通过 apt 安装)
            if ! command -v virtualenv &> /dev/null; then
                log_info "安装 virtualenv..."
                case $OS in
                    ubuntu|debian)
                        apt-get install -y virtualenv || {
                            log_error "无法安装 virtualenv"
                            exit 1
                        }
                        ;;
                    centos|rhel)
                        yum install -y python3-virtualenv || {
                            log_error "无法安装 virtualenv"
                            exit 1
                        }
                        ;;
                esac
            fi

            # 使用 virtualenv 创建
            virtualenv venv || {
                log_error "虚拟环境创建失败"
                exit 1
            }
        fi
    fi

    # 最终验证虚拟环境
    if [ ! -f "$BACKEND_ROOT/venv/bin/activate" ]; then
        log_error "虚拟环境激活脚本不存在: $BACKEND_ROOT/venv/bin/activate"
        log_info "当前目录: $PWD"
        log_info "venv 目录内容："
        ls -la venv/ 2>/dev/null || echo "venv 目录不存在"
        log_info "venv/bin 目录内容："
        ls -la venv/bin/ 2>/dev/null || echo "venv/bin 目录不存在"
        exit 1
    fi

    if [ ! -f "$BACKEND_ROOT/venv/bin/python" ]; then
        log_error "虚拟环境 Python 可执行文件不存在"
        exit 1
    fi

    # 激活虚拟环境并安装依赖
    source "$BACKEND_ROOT/venv/bin/activate"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt

    log_info "后端依赖安装完成"
}

# 安装前端依赖
install_frontend_deps() {
    log_info "[2/6] 安装前端依赖..."

    cd "$(dirname "$0")/../frontend"

    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    else
        log_info "前端依赖已存在"
    fi

    log_info "前端依赖检查完成"
}

# 构建前端
build_frontend() {
    log_info "[3/6] 构建前端..."

    cd "$(dirname "$0")/../frontend"

    if [ ! -d "dist" ]; then
        npm run build
    else
        log_info "前端构建已存在"
    fi

    log_info "前端构建完成"
}

# 初始化数据库
init_database() {
    log_info "[4/6] 初始化数据库..."

    BACKEND_ROOT="$(cd "$(dirname "$0")/../backend" && pwd)"
    cd "$BACKEND_ROOT"

    source "$BACKEND_ROOT/venv/bin/activate"

    # 检查数据库文件是否存在
    if [ ! -f "bbs.db" ]; then
        log_info "创建数据库..."
        python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
        log_info "数据库初始化完成"
    else
        log_info "数据库已存在"
    fi
}

# 创建上传目录
create_upload_dirs() {
    log_info "[5/6] 创建上传目录..."

    BACKEND_ROOT="$(cd "$(dirname "$0")/../backend" && pwd)"
    mkdir -p "$BACKEND_ROOT/uploads/avatars"
    mkdir -p "$BACKEND_ROOT/uploads/posts"

    log_info "上传目录创建完成"
}

# 启动服务
start_services() {
    log_info "[6/6] 启动服务..."

    PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
    NGINX_DIR="$PROJECT_ROOT/nginx"
    LINUX_NGINX_DIR="$NGINX_DIR/linux_nginx"
    CONF_DIR="$NGINX_DIR/conf"

    # 启动后端服务
    systemctl start mybbs
    sleep 2

    # 检查后端服务状态
    if systemctl is-active --quiet mybbs; then
        log_info "后端服务启动成功"
    else
        log_error "后端服务启动失败，请查看日志: journalctl -u mybbs"
        exit 1
    fi

    # 停止可能存在的其他nginx进程
    pkill nginx 2>/dev/null || true
    sleep 1

    # 启动项目内的Nginx
    log_info "启动Nginx..."
    "$LINUX_NGINX_DIR/sbin/nginx" -c "$CONF_DIR/nginx.conf"

    sleep 2

    # 检查Nginx是否运行
    if pgrep -x nginx > /dev/null; then
        log_info "Nginx服务启动成功"
        log_info "Nginx PID文件: $NGINX_DIR/logs/nginx.pid"
    else
        log_error "Nginx服务启动失败，请查看日志: $NGINX_DIR/logs/error.log"
        exit 1
    fi
}

# 显示访问信息
show_access_info() {
    PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
    NGINX_DIR="$PROJECT_ROOT/nginx"
    LINUX_NGINX_DIR="$NGINX_DIR/linux_nginx"

    echo ""
    echo "===================================="
    echo "部署完成！"
    echo "===================================="
    echo ""
    log_info "服务访问地址："
    echo "  前端界面: http://$PUBLIC_IP:$HTTP_PORT"
    echo "  后端API:  http://$PUBLIC_IP:$HTTP_PORT/api"
    echo "  API文档:  http://$PUBLIC_IP:$HTTP_PORT/api/docs"
    echo ""
    log_info "目录结构："
    echo "  项目根目录: $PROJECT_ROOT"
    echo "  Nginx安装目录: $LINUX_NGINX_DIR"
    echo "  Nginx配置文件: $NGINX_DIR/conf/nginx.conf"
    echo "  Nginx日志目录: $NGINX_DIR/logs"
    echo ""
    log_warn "注意："
    echo "  1. 端口 $HTTP_PORT 已开放，请确保云服务器安全组也已开放该端口"
    echo "  2. 如果端口无法访问，请检查云服务器控制台的安全组设置"
    echo "  3. 国内常见可用的端口: 8080, 8081, 8082, 9000, 8888"
    echo ""
    log_info "服务管理命令："
    echo "  查看后端状态: systemctl status mybbs"
    echo "  重启后端服务: systemctl restart mybbs"
    echo "  查看Nginx进程: ps aux | grep nginx"
    echo "  重启Nginx: sudo $LINUX_NGINX_DIR/sbin/nginx -s reload"
    echo "  停止Nginx: sudo $LINUX_NGINX_DIR/sbin/nginx -s stop"
    echo ""
    log_info "查看日志："
    echo "  后端日志: journalctl -u mybbs -f"
    echo "  Nginx访问日志: tail -f $NGINX_DIR/logs/access.log"
    echo "  Nginx错误日志: tail -f $NGINX_DIR/logs/error.log"
    echo ""
}

# 主函数
main() {
    # 检测系统
    detect_os

    # 获取公网IP
    get_public_ip

    # 检查是否为root用户
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root用户运行此脚本"
        echo "使用命令: sudo bash $0"
        exit 1
    fi

    # 配置国内镜像源
    configure_apt_mirror
    configure_yum_mirror
    update_package_cache

    # 安装必要软件
    install_python
    configure_pip_mirror
    install_nodejs
    configure_npm_mirror
    install_nginx
    configure_firewall

    # 配置服务
    configure_nginx
    create_systemd_service

    # 安装依赖和构建
    install_backend_deps
    install_frontend_deps
    build_frontend
    init_database
    create_upload_dirs

    # 启动服务
    start_services

    # 显示访问信息
    show_access_info
}

# 执行主函数
main

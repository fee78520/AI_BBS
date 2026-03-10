#!/bin/bash

echo "===================================="
echo "BBS论坛 - Linux部署脚本"
echo "===================================="
echo ""

# 检查是否以root用户运行
if [ "$EUID" -ne 0 ]; then
    echo "[错误] 请使用sudo运行此脚本"
    exit 1
fi

# 设置变量
PROJECT_DIR="$(dirname "$0")/.."
WEB_ROOT="/var/www/bbs"
NGINX_CONF_DIR="/etc/nginx/sites-available"
SYSTEMD_DIR="/etc/systemd/system"

echo "[1/7] 安装系统依赖..."
apt-get update
apt-get install -y python3 python3-venv python3-pip nodejs npm nginx
echo "系统依赖安装完成"

echo ""
echo "[2/7] 创建项目目录..."
mkdir -p $WEB_ROOT
mkdir -p $WEB_ROOT/uploads
echo "项目目录创建完成"

echo ""
echo "[3/7] 部署后端..."
cd $PROJECT_DIR/backend

# 创建虚拟环境
python3 -m venv $WEB_ROOT/backend/venv
source $WEB_ROOT/backend/venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制代码
cp -r app $WEB_ROOT/backend/
cp -r uploads $WEB_ROOT/

# 设置权限
chown -R www-data:www-data $WEB_ROOT
chmod -R 755 $WEB_ROOT

echo "后端部署完成"

echo ""
echo "[4/7] 部署前端..."
cd $PROJECT_DIR/frontend

# 安装依赖
npm install

# 构建前端
npm run build

# 复制构建文件
cp -r dist/* $WEB_ROOT/

echo "前端部署完成"

echo ""
echo "[5/7] 配置Nginx..."
cp $PROJECT_DIR/nginx/nginx-linux.conf /etc/nginx/nginx.conf
cp $PROJECT_DIR/nginx/bbs.conf $NGINX_CONF_DIR/bbs

# 创建软链接
ln -sf $NGINX_CONF_DIR/bbs /etc/nginx/sites-enabled/bbs

# 测试配置
nginx -t

if [ $? -eq 0 ]; then
    systemctl restart nginx
    echo "Nginx配置完成"
else
    echo "[错误] Nginx配置有误"
    exit 1
fi

echo ""
echo "[6/7] 配置Systemd服务..."
cat > $SYSTEMD_DIR/bbs-backend.service <<EOF
[Unit]
Description=BBS Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=$WEB_ROOT/backend
Environment="PATH=$WEB_ROOT/backend/venv/bin"
ExecStart=$WEB_ROOT/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bbs-backend
systemctl start bbs-backend

echo "Systemd服务配置完成"

echo ""
echo "[7/7] 配置防火墙..."
if command -v ufw &> /dev/null; then
    ufw allow 'Nginx Full'
    echo "防火墙规则已添加"
fi

echo ""
echo "===================================="
echo "部署完成！"
echo "===================================="
echo ""
echo "网站访问地址: http://$(hostname -I | awk '{print $1}')"
echo "后端API地址: http://localhost:8000"
echo "API文档地址: http://localhost:8000/docs"
echo ""
echo "服务管理命令："
echo "  启动后端: sudo systemctl start bbs-backend"
echo "  停止后端: sudo systemctl stop bbs-backend"
echo "  重启后端: sudo systemctl restart bbs-backend"
echo "  查看日志: sudo journalctl -u bbs-backend -f"
echo "  重启Nginx: sudo systemctl restart nginx"
echo ""

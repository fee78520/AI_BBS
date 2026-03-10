# Linux 一键部署指南

## 快速开始

在全新的国内 Linux 云服务器上执行以下命令：

```bash
# 1. 下载项目代码
git clone <你的仓库地址>
cd mybbs

# 2. 执行一键部署脚本（需要root权限）
# 使用默认端口 8080
sudo bash scripts/start-linux.sh

# 或者指定自定义端口
sudo bash scripts/start-linux.sh 8081
```

脚本会自动完成以下操作：
1. 检测系统类型（Ubuntu/Debian/CentOS）
2. **配置国内镜像源**：
   - Ubuntu/Debian：清华大学镜像源
   - CentOS/RHEL：阿里云镜像源
3. 使用国内镜像源安装 Python3、Node.js、Nginx
4. 配置 pip（清华镜像）、npm（淘宝镜像）
5. 自动配置 Nginx 反向代理
6. 配置防火墙开放端口（默认 8080）
7. 创建 systemd 服务实现开机自启
8. 获取并显示公网 IP
9. 安装依赖、构建前端、启动服务

**端口说明**：
- 默认使用 8080 端口（避免运营商禁用 80 端口的问题）
- 可通过命令行参数指定端口：`sudo bash scripts/start-linux.sh 8081`
- 常用可用端口：8080、8081、8082、9000、8888

## 系统要求

- **操作系统**: Ubuntu 18.04+ / Debian 9+ / CentOS 7+
- **权限**: root 或 sudo 权限
- **网络**: 公网 IP（用于外部访问）

## 国内镜像源说明

脚本会自动配置以下国内镜像源，加快下载速度：

### APT 软件包镜像（Ubuntu/Debian）
- **源地址**：清华大学镜像
- **支持版本**：Ubuntu 22.04、Ubuntu 24.04、Debian 12
- **配置文件**：`/etc/apt/sources.list`

### YUM 软件包镜像（CentOS/RHEL）
- **源地址**：阿里云镜像
- **支持版本**：CentOS 7
- **配置文件**：`/etc/yum.repos.d/CentOS-Base.repo`

### Python 包镜像
- **源地址**：清华大学 PyPI 镜像
- **配置文件**：`~/.pip/pip.conf`
- **地址**：`https://pypi.tuna.tsinghua.edu.cn/simple`

### npm 包镜像
- **源地址**：淘宝 npm 镜像
- **配置命令**：`npm config set registry https://registry.npmmirror.com`
- **地址**：`https://registry.npmmirror.com`

### 恢复官方源
如果需要恢复官方软件源：
```bash
# Ubuntu/Debian
sudo cp /etc/apt/sources.list.bak /etc/apt/sources.list
sudo apt-get update

# CentOS
sudo cp /etc/yum.repos.d/CentOS-Base.repo.bak /etc/yum.repos.d/CentOS-Base.repo
```

## 访问地址

部署完成后，使用以下地址访问：

```
前端界面: http://你的公网IP:8080
后端API:  http://你的公网IP:8080/api
API文档:  http://你的公网IP:8080/api/docs
```

**重要提示**：
1. 端口 8080 需要在云服务器控制台的安全组中开放
2. 如果使用其他端口（如 8081），则访问地址改为 `http://你的公网IP:8081`
3. 部分云服务商（阿里云、腾讯云、华为云等）需要在安全组中手动开放端口

## 服务管理

### 查看服务状态
```bash
# 后端服务
systemctl status mybbs

# Nginx服务
systemctl status nginx
```

### 重启服务
```bash
# 重启后端
sudo systemctl restart mybbs

# 重启Nginx
sudo systemctl restart nginx
```

### 查看日志
```bash
# 后端实时日志
sudo journalctl -u mybbs -f

# Nginx访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx错误日志
sudo tail -f /var/log/nginx/error.log
```

## 配置文件位置

| 文件 | 路径 |
|------|------|
| Nginx配置 | `/etc/nginx/sites-available/mybbs.conf` |
| systemd服务 | `/etc/systemd/system/mybbs.service` |
| pip配置 | `~/.pip/pip.conf` |
| npm配置 | `~/.npmrc` |

## 常见问题

### 1. 防火墙未开放端口
如果外部无法访问，检查防火墙：

```bash
# Ubuntu/Debian
sudo ufw status
sudo ufw allow 8080/tcp  # 根据实际端口修改

# CentOS/RHEL
sudo firewall-cmd --list-ports
sudo firewall-cmd --permanent --add-port=8080/tcp  # 根据实际端口修改
sudo firewall-cmd --reload
```

### 2. 云服务器安全组未开放端口
脚本只能配置服务器防火墙，**云服务商的安全组需要手动配置**：

- **阿里云**: 进入 ECS 控制台 → 安全组 → 添加规则 → 开放端口 8080
- **腾讯云**: 进入 CVM 控制台 → 安全组 → 添加规则 → 开放端口 8080
- **华为云**: 进入 ECS 控制台 → 安全组 → 添加规则 → 开放端口 8080
- **其他云服务商**: 查找"安全组"或"防火墙"设置，开放对应端口

**安全组配置示例**：
- 协议类型: TCP
- 端口范围: 8080 (或你指定的端口)
- 授权对象: 0.0.0.0/0 (允许所有IP访问)

### 2. Nginx 配置错误
测试 Nginx 配置：
```bash
sudo nginx -t
```

### 3. 后端服务启动失败
查看详细日志：
```bash
sudo journalctl -u mybbs -n 50
```

### 4. 端口被占用
检查端口占用：
```bash
sudo netstat -tulpn | grep :8080
sudo netstat -tulpn | grep :8000
```

### 5. 8080 端口仍无法访问
如果配置了防火墙和安全组后仍无法访问，尝试：

```bash
# 1. 检查端口是否监听
sudo netstat -tulpn | grep nginx

# 2. 检查 Nginx 配置
sudo nginx -t

# 3. 重启 Nginx
sudo systemctl restart nginx

# 4. 查看防火墙状态
sudo ufw status  # Ubuntu/Debian
sudo firewall-cmd --list-ports  # CentOS/RHEL

# 5. 尝试其他端口
sudo bash scripts/start-linux.sh 9000
```

## 更新部署

当代码更新后，只需重新执行部署脚本：

```bash
cd mybbs
sudo bash scripts/start-linux.sh
```

脚本会自动检测已安装的软件和依赖，只执行必要的更新。

## 开机自启

脚本已配置自动开机自启：
- 后端服务：`systemctl enable mybbs`
- Nginx服务：`systemctl enable nginx`

如需禁用：
```bash
sudo systemctl disable mybbs
sudo systemctl disable nginx
```

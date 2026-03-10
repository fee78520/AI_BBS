@echo off
chcp 65001 >nul
echo ====================================
echo BBS论坛 - Windows启动脚本
echo ====================================
echo.

cd /d "%~dp0.."

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

:: 检查Node.js是否安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)

echo [1/5] 检查后端依赖...
cd backend
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)
call venv\Scripts\activate.bat

if not exist "requirements.txt" (
    echo [错误] 未找到requirements.txt
    pause
    exit /b 1
)

pip install  -q -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
echo 后端依赖已安装

echo.
echo [2/5] 检查前端依赖...
cd ..\frontend
if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install --registry=https://registry.npmmirror.com/
) else (
    echo 前端依赖已存在
)

echo.
echo [3/5] 构建前端...
call npm run build
if %errorlevel% neq 0 (
    echo [错误] 前端构建失败
    pause
    exit /b 1
)
echo 前端构建完成

echo.
echo [4/5] 检查nginx...
cd ..\nginx\nginx-1.29.3
if not exist "nginx.exe" (
    echo [错误] 未找到nginx.exe，请先安装nginx
    pause
    exit /b 1
)
echo 停止已运行的nginx...
taskkill /F /IM nginx.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo 启动nginx...
start "" nginx.exe
echo nginx已启动

echo.
echo [5/5] 启动后端服务...
cd /d "%~dp0..\backend"
call venv\Scripts\activate.bat
echo ====================================
echo 所有服务启动完成！
echo ====================================
echo 前端页面地址: http://localhost:80
echo API文档地址: http://localhost:18888/docs
echo.
echo 按 Ctrl+C 停止后端服务
echo 注意：nginx需要手动停止，运行: cd nginx\nginx-1.29.3 && nginx.exe -s stop
echo ====================================
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 18888 --reload

pause

@echo off
chcp 65001 >nul
echo ====================================
echo BBS论坛 - 停止服务
echo ====================================
echo.

cd /d "%~dp0.."

echo [1/2] 停止 nginx...
cd nginx\nginx-1.29.3
if exist "nginx.exe" (
    taskkill /F /IM nginx.exe >nul 2>&1
    echo nginx 已停止
) else (
    echo [警告] 未找到 nginx.exe
)

echo.
echo [2/2] 停止后端服务...
echo 请手动关闭运行后端的终端窗口（按 Ctrl+C）
echo 或使用任务管理器结束 python.exe 进程

echo.
echo ====================================
echo nginx 停止完成
echo 后端服务需要手动停止
echo ====================================
echo.

pause

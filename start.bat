@echo off
chcp 65001 >nul
title 码途智伴 v2.0 - 启动中...

echo.
echo ╔══════════════════════════════════════════╗
echo ║     🤖 码途智伴 - 编程教学AI引擎        ║
echo ║     便携版 v2.0                          ║
echo ╚══════════════════════════════════════════╝
echo.

:: 获取脚本所在目录
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] 未找到 Python，正在安装便携版 Python...
    if not exist "python-embed" (
        echo [X] 请先下载 Python 嵌入版到 python-embed 文件夹
        pause
        exit
    )
    set "PATH=%BASE_DIR%python-embed;%PATH%"
)

:: 检查 Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未找到 Node.js，前端需要 Node.js 运行
    echo [!] 请安装 Node.js 或使用打包后的前端
)

:: 创建虚拟环境（首次）
if not exist "env" (
    echo [*] 首次运行，正在创建虚拟环境...
    python -m venv env
    call env\Scripts\activate
    echo [*] 安装后端依赖...
    pip install -r backend\requirements.txt -q
) else (
    call env\Scripts\activate
)

:: 设置环境变量
set HF_ENDPOINT=https://hf-mirror.com
if "%ZHIPU_API_KEY%"=="" (
    echo [!] 未设置 ZHIPU_API_KEY，请手动输入或设置环境变量
    set /p ZHIPU_API_KEY="请输入智谱 API Key (回车跳过): "
)

:: 启动后端
echo [*] 启动后端服务...
start "后端-码途智伴" cmd /c "cd /d %BASE_DIR%backend && ..\env\Scripts\activate && set HF_ENDPOINT=https://hf-mirror.com && set ZHIPU_API_KEY=%ZHIPU_API_KEY% && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"

:: 等待后端启动
echo [*] 等待后端启动（约15秒）...
timeout /t 15 /nobreak >nul

:: 启动前端
echo [*] 启动前端界面...
start "前端-码途智伴" cmd /c "cd /d %BASE_DIR%frontend && npm run dev"

:: 打开浏览器
echo [*] 打开浏览器...
timeout /t 8 /nobreak >nul
start http://localhost:5173

echo.
echo ╔══════════════════════════════════════════╗
echo ║  启动完成！                              ║
echo ║  学生端: http://localhost:5173           ║
echo ║  教师端: http://localhost:5173/admin     ║
echo ║  API文档: http://localhost:8001/docs     ║
echo ║  登录: student/123456  admin/admin123    ║
echo ╚══════════════════════════════════════════╝
echo.
echo 按任意键停止所有服务...
pause >nul

:: 停止服务
taskkill /FI "WINDOWTITLE eq 后端-码途智伴*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 前端-码途智伴*" /T /F >nul 2>&1
echo 已停止所有服务
pause
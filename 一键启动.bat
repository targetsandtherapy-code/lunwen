@echo off
chcp 65001 >nul
title 论文参考文献智能生成工具

echo ================================================
echo   论文参考文献智能生成工具
echo ================================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 安装依赖
echo 正在检查依赖...
pip install requests beautifulsoup4 python-docx openai streamlit >nul 2>&1
echo 依赖检查完成

:: 设置环境变量
set NO_PROXY=localhost,127.0.0.1
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo.
echo 正在启动服务...
echo 浏览器将自动打开
echo.
echo 关闭此窗口即可停止服务
echo ------------------------------------------------

:: 启动
streamlit run "%~dp0app.py" --server.port 8501 --server.headless true --browser.gatherUsageStats false

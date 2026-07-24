@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   BJTU 校园网自动登录 — 打包构建
echo ============================================================
echo.

:: 检查 Python
echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.7+
    pause & exit /b 1
)
python --version

:: 安装依赖
echo.
echo [2/3] 安装依赖...
pip install -r requirements.txt -q
pip install pyinstaller -q
if %errorlevel% neq 0 (
    echo [警告] 依赖安装可能有问题，继续...
)

:: PyInstaller 打包
echo.
echo [3/3] PyInstaller 打包中 (预计 2~5 分钟)...
echo.

if exist "dist" rmdir /s /q "dist" 2>nul
if exist "build" rmdir /s /q "build" 2>nul

pyinstaller BJTUAutoLogin.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo [错误] 打包失败！
    pause & exit /b 1
)

echo.
echo ============================================================
echo   打包完成！
echo   输出: dist\BJTUAutoLogin.exe
echo ============================================================
echo.
pause

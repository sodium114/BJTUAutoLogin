@echo off
chcp 65001 >nul
title BJTU校园网自动登录 - 安装程序

echo ========================================
echo BJTU校园网自动登录 - 一键安装
echo ========================================
echo.

cd /d "%~dp0.."

:: ========== [1] 检查 Python ==========
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未找到Python，请先安装 Python 3.7+
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo   Python版本: %%i
echo   Python 检查通过
echo.

:: ========== [2] 安装依赖 ==========
echo [2/4] 安装依赖包...
pip install pyinstaller -q
pip install -r requirements.txt -q
echo   依赖安装完成
echo.

:: ========== [3] 打包 EXE ==========
echo [3/4] 正在打包无黑框 EXE（约1-3分钟）...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "*.spec" del /q "*.spec"

python -m PyInstaller --noconfirm --onefile --noconsole --icon="resources\icon.ico" --name="BJTUAutoLogin" --add-data="resources\config.json;." --add-data="resources\icon.ico;." src\main.pyw

if %errorlevel% neq 0 (
    echo.
    echo 打包失败！请检查错误信息
    pause
    exit /b 1
)
echo   打包成功！
echo.

:: ========== [4] 安装到系统 ==========
echo [4/4] 安装到系统...
set "INSTALL_DIR=%LOCALAPPDATA%\BJTUAutoLogin"
set "TASK_NAME=BJTUAutoLogin"
set "EXE_PATH=%INSTALL_DIR%\BJTUAutoLogin.exe"

:: 创建安装目录
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: 复制文件
copy /y "dist\BJTUAutoLogin.exe" "%INSTALL_DIR%\" >nul
copy /y "resources\config.json" "%INSTALL_DIR%\" >nul
copy /y "resources\icon.ico" "%INSTALL_DIR%\" >nul
echo   文件已复制到: %INSTALL_DIR%

:: 创建开机自启任务
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    schtasks /delete /tn "%TASK_NAME%" /f >nul
)
schtasks /create /tn "%TASK_NAME%" /tr "\"%EXE_PATH%\"" /sc onlogon /rl highest /f >nul
echo   开机自动启动已设置

:: 创建桌面快捷方式
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\BJTUAutoLogin.lnk"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%EXE_PATH%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()" >nul
echo   桌面快捷方式已创建
echo.

echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 安装位置: %INSTALL_DIR%
echo 桌面快捷方式: BJTUAutoLogin
echo.
echo 程序特点：
echo - 无窗口后台运行
echo - 开机自动启动
echo - 系统托盘图标（右键菜单）
echo - 自动检测WiFi并登录
echo.
echo 如有问题请查看: %INSTALL_DIR%\login.log
echo.
pause

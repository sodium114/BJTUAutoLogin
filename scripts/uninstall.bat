@echo off
chcp 65001 >nul
title BJTU校园网自动登录 - 卸载程序

echo ========================================
echo BJTU校园网自动登录 - 卸载程序
echo ========================================
echo.

set "TASK_NAME=BJTUAutoLogin"
set "INSTALL_DIR=%LOCALAPPDATA%\BJTUAutoLogin"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\BJTUAutoLogin.lnk"

:: 删除开机自启任务
echo [1/3] 删除开机自启任务...
schtasks /query /tn "%TASK_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    schtasks /delete /tn "%TASK_NAME%" /f >nul
    echo   已删除
) else (
    echo   任务不存在，跳过
)
echo.

:: 删除桌面快捷方式
echo [2/3] 删除桌面快捷方式...
if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo   已删除
) else (
    echo   快捷方式不存在，跳过
)
echo.

:: 删除安装目录
echo [3/3] 删除安装文件...
if exist "%INSTALL_DIR%" (
    rd /s /q "%INSTALL_DIR%"
    echo   已删除: %INSTALL_DIR%
) else (
    echo   安装目录不存在，跳过
)
echo.

echo ========================================
echo 卸载完成！
echo ========================================
echo.
echo 项目文件夹未被删除，如需彻底移除请手动删除本文件夹
echo.
pause

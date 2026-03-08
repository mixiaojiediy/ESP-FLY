@echo off
chcp 65001 >nul
echo ========================================
echo ESP-FLY-PC 打包脚本
echo ========================================
echo.

REM 激活 .venv 虚拟环境
if exist .venv\Scripts\activate.bat (
    echo [提示] 正在激活 .venv 虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo [警告] 未找到 .venv 虚拟环境，将使用系统 Python
)

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8 或更高版本
    pause
    exit /b 1
)

echo [1/5] 检查依赖包...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装 PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        pause
        exit /b 1
    )
)

echo [2/5] 检查项目依赖...
if not exist requirements.txt (
    echo [错误] 未找到 requirements.txt 文件
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo [警告] 部分依赖包安装失败，但继续打包...
)

echo [3/5] 生成启动画面...
python create_splash_image.py
if errorlevel 1 (
    echo [警告] 启动画面生成失败，将继续打包...
)

echo [4/5] 清理旧的打包文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo [5/5] 开始打包...
pyinstaller build_exe.spec

if errorlevel 1 (
    echo.
    echo [错误] 打包失败，请检查错误信息
    pause
    exit /b 1
)

REM 删除 dist 根目录下多余的中间 exe 文件
if exist dist\ESP-FLY-PC.exe (
    del /q dist\ESP-FLY-PC.exe
    echo [提示] 已清理多余的中间文件 dist\ESP-FLY-PC.exe
)

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo.
echo 可执行文件位置: dist\ESP-FLY-PC\ESP-FLY-PC.exe
echo.
echo 注意：
echo 1. 请进入 dist\ESP-FLY-PC\ 文件夹，双击其中的 ESP-FLY-PC.exe 运行
echo 2. 必须保持整个 ESP-FLY-PC 文件夹完整，不能单独复制 exe 文件
echo 3. config.ini 已打包进程序，首次运行会自动创建用户配置文件
echo.
pause

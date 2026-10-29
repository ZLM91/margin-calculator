@echo off
chcp 936 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

set "NODE=C:\Users\C Z\.workbuddy\binaries\node\versions\22.22.2\node.exe"

echo ==========================================
echo   校验 TikTok 文案品类
echo ==========================================
echo.

if not exist "%NODE%" (
    echo [错误] 找不到 Node: %NODE%
    pause
    exit /b 1
)

echo 已有品类 key 对照:
echo   wetwipes=湿厕纸   travel=旅行装湿厕纸
echo   facial=洗脸巾     babywipes=纯水婴儿湿巾
echo   toothpaste=牙膏   mudmask=控油清洁泥膜
echo   cleanser=洁面啫喱 pet=宠物清洁手套
echo.

set KEY=babywipes
set /p INPUT=请输入要校验的品类 key(直接回车用 babywipes): 
if not "!INPUT!"=="" set KEY=!INPUT!

echo.
echo 正在校验 [%KEY%]...
echo ------------------------------------------
"%NODE%" tools\verify_copy.js --repo "%CD%" --key !KEY! --expect 18
set RC=!ERRORLEVEL!
if !RC! NEQ 0 (
    echo.
    echo [失败] 退出码 !RC!，上面列出了具体问题。
) else (
    echo.
    echo [成功] 校验通过。
)

echo.
pause

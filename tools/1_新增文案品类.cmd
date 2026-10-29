@echo off
chcp 936 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

set "PY=C:\Users\C Z\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "NODE=C:\Users\C Z\.workbuddy\binaries\node\versions\22.22.2\node.exe"

echo ==========================================
echo   新增 TikTok 文案品类
echo ==========================================
echo.

if not exist "%PY%" (
    echo [错误] 找不到 Python: %PY%
    pause
    exit /b 1
)

if not exist "tools\new_category.json" (
    echo [错误] 找不到配置文件 tools\new_category.json
    echo.
    echo 请先把 tools\new_category.example.json 复制一份为:
    echo     tools\new_category.json
    echo 然后按里面的说明填写品类和文案文件路径。
    echo.
    pause
    exit /b 1
)

echo 第一步: 先预览将要做的改动（不写文件）
echo ------------------------------------------
"%PY%" tools\add_copy_category.py --config tools\new_category.json --dry-run
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo [失败] 预览就出错了，已中止，什么都没改。
    echo 检查 tools\new_category.json 里的路径和字段。
    pause
    exit /b 1
)

echo.
echo ------------------------------------------
set /p CONFIRM=确认要写入吗？(y/n): 
if /i not "%CONFIRM%"=="y" (
    echo 已取消，未做任何改动。
    pause
    exit /b 0
)

echo.
echo 第二步: 正式写入并校验
echo ------------------------------------------
"%PY%" tools\add_copy_category.py --config tools\new_category.json
set RC=!ERRORLEVEL!
if !RC! NEQ 0 (
    echo.
    echo [失败] 退出码 !RC!
    echo 上面有具体报错。改动可能已部分写入。
    echo 可用 git checkout . 全部放弃，或用 git diff 看改了什么。
) else (
    echo.
    echo [成功] 文案已加入，index.html 三处已同步，校验通过。
    echo.
    echo 接下来请自己执行:
    echo   git diff              先看一眼改动
    echo   git add . ^&^& git commit -m "feat(copy): ..."
    echo   git fetch             推送前先确认远端有没有别人新推的提交
    echo   git push origin main
)

echo.
pause

@echo off
echo 🧪 Testing DinariBlockchain RPC Client...
echo.

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment activated
)

echo.
echo 📡 RPC Client Test
echo    Target Server: http://127.0.0.1:8545/rpc
echo.
echo ⚠️  Make sure RPC server is running first!
echo    Run: scripts\start_rpc_server.bat
echo.

pause

echo Running RPC client demo...
echo.

REM Run the RPC client demo
python rpc\rpc_client.py

echo.
echo RPC Client test completed.
pause
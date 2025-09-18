@echo off
echo 🚀 Starting DinariBlockchain RPC Server...
echo.

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo ✅ Virtual environment activated
)

REM Set environment variables
set NODE_ENV=development
set NODE_ID=rpc_node_1

echo.
echo 📡 RPC Server Details:
echo    URL: http://127.0.0.1:8545/rpc
echo    Health Check: http://127.0.0.1:8545/health
echo    Web Interface: http://127.0.0.1:8545/
echo.
echo Press Ctrl+C to stop the server
echo.

REM Change to project root directory and start the RPC server
cd ..
python rpc\rpc_server.py --host 127.0.0.1 --port 8545 --node-id rpc_node_1

echo.
echo RPC Server stopped.
pause
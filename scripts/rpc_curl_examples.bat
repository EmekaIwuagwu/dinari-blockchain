@echo off
echo 🌍 DinariBlockchain RPC Examples using curl
echo ============================================
echo.

set RPC_URL=http://127.0.0.1:8545/rpc

echo ⚠️  Make sure RPC server is running first!
echo    Run: scripts\start_rpc_server.bat
echo.
pause

echo.
echo 🔍 Testing ping...
curl -X POST %RPC_URL% ^
  -H "Content-Type: application/json" ^
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"dinari_ping\",\"params\":[],\"id\":1}"
echo.
echo.

echo 📋 Getting version...
curl -X POST %RPC_URL% ^
  -H "Content-Type: application/json" ^
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"dinari_getVersion\",\"params\":[],\"id\":2}"
echo.
echo.

echo 📊 Getting blockchain info...
curl -X POST %RPC_URL% ^
  -H "Content-Type: application/json" ^
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"dinari_getBlockchainInfo\",\"params\":[],\"id\":3}"
echo.
echo.

echo 💰 Getting treasury balance...
curl -X POST %RPC_URL% ^
  -H "Content-Type: application/json" ^
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"dinari_getBalance\",\"params\":[\"treasury\"],\"id\":4}"
echo.
echo.

echo 🏆 Getting validators...
curl -X POST %RPC_URL% ^
  -H "Content-Type: application/json" ^
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"dinari_getValidators\",\"params\":[],\"id\":5}"
echo.
echo.

echo 💸 Sending test transaction...
curl -X POST %RPC_URL% ^
  -H "Content-Type: application/json" ^
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"dinari_sendTransaction\",\"params\":[\"treasury\",\"test_account\",\"50\",\"0.1\"],\"id\":6}"
echo.
echo.

echo ⛏️  Mining a block...
curl -X POST %RPC_URL% ^
  -H "Content-Type: application/json" ^
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"dinari_mineBlock\",\"params\":[],\"id\":7}"
echo.
echo.

echo 🎉 All RPC examples completed!
echo.
pause
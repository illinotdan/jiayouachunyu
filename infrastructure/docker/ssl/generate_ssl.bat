@echo off
:: SSL证书生成脚本（Windows版本）
:: 用于生成自签名SSL证书（开发环境使用）

echo 🔐 生成SSL证书...

:: 创建ssl目录
if not exist ssl mkdir ssl

:: 检查OpenSSL是否安装
where openssl >nul 2>&1
if errorlevel 1 (
    echo ❌ OpenSSL未安装
    echo 请安装OpenSSL或下载Windows版本
    echo 下载地址: https://slproweb.com/products/Win32OpenSSL.html
    pause
    exit /b 1
)

:: 生成私钥
openssl genrsa -out ssl/key.pem 2048

:: 生成证书签名请求
openssl req -new -key ssl/key.pem -out ssl/cert.csr -subj "/C=CN/ST=Beijing/L=Beijing/O=Dota2Analytics/CN=localhost"

:: 生成自签名证书
openssl x509 -req -days 365 -in ssl/cert.csr -signkey ssl/key.pem -out ssl/cert.pem

:: 删除CSR文件
del ssl\cert.csr

echo ✅ SSL证书生成完成！
echo 证书文件: ssl\cert.pem
echo 私钥文件: ssl\key.pem
echo.
echo ⚠️  注意：这是自签名证书，仅用于开发环境。
echo 生产环境请使用有效的SSL证书。
pause
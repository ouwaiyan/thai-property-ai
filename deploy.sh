#!/bin/bash
# ═══════════════════════════════════════════════════
# ThaiEstate VPS 一键部署脚本
# 使用方法: chmod +x deploy.sh && ./deploy.sh
# ═══════════════════════════════════════════════════
set -e

echo "╔════════════════════════════════════════╗"
echo "║   ThaiEstate VPS Deploy Script        ║"
echo "╚════════════════════════════════════════╝"

# ── 1. 环境检查 ──
if ! command -v docker &> /dev/null; then
    echo ">>> 安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo ">>> 安装 Docker Compose..."
    sudo apt-get update && sudo apt-get install -y docker-compose-plugin
fi

# ── 2. 准备环境文件 ──
if [ ! -f .env ]; then
    echo ">>> 创建 .env 文件..."
    cp .env.production .env
    echo "⚠ 请编辑 .env 填入真实的 API Key 和密码后重新运行此脚本"
    exit 1
fi

# ── 3. 准备 SSL 目录 ──
mkdir -p nginx/ssl
if [ ! -f nginx/ssl/fullchain.pem ]; then
    echo ">>> 生成自签名 SSL 证书 (仅测试，生产请用 Let's Encrypt)..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/privkey.pem \
        -out nginx/ssl/fullchain.pem \
        -subj "/CN=your-domain.com"
fi

# ── 4. 构建并启动 ──
echo ">>> 构建 Docker 镜像..."
docker compose build

echo ">>> 启动服务..."
docker compose up -d

echo ">>> 等待数据库就绪..."
sleep 10

# ── 5. 运行数据库迁移 ──
echo ">>> 运行数据库迁移..."
docker compose exec -T backend alembic upgrade head

# ── 6. 种子数据 ──
echo ">>> 创建初始账号..."
docker compose exec -T backend python seed.py

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  部署完成!                            ║"
echo "║  访问: https://your-domain.com        ║"
echo "║  管理员: admin@thaiestate.com         ║"
echo "║  密码:   admin123                     ║"
echo "║                                       ║"
echo "║  查看日志: docker compose logs -f     ║"
echo "║  停止服务: docker compose down        ║"
echo "╚════════════════════════════════════════╝"

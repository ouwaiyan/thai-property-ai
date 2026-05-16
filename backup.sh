#!/bin/bash
# ══════════════════════════════════════════════
# 数据库自动备份脚本 (建议 crontab 每日执行)
# 0 3 * * * /path/to/backup.sh
# ══════════════════════════════════════════════
BACKUP_DIR="./backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "[$(date)] 开始备份..."

docker compose exec -T postgres pg_dump \
    -U ${POSTGRES_USER:-postgres} \
    -d ${POSTGRES_DB:-thai_estate_db} \
    --clean --if-exists --no-owner \
    > "$BACKUP_DIR/backup_$TIMESTAMP.sql"

# 压缩
gzip "$BACKUP_DIR/backup_$TIMESTAMP.sql"

# 删除 30 天前的备份
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] 备份完成: backup_$TIMESTAMP.sql.gz"
echo "当前备份文件:"
ls -lh "$BACKUP_DIR" | tail -5

#!/bin/bash

# Configuración básica
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$DATE"

echo "Creando backup: $DATE"

# Crear carpeta
mkdir -p $BACKUP_DIR

# Backup del volumen etcd
docker run --rm -v apisix_etcd_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/etcd.tar.gz -C /data .

# Backup de archivos locales
tar czf $BACKUP_DIR/archivos.tar.gz apisix_conf/ dashboard_conf/ dashboard_logs/ apisix_logs/ docker-compose.yml

# Limpiar backups viejos (más de 7 días)
find ./backups -type d -name "20*" -mtime +7 -exec rm -rf {} \; 2>/dev/null

echo "Backup completado en: $BACKUP_DIR"
ls -lh $BACKUP_DIR

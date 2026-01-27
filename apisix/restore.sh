#!/bin/bash

if [ -z "$1" ]; then
    echo "Uso: $0 <carpeta_backup>"
    echo "Backups disponibles:"
    ls -1 ./backups/ | grep "20"
    exit 1
fi

BACKUP_DIR="$1"

echo "Restaurando desde: $BACKUP_DIR"

# Parar servicios
docker compose down

# Restaurar etcd
if [ -f "$BACKUP_DIR/etcd.tar.gz" ]; then
    docker volume rm apisix_etcd_data 2>/dev/null || true
    docker volume create apisix_etcd_data
    docker run --rm -v apisix_etcd_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar xzf /backup/etcd.tar.gz -C /data
    echo "✓ etcd restaurado"
fi

# Restaurar archivos
if [ -f "$BACKUP_DIR/archivos.tar.gz" ]; then
    tar xzf $BACKUP_DIR/archivos.tar.gz
    echo "✓ Archivos restaurados"
fi

# Iniciar servicios
docker compose up -d

echo "Restauración completada"

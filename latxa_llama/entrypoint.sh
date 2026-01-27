#!/bin/bash

MODEL_PATH="/mnt/models/Latxa-Llama-3.1-8B-Instruct.gguf"

# Descargar modelo solo si no existe
if [ ! -f "$MODEL_PATH" ]; then
    echo "Modelo no encontrado. Descargando..."
    wget -O "$MODEL_PATH" "https://huggingface.co/mradermacher/Latxa-Llama-3.1-8B-Instruct-GGUF/resolve/main/Latxa-Llama-3.1-8B-Instruct.Q4_K_M.gguf"
else
    echo "Modelo ya existe. Usando versión cacheada."
fi

# Ejecutar FastAPI (puedes comentar esto para usar CLI)
exec python3 -m uvicorn api:app --host 0.0.0.0 --port 8111
# CLI alternativo:
# exec /opt/llama.cpp/main -m "$MODEL_PATH" -ins -t 4 -n 512

FROM ubuntu:22.04

# 1. Dependencias
RUN apt-get update && apt-get install -y \
    git build-essential cmake wget python3 python3-pip \
    libcurl4-openssl-dev ninja-build \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip setuptools wheel


# 2. Clonar llama.cpp solo si no existe
RUN if [ ! -d /opt/llama.cpp ]; then \
        git clone https://github.com/ggerganov/llama.cpp /opt/llama.cpp; \
    fi

# 3. Compilar llama.cpp
RUN cd /opt/llama.cpp && mkdir -p build && cd build \
    && cmake .. \
    && cmake --build .

# 4. Crear symlink para compatibilidad
RUN ln -sf /opt/llama.cpp/build/main /opt/llama.cpp/main

# 5. Instalar Python bindings + FastAPI
RUN pip3 install --no-cache-dir llama-cpp-python fastapi pydantic
RUN pip3 install fastapi uvicorn pydantic

# 6. Directorio de modelos y trabajo
RUN mkdir -p /mnt/models
WORKDIR /app

# 7. Copiar entrypoint y API
COPY entrypoint.sh /entrypoint.sh
COPY api.py /app/api.py
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

from fastapi import FastAPI
from pydantic import BaseModel
from llama_cpp import Llama

app = FastAPI(title="Latxa-LLaMA 3.1 API", description="API para generar texto con Latxa-LLaMA GGUF")

#MODEL_PATH = "/mnt/models/Latxa-Llama-3.1-8B-Instruct.gguf"
MODEL_PATH = "/mnt/models/Latxa-Llama-3.1-8B-Instruct.Q6_K.gguf"

# Definir número de threads (equivalente a -t)
LLAMA_THREADS = 8

# Cargar el modelo con número de threads
llm = Llama(model_path=MODEL_PATH, n_threads=LLAMA_THREADS)

class Prompt(BaseModel):
    text: str
    max_tokens: int = 200  # equivalente a -n
    threads: int = None     # opcional para sobrescribir n_threads

@app.post("/generate")
def generate(prompt: Prompt):
    threads_to_use = prompt.threads if prompt.threads else LLAMA_THREADS
    # Crear una instancia temporal si se quiere cambiar threads
    if threads_to_use != LLAMA_THREADS:
        tmp_llm = Llama(model_path=MODEL_PATH, n_threads=threads_to_use)
        output = tmp_llm(prompt.text, max_tokens=prompt.max_tokens)
    else:
        output = llm(prompt.text, max_tokens=prompt.max_tokens)
    return {"text": output['choices'][0]['text']}

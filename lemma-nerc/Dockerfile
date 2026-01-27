FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git

# Install Git LFS for handling large files
RUN apt-get update && apt-get install -y git-lfs && git lfs install

# Set up Hugging Face cache directory
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers
ENV HUGGINGFACE_HUB_CACHE=/app/.cache/huggingface/hub

# Create cache directory
RUN mkdir -p /app/.cache/huggingface/transformers
RUN mkdir -p /app/.cache/huggingface/hub

# Copy requirements first to leverage Docker cache
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Download the model during build
RUN python -c "from transformers import AutoModelForTokenClassification; AutoModelForTokenClassification.from_pretrained('HiTZ/xlm-roberta-large-lemma-eu')"

EXPOSE 8010

CMD ["python", "manage.py", "runserver", "0.0.0.0:8010"]
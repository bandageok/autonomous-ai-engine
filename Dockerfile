FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install faiss for vector storage
RUN pip install --no-cache-dir faiss-cpu

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "__main__.py", "serve", "--host", "0.0.0.0", "--port", "8000"]

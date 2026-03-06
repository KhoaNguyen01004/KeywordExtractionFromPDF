# Use slim Python image to reduce build size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for opencv, easyocr, and pdf2image
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# Use --no-cache-dir to reduce image size
# Use --extra-index-url for CPU-only PyTorch
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Copy application code
COPY . .

# Expose port (Flask default)
EXPOSE 5000

# Run the application
CMD ["python", "run.py"]


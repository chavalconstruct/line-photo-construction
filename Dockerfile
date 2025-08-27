# ---- Stage 1: The Builder ----
# Use a full-featured Python image to install dependencies
FROM python:3.11 AS builder

# 1. Install uv first, which is a very fast process
RUN pip install uv

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements file to leverage Docker's layer caching
COPY requirements.txt .

# 2. Use uv to install dependencies much faster than pip
RUN uv pip install --no-cache-dir -r requirements.txt


# ---- Stage 2: The Final Image ----
FROM python:3.11-slim

# (ส่วนที่เหลือของ Stage 2 เหมือนเดิมทุกอย่าง)
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
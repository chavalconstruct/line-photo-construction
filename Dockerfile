# Dockerfile

# ---- Stage 1: The Builder ----
# (ส่วนนี้ยังคงเหมือนเดิม)
FROM python:3.11 AS builder
RUN pip install uv
WORKDIR /app
COPY requirements.txt .
RUN uv pip install --no-cache-dir -r requirements.txt --system


# ---- Stage 2: The Final Image ----
FROM python:3.11-slim

WORKDIR /app

# Copy installed dependencies from the 'builder' stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy python executables from the 'builder' stage
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application source code
COPY . .

# --- START: การแก้ไขสำหรับสถาปัตยกรรม Entrypoint ---

# 1. COPY สคริปต์ที่สร้างขึ้นใหม่เข้าไปใน image
COPY fetch_secrets.py .
COPY entrypoint.sh .

# 2. ให้สิทธิ์ในการ execute กับ entrypoint script
RUN chmod +x entrypoint.sh

# 3. ตั้งค่า ENTRYPOINT ให้ชี้ไปที่สคริปต์ของเรา
ENTRYPOINT ["./entrypoint.sh"]

# --- END: การแก้ไข ---


# Expose the port the app will run on
EXPOSE 8000

# Command to run the application using uvicorn
# คำสั่งนี้จะถูกส่งเป็น arguments ($@) ไปให้กับ entrypoint.sh
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]
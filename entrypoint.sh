#!/bin/sh

# entrypoint.sh

# 1. ป้องกันการทำงานต่อหากมีคำสั่งใดล้มเหลว
set -e

echo "Starting entrypoint script..."

# 2. เรียกใช้ Python script เพื่อดึง Secrets และนำผลลัพธ์ (stdout)
#    มาเขียนทับลงในไฟล์ .env
echo "Fetching secrets from OCI Vault and creating .env file..."
python fetch_secrets.py > .env
echo ".env file created successfully."

# 3. ใช้คำสั่ง 'exec "$@"' เพื่อรันคำสั่งหลัก (CMD) ที่ถูกส่งต่อมาจาก Dockerfile
#    ในที่นี้คือคำสั่ง 'uvicorn main:app ...'
#    การใช้ 'exec' จะทำให้ Uvicorn กลายเป็น process หลัก (PID 1) ของ container
#    ซึ่งเป็น best practice สำหรับการจัดการ signal
echo "Executing the main application command..."
exec "$@"
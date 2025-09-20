# ---- Stage 1: The Builder ----
# (This part is correct and remains the same)
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

# --- ADD THIS LINE ---
# Copy python executables from the 'builder' stage
COPY --from=builder /usr/local/bin /usr/local/bin
# --------------------

# Copy the application source code
COPY . .

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application using uvicorn
CMD ["/bin/sh", "-c", "echo $CONFIG_JSON | base64 -d > config.json && echo $CREDENTIALS_JSON | base64 -d > credentials.json && echo $TOKEN_JSON | base64 -d > token.json && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

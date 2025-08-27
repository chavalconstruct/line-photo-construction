# ---- Stage 1: The Builder ----
# Use a full-featured Python image to install dependencies
FROM python:3.11 AS builder

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements file to leverage Docker's layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


# ---- Stage 2: The Final Image ----
# Use a slim Python image for the production environment
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy installed dependencies from the 'builder' stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy the application source code
COPY . .

# Expose the port the app will run on
EXPOSE 8000

# Command to run the application using uvicorn
# This makes the server accessible from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
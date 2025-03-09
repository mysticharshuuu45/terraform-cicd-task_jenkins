# Use a lightweight Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install dependencies
RUN apt update && apt install -y git python3-pip

# Copy application files
COPY . /app

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Run the application
CMD ["python", "app.py"]

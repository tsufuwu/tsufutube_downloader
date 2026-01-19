# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# ffmpeg: for media processing
# python3-tk, tk-dev: for Tkinter GUI
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3-tk \
    tk-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Environment variable to prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "Tsufutube downloader.py"]

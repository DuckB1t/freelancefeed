# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure the database and .env are handled externally via volumes or env vars
# But we copy a default .env.example if needed
RUN cp .env.example .env

# Run the bot
CMD ["python", "main.py", "start"]

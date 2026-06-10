# Use python official slim base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Set working directory
WORKDIR /app

# Install system dependencies (required for compiling packages like bcrypt)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app/

# Create a non-privileged user to run the app for security
RUN useradd -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (application runs on port 5454)
EXPOSE 5454

# Run using Gunicorn
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5454", "app:app"]

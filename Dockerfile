# Use an official Python image as the base
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for lxml
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install required Python packages
RUN pip install --no-cache-dir beautifulsoup4 lxml python-telegram-bot pytz

# Copy your Python script into the container
COPY cmds/ /app/
COPY MensaTelegramBot.py /app/bot.py

# Specify the script to run when the container starts
CMD ["python", "/app/bot.py"]

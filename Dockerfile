FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install fonts
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Cache bust - force fresh copy of all files
ARG CACHE_BUST=1
COPY . .

# Start bot
CMD ["python", "bot.py"]

FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install fonts
RUN apt-get update && apt-get install -y \
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    && fc-cache -f -v \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright browsers explicitly
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy all bot files
ARG CACHE_BUST=3
COPY . .

# Start bot
CMD ["python", "bot.py"]

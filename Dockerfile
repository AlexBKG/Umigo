#Base image
FROM python:3.11-slim

WORKDIR /app

#System level dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

#Project setup
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#Initial variables
ENV PYTHONUNBUFFERED=1

#Entrypoint and its permissions
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
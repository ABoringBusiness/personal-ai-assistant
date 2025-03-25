#!/bin/bash

# Exit on error
set -e

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create one based on .env.example"
    echo "You can run: cp .env.example .env"
    exit 1
fi

# Build the Docker images
echo "Building Docker images..."
docker-compose build

# Create the db directory if it doesn't exist
mkdir -p db

echo "Docker images built successfully!"
echo ""
echo "To start the Telegram bot, run:"
echo "docker-compose up -d telegram-bot"
echo ""
echo "To start the WhatsApp bot, run:"
echo "docker-compose up -d whatsapp-bot"
echo ""
echo "To start both bots, run:"
echo "docker-compose up -d"
echo ""
echo "To view logs, run:"
echo "docker-compose logs -f"
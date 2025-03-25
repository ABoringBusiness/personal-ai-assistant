# Docker Setup for Personal AI Assistant

This document explains how to run the Personal AI Assistant using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/ABoringBusiness/personal-ai-assistant.git
   cd personal-ai-assistant
   ```

2. Create a `.env` file based on the `.env.example` file:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file and fill in your API keys and other required environment variables.

## Running the Application

### Using Docker Compose

You can run both the Telegram and WhatsApp bots using Docker Compose:

```bash
# Build and start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the services
docker-compose down
```

### Running Individual Services

If you want to run only one of the services:

```bash
# Run only the Telegram bot
docker-compose up -d telegram-bot

# Run only the WhatsApp bot
docker-compose up -d whatsapp-bot
```

### Using Docker Directly

You can also build and run the Docker image directly:

```bash
# Build the Docker image
docker build -t personal-ai-assistant .

# Run the Telegram bot
docker run -d --name telegram-bot --env-file .env -v $(pwd)/db:/app/db personal-ai-assistant telegram

# Run the WhatsApp bot
docker run -d --name whatsapp-bot -p 5000:5000 --env-file .env -v $(pwd)/db:/app/db personal-ai-assistant whatsapp
```

## Persistent Data

The application uses SQLite for storing data. The database files are stored in the `db` directory, which is mounted as a volume in the Docker container. This ensures that your data persists even if the container is stopped or removed.

## Environment Variables

Make sure to set all the required environment variables in the `.env` file. Refer to the `.env.example` file for a list of all the required variables.

## Troubleshooting

If you encounter any issues:

1. Check the logs:
   ```bash
   docker-compose logs -f
   ```

2. Make sure all the required environment variables are set in the `.env` file.

3. Ensure that the ports are not already in use by another application.

4. If you're using the WhatsApp bot, make sure your Twilio webhook URL is correctly configured to point to your server's public IP or domain with the correct port (5000).
# AI Personal Assistant Docker Setup

This document provides instructions for running the AI Personal Assistant service using Docker and Docker Compose.

## Prerequisites

1. [Docker](https://docs.docker.com/get-docker/)
2. [Docker Compose](https://docs.docker.com/compose/install/)
3. Required API keys and credentials (see below)

## Configuration

Before running the application, make sure you have:

1. A properly configured `.env` file with all necessary API keys and credentials. Copy `.env.example` to `.env` and fill in your credentials.
2. `credentials.json` for Google API access (required for calendar and email functionality)

### Essential Environment Variables

The following variables are essential depending on which features you want to use:

- **OpenAI and LangChain**:
  - `OPENAI_API_KEY`: Required for the AI functionality
  - `LANGCHAIN_API_KEY`: For tracing and monitoring (optional)

- **Google Integration (Calendar, Email)**:
  - Place a valid `credentials.json` file in the project root

- **Telegram Bot**:
  - `TELEGRAM_TOKEN`: Your Telegram bot token
  - `CHAT_ID`: ID of the chat where the bot will operate

- **Notion Integration**:
  - `NOTION_TOKEN`: Your Notion API token
  - `NOTION_DATABASE_ID`: ID of your Notion database

## Running the Application

### Using Helper Scripts

For convenience, helper scripts are provided for both Bash (Linux/macOS) and PowerShell (Windows) environments.

#### For Linux/macOS:

Make the script executable:
```bash
chmod +x docker-helper.sh
```

Common commands:
```bash
./docker-helper.sh start   # Start the application
./docker-helper.sh stop    # Stop the application
./docker-helper.sh logs    # View logs
./docker-helper.sh token   # Clear OAuth token (if you need to reauthenticate)
./docker-helper.sh help    # Show all available commands
```

#### For Windows:

```powershell
.\docker-helper.ps1 start   # Start the application
.\docker-helper.ps1 stop    # Stop the application
.\docker-helper.ps1 logs    # View logs
.\docker-helper.ps1 token   # Clear OAuth token (if you need to reauthenticate)
.\docker-helper.ps1 help    # Show all available commands
```

### Manual Commands

If you prefer to use Docker Compose directly:

1. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

2. Check logs to verify everything is working:
   ```bash
   docker-compose logs -f
   ```

3. To stop the application:
   ```bash
   docker-compose down
   ```

## OAuth Authentication

For the first run, Google services (Calendar, Gmail) require OAuth authentication:

1. After starting the container, watch the logs with `docker-compose logs -f`
2. When prompted, follow the OAuth URL that appears in the logs
3. Complete authentication in your browser
4. The OAuth token will be saved to the `token.json` volume for future use

## Data Persistence

The application uses volumes to persist:
- Database files: `./db:/app/db`
- OAuth tokens: `./token.json:/app/token.json`

## WhatsApp Integration (Optional)

To enable the WhatsApp API service:
1. Uncomment the `whatsapp-api` section in `docker-compose.yml`
2. Add Twilio credentials to your `.env` file:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `FROM_WHATSAPP_NUMBER`
3. Restart the containers: `docker-compose up -d`

## Troubleshooting

1. **OAuth Issues**: 
   - If you encounter OAuth errors, clear the token using the helper script:
     ```bash
     ./docker-helper.sh token   # Linux/macOS
     .\docker-helper.ps1 token  # Windows
     ```
   - Then restart the application

2. **Database Issues**: 
   - Clear the database using the helper script:
     ```bash
     ./docker-helper.sh db   # Linux/macOS
     .\docker-helper.ps1 db  # Windows
     ```

3. **Container Errors**: 
   - Check the logs:
     ```bash
     ./docker-helper.sh logs   # Linux/macOS
     .\docker-helper.ps1 logs  # Windows
     ```
   - Rebuild the application:
     ```bash
     ./docker-helper.sh rebuild   # Linux/macOS
     .\docker-helper.ps1 rebuild  # Windows
     ```

## Security Considerations

1. Your `.env` file and `credentials.json` contain sensitive information - never commit them to version control
2. The container runs with a non-root user for additional security
3. Credentials are mounted as read-only volumes where possible
4. All services use the binding to 127.0.0.1 to prevent external access 
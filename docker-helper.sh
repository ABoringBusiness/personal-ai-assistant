#!/bin/bash

# Helper script for AI Personal Assistant Docker setup

# Make the script executable
chmod +x "${0}"

# Check for required files
check_requirements() {
  echo "Checking for required files..."
  
  # Check for .env file
  if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
      echo "ERROR: .env file not found. Please copy .env.example to .env and configure your credentials."
      echo "  cp .env.example .env"
    else
      echo "ERROR: Neither .env nor .env.example found. Please create a .env file with your credentials."
    fi
    return 1
  fi
  
  # Check for credentials.json
  if [ ! -f "credentials.json" ]; then
    echo "ERROR: credentials.json not found. This file is required for Google services integration."
    echo "Please obtain credentials.json from the Google Cloud Console and place it in the project directory."
    return 1
  fi
  
  echo "All required files found."
  return 0
}

# Function to start the services
start_services() {
  echo "Starting AI Personal Assistant..."
  
  # Build and start containers
  docker-compose up -d
  
  # Show logs
  docker-compose logs -f
}

# Function to stop the services
stop_services() {
  echo "Stopping AI Personal Assistant..."
  docker-compose down
}

# Function to restart the services
restart_services() {
  echo "Restarting AI Personal Assistant..."
  docker-compose restart
  
  # Show logs
  docker-compose logs -f
}

# Function to rebuild the services
rebuild_services() {
  echo "Rebuilding AI Personal Assistant..."
  docker-compose down
  docker-compose build
  docker-compose up -d
  
  # Show logs
  docker-compose logs -f
}

# Function to clear token for reauthorization
clear_token() {
  echo "Clearing OAuth token..."
  if [ -f "token.json" ]; then
    rm token.json
    echo "token.json removed. You will need to reauthorize on next startup."
  else
    echo "token.json not found."
  fi
}

# Function to clear the database
clear_db() {
  echo "Clearing database..."
  if [ -d "db" ]; then
    rm -rf db/*
    echo "Database cleared."
  else
    echo "Database directory not found."
  fi
}

# Display usage
usage() {
  echo "Usage: $0 [command]"
  echo "Commands:"
  echo "  start    - Start the AI Personal Assistant"
  echo "  stop     - Stop the AI Personal Assistant"
  echo "  restart  - Restart the AI Personal Assistant"
  echo "  rebuild  - Rebuild and restart the AI Personal Assistant"
  echo "  logs     - Show logs"
  echo "  token    - Clear OAuth token for reauthorization"
  echo "  db       - Clear the database"
  echo "  check    - Check for required files"
  echo "  help     - Show this help message"
}

# Main script
case "$1" in
  start)
    check_requirements && start_services
    ;;
  stop)
    stop_services
    ;;
  restart)
    restart_services
    ;;
  rebuild)
    rebuild_services
    ;;
  logs)
    docker-compose logs -f
    ;;
  token)
    clear_token
    ;;
  db)
    clear_db
    ;;
  check)
    check_requirements
    ;;
  help)
    usage
    ;;
  *)
    usage
    ;;
esac 
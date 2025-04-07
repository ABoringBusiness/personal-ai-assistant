# Helper script for AI Personal Assistant Docker setup in PowerShell

# Check for required files
function Check-Requirements {
    Write-Host "Checking for required files..." -ForegroundColor Cyan
    
    # Check for .env file
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Write-Host "ERROR: .env file not found. Please copy .env.example to .env and configure your credentials." -ForegroundColor Red
            Write-Host "  Copy-Item .env.example .env" -ForegroundColor Yellow
        } else {
            Write-Host "ERROR: Neither .env nor .env.example found. Please create a .env file with your credentials." -ForegroundColor Red
        }
        return $false
    }
    
    # Check for credentials.json
    if (-not (Test-Path "credentials.json")) {
        Write-Host "ERROR: credentials.json not found. This file is required for Google services integration." -ForegroundColor Red
        Write-Host "Please obtain credentials.json from the Google Cloud Console and place it in the project directory." -ForegroundColor Yellow
        return $false
    }
    
    Write-Host "All required files found." -ForegroundColor Green
    return $true
}

# Function to start the services
function Start-Services {
    Write-Host "Starting AI Personal Assistant..." -ForegroundColor Cyan
    
    # Build and start containers
    docker-compose up -d
    
    # Show logs
    docker-compose logs -f
}

# Function to stop the services
function Stop-Services {
    Write-Host "Stopping AI Personal Assistant..." -ForegroundColor Cyan
    docker-compose down
}

# Function to restart the services
function Restart-Services {
    Write-Host "Restarting AI Personal Assistant..." -ForegroundColor Cyan
    docker-compose restart
    
    # Show logs
    docker-compose logs -f
}

# Function to rebuild the services
function Rebuild-Services {
    Write-Host "Rebuilding AI Personal Assistant..." -ForegroundColor Cyan
    docker-compose down
    docker-compose build
    docker-compose up -d
    
    # Show logs
    docker-compose logs -f
}

# Function to clear token for reauthorization
function Clear-Token {
    Write-Host "Clearing OAuth token..." -ForegroundColor Cyan
    if (Test-Path "token.json") {
        Remove-Item "token.json"
        Write-Host "token.json removed. You will need to reauthorize on next startup." -ForegroundColor Green
    } else {
        Write-Host "token.json not found." -ForegroundColor Yellow
    }
}

# Function to clear the database
function Clear-Database {
    Write-Host "Clearing database..." -ForegroundColor Cyan
    if (Test-Path "db") {
        Remove-Item "db\*" -Recurse -Force
        Write-Host "Database cleared." -ForegroundColor Green
    } else {
        Write-Host "Database directory not found." -ForegroundColor Yellow
    }
}

# Display usage
function Show-Usage {
    Write-Host "Usage: .\docker-helper.ps1 [command]" -ForegroundColor Cyan
    Write-Host "Commands:"
    Write-Host "  start    - Start the AI Personal Assistant"
    Write-Host "  stop     - Stop the AI Personal Assistant"
    Write-Host "  restart  - Restart the AI Personal Assistant"
    Write-Host "  rebuild  - Rebuild and restart the AI Personal Assistant"
    Write-Host "  logs     - Show logs"
    Write-Host "  token    - Clear OAuth token for reauthorization"
    Write-Host "  db       - Clear the database"
    Write-Host "  check    - Check for required files"
    Write-Host "  help     - Show this help message"
}

# Main script
if ($args.Count -eq 0) {
    Show-Usage
    return
}

switch ($args[0]) {
    "start" {
        if (Check-Requirements) { Start-Services }
    }
    "stop" {
        Stop-Services
    }
    "restart" {
        Restart-Services
    }
    "rebuild" {
        Rebuild-Services
    }
    "logs" {
        docker-compose logs -f
    }
    "token" {
        Clear-Token
    }
    "db" {
        Clear-Database
    }
    "check" {
        Check-Requirements
    }
    "help" {
        Show-Usage
    }
    default {
        Show-Usage
    }
} 
# PowerShell script to launch the Brave Search Knowledge Aggregator test server
param(
    [string]$EnvFile = ".env.test",
    [string]$VenvPath = "$env:DEV_ROOT\venvs\multi-llm-wrapper\Scripts\Activate.ps1"
)

# Function to load environment variables from file
function Load-EnvFile {
    param([string]$FilePath)
    
    if (Test-Path $FilePath) {
        Get-Content $FilePath | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                [Environment]::SetEnvironmentVariable($key, $value)
                Write-Host "Set environment variable: $key"
            }
        }
    }
    else {
        Write-Error "Environment file not found: $FilePath"
        exit 1
    }
}

# Function to check if port is available
function Test-PortAvailable {
    param([int]$Port)
    
    $listener = $null
    try {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, $Port)
        $listener.Start()
        return $true
    }
    catch {
        return $false
    }
    finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

# Activate virtual environment
if (Test-Path $VenvPath) {
    Write-Host "Activating virtual environment..."
    & $VenvPath
}
else {
    Write-Error "Virtual environment not found at: $VenvPath"
    exit 1
}

# Load environment variables
Write-Host "Loading test environment variables..."
Load-EnvFile $EnvFile

# Check if port 8001 is available
if (-not (Test-PortAvailable 8001)) {
    Write-Error "Port 8001 is already in use. Please ensure no other service is running on this port."
    exit 1
}

# Set test mode environment variable
$env:TEST_MODE = "true"

# Start the test server
Write-Host "Starting test server on port 8001..."
try {
    uvicorn brave_search_aggregator.test_server:app --host 0.0.0.0 --port 8001 --reload --log-level debug
}
catch {
    Write-Error "Failed to start test server: $_"
    exit 1
}
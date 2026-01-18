$pythonExe = "python3.12"

# Check Python version
$version = & $pythonExe --version
Write-Host "Using Python version: $version"

Write-Host "Creating virtual environment..."
& python3.12 -m venv venv

Write-Host "Activating virtual environment..."
& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

Write-Host "Installing project dependencies..."
# & pip install . # dla usera
& pip install .[dev] # dla developera

Write-Host "Setup is done."

# pip freeze > requirements.txt
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

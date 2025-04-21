# Windows Setup Guide for agent-app-agno

This guide provides instructions for setting up and running the agent-app-agno project on Windows systems.

## Prerequisites

* Python 3.12 or higher
* [uv](https://github.com/astral-sh/uv) package manager
* Docker Desktop or Podman

## Development Environment Setup

### 1. Create Python Development Environment

Run the Windows-specific setup script from the project root directory:

```powershell
# From Command Prompt
scripts\dev_setup.bat

# From PowerShell
.\scripts\dev_setup.bat
```

This script will:

- Create a virtual environment in `.venv`
- Install all dependencies with Windows-specific adjustments
- Remove Unix-only packages like `uvloop`
- Install the project in editable mode

Next, activate the virtual environment:

```powershell
# Command Prompt
.venv\Scripts\activate

# PowerShell
.venv\Scripts\Activate.ps1
```

### 2. Build container image locally

Build the application container locally:
```bash
docker build -t local/agent-app:dev .
```

If you are using `podman` instead of `docker`, set an alias by running:

```powershell
Set-Alias -Name docker -Value podman

# Verify the alias works
docker --version
```

### 3. Start the application

Use the agno CLI to start the application:

```bash
ag ws up
```

**What gets deployed:**
- **Streamlit UI:** [http://localhost:8501](http://localhost:8501)
- **FastAPI Backend:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Postgres Database:** localhost:5432

### 4. Stop the application

Use the agno CLI to stop the application:

```bash
ag ws down
```










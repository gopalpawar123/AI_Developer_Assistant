# AI Developer Assistant — V1.0

A Python-based AI Developer Assistant that uses local AI models through Ollama to assist developers with code analysis, automated test generation, test execution, failure analysis, and AI-assisted test repair.

## Features

- Read and analyze source code.
- Generate unit tests using AI.
- Validate generated Python tests.
- Execute tests in an isolated Docker environment.
- Analyze test failures.
- Generate AI-assisted test repairs.
- Display proposed changes before saving.
- Require user approval before saving or executing repairs.
- Maintain repair history.
- Limit automatic repair attempts.

## Technology Stack

- Python 3.12
- Ollama with a local Qwen model
- pytest
- Docker
- Python AST for static validation
- Git

## Installation

Clone the repository and navigate to the project directory.

Create and activate a Python virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Install Ollama and download the configured local AI model.

Ensure Docker Desktop is running and the project's test-runner image is available.

## Running the Assistant

```powershell
python app.py
```

Follow the interactive prompts to generate tests, execute them, inspect failures, and review proposed repairs.

## Running Automated Tests

```powershell
python -m pytest tests/ -q
```

Latest verified result during V1 preparation:

**127 passed, 1 skipped**

## AI Test Repair Workflow

1. Execute generated or existing tests.
2. Detect failing tests.
3. Analyze the failure using AI.
4. Generate a proposed repair.
5. Validate the repaired test code.
6. Display a diff between original and repaired tests.
7. Request user approval before saving.
8. Save the repaired test separately.
9. Request approval before Docker execution.
10. Execute the repaired test and report the result.

## Safety and Limitations

- AI-generated code may contain incorrect assertions or misleading test names.
- Static validation does not guarantee that tests are semantically correct.
- Users should review all proposed repairs.
- Docker execution requires a correctly configured local Docker environment.
- The assistant does not modify production code as part of the demonstrated test-repair workflow.

## Project Status

V1 core workflow has been successfully demonstrated, including an AI-generated test repair that passed all seven tests in Docker.

## Future Improvements

- Stronger semantic test validation
- More reliable AI failure analysis
- Web-based interface
- RAG-based repository understanding
- Multi-agent development workflows
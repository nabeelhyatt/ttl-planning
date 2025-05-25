# Tabletop Library Planning Tools

## Overview

This project is a Python-based web application designed to model, analyze, and optimize membership plans, capacity utilization, and revenue for a tabletop game cafe or library. It uses customer personas and physical constraints (tables, hours) to simulate demand and check against available capacity.

## Features

*   **Capacity Planning**: Models available monthly table time based on table types (4-tops, 8-tops, etc.) and operating hours.
*   **Demand Modeling**: Simulates monthly demand for table space based on defined customer personas (e.g., casual, students, families, hobbyists, everyday) and their expected visit frequency and group sizes.
*   **Capacity vs. Demand Analysis**: Uses linear programming (via PuLP) to determine if the simulated demand can be accommodated within the available capacity for a given number of members.
*   **Membership Plan Value**: Calculates the perceived value of different membership tiers (Basic, Standard, Family) based on included features and usage patterns.
*   **Plan Optimization**: Includes logic (`plan_optimizer.py`) to optimize plan pricing or features (details inferred).
*   **Persona Optimization**: Analyzes plan value from the perspective of different customer personas (`persona_optimization.py`).
*   **Revenue Planning**: Projects potential revenue based on membership plans and spending assumptions (`revenue_planner.py`).
*   **Web Interface**: Provides a basic web UI (via Flask and `templates/index.html`) to display analysis results and potentially configure parameters.

## Project Structure

```
/Users/nabeelhyatt/Library/Mobile Documents/com~apple~CloudDocs/Tabletop Library/ttl-planning
├── api/
│   └── index.py           # Simplified Flask app (likely for serverless deployment, e.g., Vercel)
├── templates/
│   └── index.html         # Main HTML frontend template (contains UI and likely JavaScript logic)
├── venv/                  # Python virtual environment (ignored by git)
├── app.py                 # Main Flask application (intended for local development, runs on port 3001)
├── planner.py             # Core logic: capacity, demand, personas, value constants, PuLP modeling
├── plan_optimizer.py      # Logic for optimizing membership plans based on value
├── persona_optimization.py # Logic for analyzing plan suitability per persona
├── revenue_planner.py     # Logic for calculating revenue projections
├── value_calculator.py    # Calculates the perceived value of plans for specific personas
├── requirements.txt       # Python package dependencies
├── journey.md             # Log of development sprints, tasks, and todos
├── work-log.md            # Detailed log of code changes per session
├── README.md              # This file
├── OBG_Members_Processed.csv # Processed member data (output of utility script)
├── process_members.py     # Utility script: Parses 'OBG Members.txt' into CSV
├── analyze_frequencies.py # Utility script: Analyzes visit frequency data from CSV
└── test_planner.py        # Utility script: Basic tests for planner.py's demand calculation
```

*Note: Utility scripts (`process_members.py`, `analyze_frequencies.py`, `test_planner.py`) are for data preparation and development testing, not part of the core web application runtime. The persona definitions in `planner.py` may have been informed by analyzing data processed by these scripts (e.g., from an original `OBG Members.txt` file, not included in repo).* 

## Key Technologies

*   **Backend**: Python
*   **Web Framework**: Flask
*   **Optimization**: PuLP (Linear Programming) - *Note: Uses the default bundled CBC solver. Other solvers might be installable via system packages if needed.*
*   **API Handling**: Flask-CORS
*   **Frontend**: HTML - *Note: Interactive logic is likely implemented using JavaScript within `templates/index.html`.*

## Setup and Running Locally

1.  **Prerequisites**:
    *   Python 3.x
    *   pip (Python package installer)

2.  **Clone the repository** (if not already done).

3.  **Create and activate a Python virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate  # On Windows
    ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the development server**:
    ```bash
    python app.py
    ```

6.  Access the application in your web browser at [http://localhost:3001](http://localhost:3001).

## Deployment

### Local Development

For local development, use the standard Flask development server:

```bash
# Using uv (recommended)
uv run python app.py

# Or with traditional venv
source venv/bin/activate
python app.py
```

The application will be available at `http://localhost:3001`.

### Production Deployment (Zeabur)

This application is deployed on [Zeabur](https://zeabur.com), a cloud platform that supports direct Python deployment without Docker containers.

#### Deployment Configuration

1. **Procfile**: The `Procfile` defines how Zeabur should start the application:
   ```
   web: gunicorn app:app --bind 0.0.0.0:$PORT
   ```
   - Uses Gunicorn as the production WSGI server
   - Binds to the `$PORT` environment variable provided by Zeabur
   - Points to the `app` variable in `app.py`

2. **Requirements**: Dependencies are managed via `requirements.txt` for Zeabur compatibility:
   ```
   flask==3.0.0
   flask-cors==4.0.0
   pulp==2.7.0
   gunicorn==21.2.0
   pandas==2.1.4
   numpy==1.26.3
   python-dotenv==1.0.0
   ```

3. **Package Management**: While we use `uv` locally for development, `requirements.txt` is maintained for deployment compatibility.

#### Important Deployment Considerations

**⚠️ Never Use Hardcoded URLs in Frontend Code**

The frontend JavaScript must work in both local development and production environments. Always use relative URLs for API requests:

```javascript
// ✅ CORRECT - Works in both local and production
fetch('/api/config')

// ❌ WRONG - Only works locally
fetch('http://localhost:3001/api/config')
```

**Authentication Handling**

The `/api/config` endpoint requires HTTP Basic Authentication. The frontend uses the `authenticatedFetch()` helper function that:
- Adds proper Authorization headers
- Uses relative URLs for cross-environment compatibility
- Includes credentials for CORS requests

**Environment-Agnostic Design**

- All API endpoints use relative paths (`/api/...`)
- No hardcoded localhost references in production code
- Port binding uses environment variables (`$PORT` in Procfile)
- CORS configuration supports both local and production origins

#### Deployment Process

1. **Push to GitHub**: All changes must be committed and pushed to the main branch
2. **Automatic Deployment**: Zeabur automatically detects changes and redeploys
3. **Build Process**: Zeabur installs dependencies from `requirements.txt` and starts the app using the Procfile
4. **Health Check**: Verify the application starts correctly by checking runtime logs

#### Troubleshooting Deployment Issues

Common issues and solutions:

- **"Hello from ttl-planning!" loops**: Remove any test files (like `main.py`) that might be detected as the main entrypoint
- **Empty Setup page fields**: Check that API requests use relative URLs, not hardcoded localhost
- **Authentication errors**: Verify the `authenticatedFetch()` function includes proper headers
- **Port binding errors**: Ensure the Procfile uses `$PORT` environment variable

#### Monitoring

- **Runtime Logs**: Available in Zeabur dashboard for debugging
- **Build Logs**: Show dependency installation and startup process
- **Health Status**: Monitor application availability and response times

## Configuration

Key operational parameters and model assumptions (e.g., table counts, operating hours, plan prices, persona behavior, value calculations) are primarily defined as constants directly within `planner.py` and `value_calculator.py`. Modifying the core model often requires editing these files.

The `app.py` file includes an `/api/config` endpoint, which currently requires basic authentication (credentials hardcoded in `app.py` - **suitable for development only**), to potentially expose *some* configuration values, but it doesn't override the core constants embedded in the modules.

**Important:** Only the `/api/config` endpoint requires authentication. Other API endpoints like `/api/planner`, `/api/optimizer`, `/api/personas`, `/api/revenue`, and `/api/constants` do **not** require authentication.

**Note on CORS and Authentication:** When using Flask-CORS with authenticated routes (like `/api/config`), the `@cross_origin(supports_credentials=True)` decorator must be placed *before* the `@requires_auth` decorator in `app.py`. This ensures the CORS preflight (`OPTIONS`) request is handled correctly before the authentication check occurs.

## Model Assumptions

The planning and optimization logic relies on specific assumptions and heuristics defined within the Python modules (`planner.py`, `value_calculator.py`, `revenue_planner.py`, etc.). These include how customer value is calculated, how personas are expected to behave, and how revenue sources are estimated. Understanding these embedded assumptions is key to interpreting the model's output.

## Documentation Files

*   `journey.md`: Tracks high-level progress, sprints, and future plans, update when asked.
*   `work-log.md`: Provides a structured log of changes made during development sessions, update frequently.
*   'readme.md': project description and guidance

# Maintaining a project

- Create and maintain a readme.md file and describes the entire project, it's file structure, and features of the project. If I say "remember" then record a summary of the thing I tell you to remember in the readme.md file. Refer to the readme.md file for guidance. Maintain the Documentation Files on a regular basis and refer o them often.

# Writing code

- We prefer simple, clean, maintainable solutions over clever or complex ones, even if the latter are more concise or performant. Readability and maintainability are primary concerns.
- Make the smallest reasonable changes to get to the desired outcome. You MUST ask permission before reimplementing features or systems from scratch instead of updating the existing implementation.
- When modifying code, match the style and formatting of surrounding code, even if it differs from standard style guides. Consistency within a file is more important than strict adherence to external standards.
- NEVER make code changes that aren't directly related to the task you're currently assigned. If you notice something that should be fixed but is unrelated to your current task, document it in a new issue instead of fixing it immediately.
- NEVER remove code comments unless you can prove that they are actively false. Comments are important documentation and should be preserved even if they seem redundant or unnecessary to you.
- All code files should start with a brief 2 line comment explaining what the file does. Each line of the comment should start with the string "ABOUTME: " to make it easy to grep for.
- When writing comments, avoid referring to temporal context about refactors or recent changes. Comments should be evergreen and describe the code as it is, not how it evolved or was recently changed.
- NEVER implement a mock mode for testing or for any purpose. We always use real data and real APIs, never mock implementations.
- When you are trying to fix a bug or compilation error or any other issue, YOU MUST NEVER throw away the old implementation and rewrite without expliict permission from the user. If you are going to do this, YOU MUST STOP and get explicit permission from the user.
- NEVER name things as 'improved' or 'new' or 'enhanced', etc. Code naming should be evergreen. What is new today will be "old" someday.

# Getting help

- ALWAYS ask for clarification rather than making assumptions.
- If you're having trouble with something, it's ok to stop and ask for help. Especially if it's something your human might be better at.

# Testing

- Tests MUST cover the functionality being implemented.
- NEVER ignore the output of the system or the tests - Logs and messages often contain CRITICAL information.
- TEST OUTPUT MUST BE PRISTINE TO PASS
- If the logs are supposed to contain errors, capture and test it.
- NO EXCEPTIONS POLICY: Under no circumstances should you mark any test type as "not applicable". Every project, regardless of size or complexity, MUST have unit tests, integration tests, AND end-to-end tests. If you believe a test type doesn't apply, you need the human to say exactly "I AUTHORIZE YOU TO SKIP WRITING TESTS THIS TIME"

## We practice TDD. That means:

- Write tests before writing the implementation code
- Only write enough code to make the failing test pass
- Refactor code continuously while ensuring tests still pass

### TDD Implementation Process

- Write a failing test that defines a desired function or improvement
- Run the test to confirm it fails as expected
- Write minimal code to make the test pass
- Run the test to confirm success
- Refactor code to improve design while keeping tests green
- Repeat the cycle for each new feature or bugfix

# Specific Technologies

## Python

- I prefer to use uv for everything (uv add, uv run, etc)
- Do not use old fashioned methods for package management like poetry, pip or easy_install.
- Make sure that there is a pyproject.toml file in the root directory.
- If there isn't a pyproject.toml file, create one using uv by running uv init.
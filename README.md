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

## Configuration

Key operational parameters and model assumptions (e.g., table counts, operating hours, plan prices, persona behavior, value calculations) are primarily defined as constants directly within `planner.py` and `value_calculator.py`. Modifying the core model often requires editing these files.

The `app.py` file includes an `/api/config` endpoint, which currently requires basic authentication (credentials hardcoded in `app.py` - **suitable for development only**), to potentially expose *some* configuration values, but it doesn't override the core constants embedded in the modules.

**Important:** Only the `/api/config` endpoint requires authentication. Other API endpoints like `/api/planner`, `/api/optimizer`, `/api/personas`, `/api/revenue`, and `/api/constants` do **not** require authentication.

**Note on CORS and Authentication:** When using Flask-CORS with authenticated routes (like `/api/config`), the `@cross_origin(supports_credentials=True)` decorator must be placed *before* the `@requires_auth` decorator in `app.py`. This ensures the CORS preflight (`OPTIONS`) request is handled correctly before the authentication check occurs.

## Model Assumptions

The planning and optimization logic relies on specific assumptions and heuristics defined within the Python modules (`planner.py`, `value_calculator.py`, `revenue_planner.py`, etc.). These include how customer value is calculated, how personas are expected to behave, and how revenue sources are estimated. Understanding these embedded assumptions is key to interpreting the model's output.

## Documentation Files

*   `journey.md`: Tracks high-level progress, sprints, and future plans.
*   `work-log.md`: Provides a structured log of changes made during development sessions.

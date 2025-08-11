# ABOUTME: Main Flask application for local development
# ABOUTME: Provides API endpoints for configuration management and planning tools

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS, cross_origin
import os
import json
import planner
import plan_optimizer
import persona_optimization
import revenue_planner
from expenses import ExpenseCalculator
from financial_dashboard import FinancialDashboard
from functools import wraps

# Set up Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)

# Define config file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# Basic auth decorator
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def check_auth(username, password):
    """Check if username/password combination is valid."""
    return username == 'admin' and password == 'admin'  # For development only

def authenticate():
    """Send a 401 response that enables basic auth."""
    return ('Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})

# Load initial config from file
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            print(f"Loading configuration from {CONFIG_FILE}")
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {CONFIG_FILE} not found. Attempting to use defaults from planner.py.")
        # Fallback to planner constants if file doesn't exist
        try:
            return {
                'distribution': planner.PERSONA_DISTRIBUTION,
                'personas': planner.PERSONAS,
                'spending_assumptions': getattr(planner, 'SPENDING', { # Use getattr for safety
                    'retail_annual': {
                        'casual': 0, 'students': 60, 'families': 120,
                        'hobbyists': 180, 'everyday': 180
                    },
                    'snacks': {
                        'casual': 10, 'students': 5, 'families': 7,
                        'hobbyists': 4, 'everyday': 4
                    }
                }),
                'plan_prices': {
                    'visitor_plan_price': float(planner.VISITOR_PLAN_PRICE),
                    'student_plan_price': float(planner.STUDENT_PLAN_PRICE),
                    'member_plan_price': float(planner.MEMBER_PLAN_PRICE),
                    'council_plan_price': float(planner.COUNCIL_PLAN_PRICE)
                },
                'plans': {
                    'visitor': {'features': planner.get_plan_features('visitor')},
                    'student': {'features': planner.get_plan_features('student')},
                    'member': {'features': planner.get_plan_features('member')},
                    'council': {'features': planner.get_plan_features('council')}
                }
            }
        except AttributeError as e:
            print(f"Error accessing planner.py defaults: {e}. Returning empty config.")
            return {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {CONFIG_FILE}. Check file format. Returning empty config.")
        return {} # Or raise an exception

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
@cross_origin(supports_credentials=True)
def get_config():
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
@cross_origin(supports_credentials=True)
def save_config():
    try:
        config = request.get_json()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/planner')
def get_planner():
    try:
        # Get member count from query params, default to 300
        member_count = int(request.args.get('members', 300))
        
        # Check if we can accommodate this many members
        can_accommodate, details = planner.can_accommodate(member_count)
        
        return jsonify({
            "can_accommodate": can_accommodate,
            "details": details
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/optimizer')
def get_optimizer():
    try:
        optimizer = plan_optimizer.PlanOptimizer()
        results = optimizer.optimize_pricing()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/personas')
def get_personas():
    try:
        optimizer = persona_optimization.PersonaOptimizer()
        results = optimizer.optimize_personas()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/revenue')
def get_revenue():
    try:
        planner = revenue_planner.RevenuePlanner()
        results = planner.calculate_annual_revenue()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/constants')
def get_constants():
    constants = {
        'GUEST_PRICE': float(planner.GUEST_PRICE),
        'BASE_VISIT_VALUE': float(planner.BASE_VISIT_VALUE),
        'EVENT_VALUE': float(planner.MIXED_VALUE),
        'GAME_CHECKOUT_VALUE': float(planner.GAME_CHECKOUT_VALUE),
        'BASE_VALUE_CAP': float(planner.BASE_VALUE_CAP),
        'VISITOR_PLAN_PRICE': float(planner.VISITOR_PLAN_PRICE),
        'STUDENT_PLAN_PRICE': float(planner.STUDENT_PLAN_PRICE),
        'MEMBER_PLAN_PRICE': float(planner.MEMBER_PLAN_PRICE),
        'COUNCIL_PLAN_PRICE': float(planner.COUNCIL_PLAN_PRICE),
    }
    return jsonify(constants)

@app.route('/api/expenses')
def get_expenses():
    try:
        calculator = ExpenseCalculator()
        monthly = calculator.calculate_monthly_expenses()
        annual = calculator.calculate_annual_expenses()
        percentages = calculator.get_expense_breakdown_percentages()
        
        return jsonify({
            'monthly': monthly,
            'annual': annual,
            'percentages': percentages
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/financial-summary')
def get_financial_summary():
    try:
        # Get member count from query params or use default
        member_count = int(request.args.get('members', 200))
        
        dashboard = FinancialDashboard()
        metrics = dashboard.generate_summary_metrics(member_count)
        
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/break-even')
def get_break_even():
    try:
        dashboard = FinancialDashboard()
        break_even = dashboard.calculate_break_even()
        
        return jsonify(break_even)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=3002, debug=True)

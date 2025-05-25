# ABOUTME: Simplified Flask application for serverless deployment (e.g., Vercel)
# ABOUTME: Provides core API endpoints with authentication for configuration management

from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_cors import CORS, cross_origin
import os
import sys
import io
import json
import math
from contextlib import redirect_stdout
from functools import wraps

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import planner
import plan_optimizer
import persona_optimization
import revenue_planner

# Set up Flask app with correct template folder
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
app = Flask(__name__, template_folder=template_dir)
CORS(app, supports_credentials=True)

# Define config file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')

# Load initial config from file
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback to planner constants if file doesn't exist
        return {
            'distribution': planner.PERSONA_DISTRIBUTION,
            'personas': planner.PERSONAS,
            'spending_assumptions': planner.SPENDING,
            'plan_prices': {
                'basic_plan_price': float(planner.BASIC_PLAN_PRICE),
                'standard_plan_price': float(planner.STANDARD_PLAN_PRICE),
                'family_plan_price': float(planner.FAMILY_PLAN_PRICE)
            },
            'plans': {
                'basic': {'features': planner.get_plan_features('basic')},
                'standard': {'features': planner.get_plan_features('standard')},
                'family': {'features': planner.get_plan_features('family')}
            }
        }

# Global variable to hold the current configuration
current_config = load_config()

def check_auth(username, password):
    """Validate credentials"""
    return username == 'user' and password == '0a82f59436f2ccda6420b060c7eecffe'

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def capture_output(func, *args, **kwargs):
    """Capture stdout from a function call"""
    output = io.StringIO()
    with redirect_stdout(output):
        func(*args, **kwargs)
    return output.getvalue()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/planner')
def get_planner_data():
    # Create a planner instance and run analysis
    test_members = [200, 250, 300, 350, 400]
    results = []
    for M in test_members:
        if planner.can_accommodate(M)[0]:
            results.append((M, True))
        else:
            results.append((M, False))
    
    # Get summary and convert newlines to HTML breaks
    summary = planner.generate_summary(test_members, results)
    summary = summary.replace('\n', '<br>')
    
    # Get detailed analysis
    detailed_output = capture_output(planner.analyze_capacity)
    
    return jsonify({
        "summary": summary,
        "detailed_output": detailed_output
    })

@app.route('/api/optimizer')
def get_optimizer_data():
    # Create an optimizer instance and run optimization
    optimizer = plan_optimizer.PlanOptimizer()
    optimized_plans = optimizer.optimize_pricing()
    
    # Generate summary
    summary = []
    summary.append(" Plan Optimization Overview")
    summary.append("")
    
    # Find best value plans for each persona
    best_plans = {}
    for plan in optimized_plans:
        for persona, ratio in plan['value_ratios'].items():
            if persona not in best_plans or ratio > best_plans[persona][1]:
                best_plans[persona] = (plan['plan_type'], ratio)
    
    # Add key insights
    total_features = sum(len(plan['features']) for plan in optimized_plans)
    avg_features = total_features / len(optimized_plans)
    summary.append(f"• Average Features per Plan: {avg_features:.1f}")
    summary.append(f"• Total Unique Features: {total_features}")
    summary.append("")
    summary.append("Best Plan by Persona:")
    for persona, (plan, ratio) in best_plans.items():
        summary.append(f"• {persona.title()}: {plan.title()} Plan ({ratio:.1f}x value)")
    
    # Get detailed analysis
    output = capture_output(optimizer.print_optimization_results)
    
    return jsonify({
        "summary": "\n".join(summary),
        "output": output
    })

@app.route('/api/personas')
def get_personas_data():
    # Create a persona optimizer instance and run optimization
    optimizer = persona_optimization.PersonaOptimizer()
    optimized_personas = optimizer.optimize_personas()
    
    # Generate summary
    summary = []
    summary.append(" Persona Value Analysis")
    summary.append("")
    
    # Calculate average value ratios and find best plans
    total_value = 0
    count = 0
    best_value_persona = None
    best_value_ratio = 0
    
    for persona in optimized_personas:
        avg_ratio = sum(persona['value_ratios'].values()) / len(persona['value_ratios'])
        total_value += avg_ratio
        count += 1
        if avg_ratio > best_value_ratio:
            best_value_ratio = avg_ratio
            best_value_persona = persona['persona_type']
    
    avg_value = total_value / count
    summary.append(f"• Average Value Ratio: {avg_value:.1f}x")
    summary.append(f"• Best Value Persona: {best_value_persona.title()} ({best_value_ratio:.1f}x)")
    summary.append("")
    summary.append("Plan Matches:")
    for persona in optimized_personas:
        if persona['best_plans']:
            summary.append(f"• {persona['persona_type'].title()}: {', '.join(p.title() for p in persona['best_plans'])}")
    
    # Get detailed analysis
    output = capture_output(optimizer.print_optimization_results)
    
    return jsonify({
        "summary": "\n".join(summary),
        "output": output
    })

@app.route('/api/revenue')
def get_revenue_data():
    """Get revenue projections"""
    rp = revenue_planner.RevenuePlanner()
    revenue_data = rp.calculate_monthly_revenue()
    return jsonify(revenue_data)

@app.route('/api/config', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
@requires_auth
def handle_config():
    global current_config
    if request.method == 'POST':
        try:
            new_config_data = request.get_json()
            if not new_config_data:
                return jsonify({"error": "No JSON data received"}), 400

            # Basic validation: check if distribution sums near 1
            if 'distribution' in new_config_data:
                dist_sum = sum(new_config_data['distribution'].values())
                if not math.isclose(dist_sum, 1.0, abs_tol=0.01):
                    return jsonify({"error": "Distribution percentages must sum to 100%"}), 400

            # Update the in-memory config
            current_config.update(new_config_data)

            # Write updated config back to file
            try:
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(current_config, f, indent=2)
                return jsonify({"message": "Config updated successfully"})
            except IOError as e:
                return jsonify({"error": "Failed to write config file"}), 500

        except Exception as e:
            return jsonify({"error": "Internal server error processing config update"}), 500

    elif request.method == 'GET':
        # Return the current in-memory configuration
        return jsonify(current_config)

@app.route('/api/constants')
def get_constants():
    constants = {
        'GUEST_PRICE': float(planner.GUEST_PRICE),
        'BASE_VISIT_VALUE': float(planner.BASE_VISIT_VALUE),
        'EVENT_VALUE': float(planner.MIXED_VALUE),  # Use MIXED_VALUE instead of EVENT_VALUE
        'GAME_CHECKOUT_VALUE': float(planner.GAME_CHECKOUT_VALUE),
        'BASE_VALUE_CAP': float(planner.BASE_VALUE_CAP),
        'BASIC_PLAN_PRICE': float(planner.BASIC_PLAN_PRICE),
        'STANDARD_PLAN_PRICE': float(planner.STANDARD_PLAN_PRICE),
        'FAMILY_PLAN_PRICE': float(planner.FAMILY_PLAN_PRICE),
    }
    return jsonify(constants)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3001)

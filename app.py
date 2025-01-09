from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import planner
import plan_optimizer
import persona_optimization
import revenue_planner
import os
import io
import sys
import importlib
from contextlib import redirect_stdout
from functools import wraps

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)
CORS(app, supports_credentials=True)

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

@app.route('/api/constants')
def get_constants():
    constants = {
        'GUEST_PRICE': float(planner.GUEST_PRICE),
        'BASE_VISIT_VALUE': float(planner.BASE_VISIT_VALUE),
        'EVENT_VALUE': float(planner.MIXED_VALUE),
        'GAME_CHECKOUT_VALUE': float(planner.GAME_CHECKOUT_VALUE),
        'BASE_VALUE_CAP': float(planner.BASE_VALUE_CAP),
        'BASIC_PLAN_PRICE': float(planner.BASIC_PLAN_PRICE),
        'STANDARD_PLAN_PRICE': float(planner.STANDARD_PLAN_PRICE),
        'FAMILY_PLAN_PRICE': float(planner.FAMILY_PLAN_PRICE),
    }
    return jsonify(constants)

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

@app.route('/api/config')
@requires_auth
def get_config():
    """Get all configurable constants"""
    print("Config requested, current distribution:", planner.PERSONA_DISTRIBUTION)
    config = {
        'distribution': planner.PERSONA_DISTRIBUTION,
        'personas': planner.PERSONAS,
        'spending_assumptions': getattr(planner, 'SPENDING', {
            'retail_monthly': {
                'casual': 0, 'students': 5, 'families': 10,
                'hobbyists': 15, 'everyday': 15
            },
            'snacks': {
                'casual': 10, 'students': 5, 'families': 7,
                'hobbyists': 4, 'everyday': 4
            }
        }),
        'plan_prices': {
            'basic_plan_price': float(planner.BASIC_PLAN_PRICE),
            'standard_plan_price': float(planner.STANDARD_PLAN_PRICE),
            'family_plan_price': float(planner.FAMILY_PLAN_PRICE)
        },
        'plans': {
            'basic': {
                'features': planner.get_plan_features('basic')
            },
            'standard': {
                'features': planner.get_plan_features('standard')
            },
            'family': {
                'features': planner.get_plan_features('family')
            }
        }
    }
    return jsonify(config)

@app.route('/api/revenue')
def get_revenue_data():
    """Get revenue projections"""
    rp = revenue_planner.RevenuePlanner()
    revenue_data = rp.calculate_monthly_revenue()
    return jsonify(revenue_data)

def update_planner_file(updates):
    """Update the planner.py file with new values"""
    planner_path = os.path.join(os.path.dirname(__file__), 'planner.py')
    with open(planner_path, 'r') as f:
        lines = f.readlines()
    
    # Update distribution
    if 'distribution' in updates:
        for i, line in enumerate(lines):
            if 'PERSONA_DISTRIBUTION = {' in line:
                # Find the end of the dictionary
                end_idx = i + 1
                while end_idx < len(lines) and '}' not in lines[end_idx]:
                    end_idx += 1
                
                # Create new distribution lines
                new_lines = ['PERSONA_DISTRIBUTION = {\n']
                for persona, value in updates['distribution'].items():
                    new_lines.append(f"    '{persona}': {value},\n")
                new_lines.append('}\n')
                
                # Replace old lines with new ones
                lines[i:end_idx+1] = new_lines
    
    # Update personas
    if 'personas' in updates:
        for i, line in enumerate(lines):
            if 'PERSONAS = {' in line:
                # Find the end of the dictionary
                end_idx = i + 1
                while end_idx < len(lines) and '}' not in lines[end_idx]:
                    end_idx += 1
                
                # Create new persona lines
                new_lines = ['PERSONAS = {\n']
                for persona, data in updates['personas'].items():
                    new_lines.append(f"    '{persona}': {{\n")
                    for key, value in data.items():
                        new_lines.append(f"        '{key}': {value},\n")
                    new_lines.append('    },\n')
                new_lines.append('}\n')
                
                # Replace old lines with new ones
                lines[i:end_idx+1] = new_lines
    
    # Write changes back to file
    with open(planner_path, 'w') as f:
        f.writelines(lines)

@app.route('/api/config', methods=['POST'])
@requires_auth
def update_config():
    """Update configurable constants"""
    updates = request.get_json()
    
    # Basic validation
    if not isinstance(updates, dict):
        return jsonify({"error": "Invalid request format"}), 400
    
    # Validate distribution
    if 'distribution' in updates:
        if not isinstance(updates['distribution'], dict):
            return jsonify({"error": "Invalid distribution format"}), 400
        if not all(isinstance(v, (int, float)) for v in updates['distribution'].values()):
            return jsonify({"error": "Distribution values must be numbers"}), 400
        if abs(sum(updates['distribution'].values()) - 1.0) > 0.01:
            return jsonify({"error": "Distribution must sum to 1"}), 400
    
    # Validate personas
    if 'personas' in updates:
        if not isinstance(updates['personas'], dict):
            return jsonify({"error": "Invalid personas format"}), 400
        for persona_data in updates['personas'].values():
            if not isinstance(persona_data, dict):
                return jsonify({"error": "Invalid persona data format"}), 400
            if not all(isinstance(v, (int, float)) for v in persona_data.values()):
                return jsonify({"error": "Persona values must be numbers"}), 400
    
    # Debug logging before update
    print("Current distribution before update:", planner.PERSONA_DISTRIBUTION)
    print("Config update requested with:", updates)
    
    # Update the planner file
    update_planner_file(updates)
    
    # Debug logging after file update
    with open(os.path.join(os.path.dirname(__file__), 'planner.py'), 'r') as f:
        print("Current PERSONA_DISTRIBUTION in file:", [line.strip() for line in f if 'PERSONA_DISTRIBUTION' in line])
    
    # Reload the planner module to pick up new changes
    importlib.reload(planner)
    print("planner.py reloaded, new distribution:", planner.PERSONA_DISTRIBUTION)
    
    print("Config update successful, distribution is now:", planner.PERSONA_DISTRIBUTION)
    return jsonify({"message": "Config updated successfully"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import planner
import plan_optimizer
import persona_optimization
import os
import io
import sys
from contextlib import redirect_stdout

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)
CORS(app)

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
    output = capture_output(planner.analyze_capacity)
    return jsonify({"output": output})

@app.route('/api/optimizer')
def get_optimizer_data():
    # Create an optimizer instance and run optimization
    optimizer = plan_optimizer.PlanOptimizer()
    output = capture_output(optimizer.print_optimization_results)
    return jsonify({"output": output})

@app.route('/api/personas')
def get_persona_data():
    # Create a persona optimizer instance and run optimization
    optimizer = persona_optimization.PersonaOptimizer()
    output = capture_output(optimizer.print_optimization_results)
    return jsonify({"output": output})

@app.route('/api/config')
def get_config():
    """Get all configurable constants"""
    config = {
        'capacity_settings': {
            'num_4_top': planner.NUM_4_TOP,
            'num_8_top': planner.NUM_8_TOP,
            'num_6_top': planner.NUM_6_TOP,
            'num_2_top': planner.NUM_2_TOP,
            'mixed_value': planner.MIXED_VALUE
        },
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
    
    # Update capacity settings
    if 'capacity_settings' in updates:
        settings = updates['capacity_settings']
        
        # Update table capacities
        if 'num_4_top' in settings:
            for i, line in enumerate(lines):
                if line.strip().startswith('NUM_4_TOP ='):
                    lines[i] = f"NUM_4_TOP = {settings['num_4_top']}\n"
        
        if 'num_8_top' in settings:
            for i, line in enumerate(lines):
                if line.strip().startswith('NUM_8_TOP ='):
                    lines[i] = f"NUM_8_TOP = {settings['num_8_top']}\n"
        
        if 'num_6_top' in settings:
            for i, line in enumerate(lines):
                if line.strip().startswith('NUM_6_TOP ='):
                    lines[i] = f"NUM_6_TOP = {settings['num_6_top']}\n"
        
        if 'num_2_top' in settings:
            for i, line in enumerate(lines):
                if line.strip().startswith('NUM_2_TOP ='):
                    lines[i] = f"NUM_2_TOP = {settings['num_2_top']}\n"
        
        # Update mixed value
        if 'mixed_value' in settings:
            for i, line in enumerate(lines):
                if line.strip().startswith('MIXED_VALUE ='):
                    lines[i] = f"MIXED_VALUE = {settings['mixed_value']}\n"

    # Write changes back to file
    with open(planner_path, 'w') as f:
        f.writelines(lines)

@app.route('/api/config', methods=['POST'])
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
    
    # Validate capacity settings
    if 'capacity_settings' in updates:
        settings = updates['capacity_settings']
        if not isinstance(settings, dict):
            return jsonify({"error": "Invalid capacity settings format"}), 400
        
        # Validate table capacities are positive integers
        for key in ['num_4_top', 'num_8_top', 'num_6_top', 'num_2_top']:
            if key in settings:
                if not isinstance(settings[key], (int, float)) or settings[key] < 0:
                    return jsonify({"error": f"{key} must be a non-negative number"}), 400
                settings[key] = int(settings[key])  # Convert to integer
        
        # Validate mixed value is a positive number
        if 'mixed_value' in settings:
            if not isinstance(settings['mixed_value'], (int, float)) or settings['mixed_value'] < 0:
                return jsonify({"error": "mixed_value must be a non-negative number"}), 400
    
    # Update the planner file
    update_planner_file(updates)
    
    return jsonify({"message": "Config updated successfully"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)

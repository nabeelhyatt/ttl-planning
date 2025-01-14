from flask import Flask, render_template, jsonify, send_from_directory
import os
import sys

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import planner
import plan_optimizer
import persona_optimization

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists("templates/" + path):
        return send_from_directory('templates', path)
    return render_template('index.html')

@app.route('/api/run_optimizer')
def run_optimizer():
    optimizer = plan_optimizer.PlanOptimizer()
    optimized_plans = optimizer.optimize_pricing()
    return jsonify(optimized_plans)

@app.route('/api/get_constants')
def get_constants():
    constants = {
        'GUEST_PRICE': planner.GUEST_PRICE,
        'BASE_VISIT_VALUE': planner.BASE_VISIT_VALUE,
        'EVENT_VALUE': planner.EVENT_VALUE,
        'GAME_CHECKOUT_VALUE': planner.GAME_CHECKOUT_VALUE,
        'BASE_VALUE_CAP': planner.BASE_VALUE_CAP,
        'BASIC_PLAN_PRICE': planner.BASIC_PLAN_PRICE,
        'STANDARD_PLAN_PRICE': planner.STANDARD_PLAN_PRICE,
        'FAMILY_PLAN_PRICE': planner.FAMILY_PLAN_PRICE,
    }
    return jsonify(constants)

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
        return jsonify({"status": "success", "message": "Config updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/planner')
def get_planner():
    try:
        # Get member count from query params, default to 300
        member_count = int(request.args.get('members', 300))
        
        # Check if we can accommodate this many members
        can_accommodate, details = planner.can_accommodate(member_count)
        
        if can_accommodate and details:
            # Format summary for frontend
            summary = f"✅ Capacity Analysis for {member_count} Members\n\n"
            summary += f"• Can accommodate: {'Yes' if can_accommodate else 'No'}\n"
            summary += f"• 4-top utilization: {details['utilization']['4_top']:.1f}%\n"
            summary += f"• 6-top utilization: {details['utilization']['6_top']:.1f}%\n"
            summary += f"• 8-top utilization: {details['utilization']['8_top']:.1f}%\n"
            summary += f"• 2-top utilization: {details['utilization']['2_top']:.1f}%\n\n"
            
            # Add demand summary
            demands = details['demands']
            summary += f"Monthly Demands:\n"
            summary += f"• Reserved 4-tops: {demands['reserved_4_blocks']:.0f} blocks\n"
            summary += f"• Reserved 6-tops: {demands['reserved_6_blocks']:.0f} blocks\n"
            summary += f"• Reserved 8-tops: {demands['reserved_8_blocks']:.0f} blocks\n"
            summary += f"• Mixed seating: {demands['mixed_seat_blocks']:.0f} seat blocks"
            
            # Format detailed output
            output = f"Detailed Capacity Analysis for {member_count} Members\n"
            output += "=" * 50 + "\n\n"
            output += "Table Allocation:\n"
            output += f"4-top tables: {details['tables']['reserved_4_full']:.0f} full, {details['tables']['reserved_4_split']:.0f} split\n"
            output += f"6-top tables: {details['tables']['reserved_6_full']:.0f} full, {details['tables']['reserved_6_split_3x2']:.0f} split 3x2, {details['tables']['reserved_6_split_4_2']:.0f} split 4+2\n"
            output += f"8-top tables: {details['tables']['reserved_8_full']:.0f} full, {details['tables']['reserved_8_split']:.0f} split\n"
            output += f"2-top tables: {details['tables']['reserved_2']:.0f} reserved, {details['tables']['mixed_2']:.0f} mixed\n\n"
            
            output += "Mixed Seating Allocation:\n"
            output += f"4-top mixed: {details['tables']['mixed_4_full']:.0f} full, {details['tables']['mixed_4_split']:.0f} split\n"
            output += f"6-top mixed: {details['tables']['mixed_6_full']:.0f} full, {details['tables']['mixed_6_split_3x2']:.0f} split 3x2, {details['tables']['mixed_6_split_4_2']:.0f} split 4+2\n"
            output += f"8-top mixed: {details['tables']['mixed_8_full']:.0f} full, {details['tables']['mixed_8_split']:.0f} split\n\n"
            
            output += "Utilization Rates:\n"
            for table_type, utilization in details['utilization'].items():
                output += f"{table_type.replace('_', '-').title()}: {utilization:.1f}%\n"
            
            return jsonify({
                "summary": summary,
                "output": output
            })
        else:
            # Handle case where capacity cannot be accommodated
            bottleneck = planner.analyze_bottleneck(member_count)
            summary = f"❌ Cannot accommodate {member_count} members\n\n"
            summary += f"Bottleneck: {bottleneck['table_type']} tables\n"
            summary += f"Total utilization: {bottleneck['total_utilization']:.1f}%\n"
            if bottleneck['persona']:
                summary += f"Highest demand from: {bottleneck['persona']} persona"
            
            return jsonify({
                "summary": summary,
                "output": f"Capacity analysis failed for {member_count} members. Bottleneck analysis: {bottleneck}"
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/optimizer')
def get_optimizer():
    try:
        optimizer = plan_optimizer.PlanOptimizer()
        results = optimizer.optimize_pricing()
        
        # Format summary for frontend
        summary = "📊 Plan Optimization Results\n\n"
        summary += "Best value plans for each persona:\n"
        
        # Find best plan for each persona
        persona_best_plans = {}
        for plan in results:
            plan_type = plan['plan_type']
            for persona, ratio in plan['value_ratios'].items():
                if persona not in persona_best_plans or ratio > persona_best_plans[persona]['ratio']:
                    persona_best_plans[persona] = {
                        'plan': plan_type,
                        'ratio': ratio,
                        'price': plan['price']
                    }
        
        for persona, best in persona_best_plans.items():
            summary += f"• {persona.title()}: {best['plan'].title()} plan (${best['price']:.0f}, {best['ratio']:.1f}x value)\n"
        
        # Format detailed output
        output = "Detailed Plan Analysis\n"
        output += "=" * 30 + "\n\n"
        
        for plan in results:
            output += f"{plan['plan_type'].title()} Plan - ${plan['price']:.0f}\n"
            output += "-" * 20 + "\n"
            output += "Features:\n"
            for feature in plan['features']:
                output += f"• {feature}\n"
            output += "\nValue Ratios:\n"
            for persona, ratio in plan['value_ratios'].items():
                output += f"• {persona.title()}: {ratio:.2f}x\n"
            output += "\n"
        
        return jsonify({
            "summary": summary,
            "output": output
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/personas')
def get_personas():
    try:
        optimizer = persona_optimization.PersonaOptimizer()
        results = optimizer.optimize_personas()
        
        # Format summary for frontend
        summary = "👥 Persona Analysis Results\n\n"
        summary += "Best plan matches for each persona:\n"
        
        for persona in results:
            persona_type = persona['persona_type'].title()
            best_plans = persona['best_plans']
            if best_plans:
                summary += f"• {persona_type}: {', '.join([plan.title() for plan in best_plans])}\n"
            else:
                summary += f"• {persona_type}: No plans provide >1x value\n"
        
        # Format detailed output
        output = "Detailed Persona Analysis\n"
        output += "=" * 30 + "\n\n"
        
        for persona in results:
            output += f"{persona['persona_type'].upper()}\n"
            output += "-" * 30 + "\n"
            output += f"Price per visit: ${persona['price_per_visit']}\n\n"
            
            output += "Traits:\n"
            for trait in persona['traits']:
                output += f"• {trait}\n"
            output += "\n"
            
            output += "Plan Value Ratios:\n"
            for plan, ratio in persona['value_ratios'].items():
                output += f"• {plan.title()}: {ratio:.2f}x value\n"
            output += "\n"
            
            if persona['best_plans']:
                output += "Recommended Plans:\n"
                for plan in persona['best_plans']:
                    output += f"• {plan.title()}\n"
            output += "\n"
        
        return jsonify({
            "summary": summary,
            "output": output
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/revenue')
def get_revenue():
    try:
        revenue_planner_instance = revenue_planner.RevenuePlanner()
        results = revenue_planner_instance.calculate_annual_revenue()
        
        # Calculate member counts by persona
        total_members = 300  # Default member count
        member_counts = {
            persona: int(total_members * pct) 
            for persona, pct in planner.PERSONA_DISTRIBUTION.items()
        }
        
        # Format persona revenues for frontend
        persona_revenues = {}
        for persona, count in member_counts.items():
            # Get optimal plan for this persona
            plan_type, plan_price = revenue_planner_instance.get_optimal_plan_for_persona(persona)
            plan_features = planner.PLAN_FEATURES[plan_type]
            
            # Calculate membership revenue
            membership_revenue = count * plan_price / 12  # Monthly
            
            # Calculate extras (guests, retail, snacks)
            extras_revenue = 0
            
            # Guest revenue
            if plan_features.get('guest_passes_annual'):
                additional_guests = max(
                    0,
                    planner.PERSONAS[persona]['guests_per_year'] - plan_features.get('guest_passes_annual', 0)
                )
                extras_revenue += count * (
                    additional_guests * plan_features.get('additional_guest_cost', 10) / 12
                )
            else:
                extras_revenue += count * (
                    planner.PERSONAS[persona]['guests_per_year'] * plan_features.get('guest_cost', 10) / 12
                )
            
            # Retail and snack revenue
            extras_revenue += count * (
                planner.SPENDING['retail_annual'][persona] / 12 +
                planner.PERSONAS[persona]['reserved_visits_annual'] * 
                planner.SPENDING['snacks'][persona] / 12
            )
            
            persona_revenues[persona] = {
                'member_count': count,
                'membership': membership_revenue,
                'extras': extras_revenue,
                'total': membership_revenue + extras_revenue
            }
        
        # Format revenue breakdown for frontend
        revenue_breakdown = {
            'memberships': results['membership_revenue'] / 12,  # Monthly
            'guests': results['guest_revenue'] / 12,  # Monthly
            'mixed_events': 0,  # Not calculated in current model
            'snacks': results['snack_revenue'] / 12,  # Monthly
            'retail': results['retail_revenue'] / 12  # Monthly
        }
        
        return jsonify({
            'persona_revenues': persona_revenues,
            'revenue_breakdown': revenue_breakdown,
            'total_revenue': results['monthly_average']
        })
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
        
        # Transform expense breakdown to include monthly amounts
        expense_calculator = ExpenseCalculator()
        monthly_expenses_detail = expense_calculator.calculate_monthly_expenses()
        expense_breakdown = {}
        
        # Calculate category totals
        category_totals = monthly_expenses_detail.get('total_by_category', {
            'facilities': 0,
            'payroll': 0,
            'software': 0
        })
        
        for category, percentage in metrics['expense_breakdown'].items():
            if category in category_totals:
                expense_breakdown[category] = {
                    'monthly': category_totals[category],
                    'percentage': percentage
                }
        
        # Transform revenue breakdown to use actual dollar amounts
        revenue_breakdown = {}
        monthly_revenue = metrics['monthly']['revenue']
        
        if 'revenue_breakdown' in metrics:
            for category, percentage in metrics['revenue_breakdown'].items():
                revenue_breakdown[category] = monthly_revenue * (percentage / 100)
        
        # Update metrics with transformed data
        metrics['expense_breakdown'] = expense_breakdown
        metrics['revenue_breakdown'] = revenue_breakdown
        
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
    import os
    port = int(os.environ.get('PORT', 3002))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

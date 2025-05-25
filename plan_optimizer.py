# ABOUTME: Optimizes membership plan pricing and features based on persona value analysis
# ABOUTME: Analyzes which plans provide best value for each customer persona type

import planner
from value_calculator import ValueCalculator

class PlanOptimizer:
    def __init__(self):
        self.value_calculator = ValueCalculator()

    def optimize_pricing(self):
        """Analyze plans and return optimization results."""
        optimized_plans = []
        
        for plan_type in ['basic', 'standard', 'family']:
            # Get fresh plan data
            plan_data = planner.calculate_plan_value(plan_type)
            
            # Calculate value ratios for different personas
            value_ratios = {}
            for persona_type in planner.PERSONAS.keys():
                value_ratios[persona_type] = self.value_calculator.calculate_value_ratio(persona_type, plan_type)
            
            # Find best fit personas
            best_for = [
                persona for persona, ratio in value_ratios.items() 
                if ratio > 1.0
            ]
            
            # Get feature descriptions
            feature_list = []
            features = plan_data['features']
            if features['guest_passes'] > 0:
                feature_list.append(f"{features['guest_passes']} guest passes per month")
            if features['mixed_access']:
                feature_list.append("Access to mixed events")
            if features['game_checkouts'] > 0:
                feature_list.append(f"{features['game_checkouts']} game checkouts per month")
            
            optimized_plans.append({
                'plan_type': plan_type,
                'price': plan_data['price'],
                'features': feature_list,
                'value_ratios': value_ratios,
                'best_for': best_for
            })
        
        return optimized_plans

    def print_optimization_results(self):
        """Print optimization results in a clear format."""
        # Calculate all value ratios and collect debug info
        value_ratios = {}
        debug_info = []
        for persona in planner.PERSONAS.keys():
            value_ratios[persona] = {}
            for plan_type in ["basic", "standard", "family"]:
                plan_data = planner.calculate_plan_value(plan_type)
                value = self.value_calculator.calculate_persona_value(plan_data["features"], persona, debug_info if persona == "families" else None)
                value_ratios[persona][plan_type] = value / plan_data["price"]

        # Now start printing results
        print("Plan Optimization Summary")
        print("==================================================\n")

        # Print summary of which personas have each plan in their top 2 choices
        print("Most Likely Plan Selections:")
        print("------------------------------")
        for plan_type in ["basic", "standard", "family"]:
            top_picks = []
            for persona in planner.PERSONAS.keys():
                # Get this plan's rank for this persona
                persona_ratios = [(p, value_ratios[persona][p]) for p in ["basic", "standard", "family"]]
                persona_ratios.sort(key=lambda x: x[1], reverse=True)
                if plan_type in [p for p, _ in persona_ratios[:2]]:
                    top_picks.append(f"{persona.capitalize()} ({value_ratios[persona][plan_type]:.2f}x)")
            
            if top_picks:
                print(f"{plan_type.capitalize()}: {', '.join(top_picks)}")
            else:
                print(f"{plan_type.capitalize()}: No top picks")

        print("\n==================================================\n")
        print("Detailed Analysis")
        print("==================================================\n")

        # For each plan type
        for plan_type in ["basic", "standard", "family"]:
            print(f"{plan_type.capitalize()} Plan")
            print("-" * 20)
            
            # Get plan data
            plan_data = planner.calculate_plan_value(plan_type)
            print(f"Price: ${plan_data['price']}\n")
            
            # Print value ratios for each persona
            print("Value Ratios by Persona:")
            for persona in planner.PERSONAS.keys():
                ratio = value_ratios[persona][plan_type]
                print(f"  {persona.capitalize()}: {ratio:.2f}")
            
            # Print who this plan is best for
            print("\nBest For:")
            for persona in planner.PERSONAS.keys():
                # Get this plan's rank for this persona
                persona_ratios = [(p, value_ratios[persona][p]) for p in ["basic", "standard", "family"]]
                persona_ratios.sort(key=lambda x: x[1], reverse=True)
                if plan_type in [p for p, _ in persona_ratios[:2]]:
                    print(f"  - {persona.capitalize()}")
            
            # Print features
            print("\nFeatures:")
            features = planner.get_plan_features(plan_type)
            for feature in features:
                print(f"  - {feature}")
            print("\n")

        # Print debug info at the bottom
        print("==================================================")
        print("Debug Information")
        print("==================================================\n")
        
        # Print collected debug info
        for i, debug_data in enumerate(debug_info):
            plan_type = ["Basic", "Standard", "Family"][i]
            print(f"\n{plan_type} Plan Value Calculation:")
            print("-" * 40)
            print(f"Visit value: {debug_data['visit_value']}")
            print(f"Guest value: {debug_data['guest_value']}")
            print(f"Retail discount: {debug_data['retail_discount']}")
            print(f"Game value: {debug_data['game_value']}")
            print(f"Additional member value: {debug_data['additional_member_value']}")
            print(f"Event value: {debug_data['event_value']}")
            print(f"Total value: {debug_data['total_value']}")

def analyze_and_recommend_plans():
    """Main function to analyze and recommend optimal plans"""
    optimizer = PlanOptimizer()
    optimizer.print_optimization_results()

if __name__ == "__main__":
    analyze_and_recommend_plans()

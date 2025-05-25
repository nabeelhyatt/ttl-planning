# ABOUTME: Analyzes customer personas and their optimal membership plan matches
# ABOUTME: Evaluates value ratios and recommends best-fit plans for each persona type

import planner
from value_calculator import ValueCalculator

class PersonaOptimizer:
    def __init__(self):
        self.calculator = ValueCalculator()

    def optimize_personas(self):
        """Analyze personas and return optimization results."""
        optimized_personas = []
        
        for persona_type, persona_data in planner.PERSONAS.items():
            # Calculate value ratios for different plans
            value_ratios = {}
            for plan_type in ['basic', 'standard', 'family']:
                value_ratios[plan_type] = self.calculator.calculate_value_ratio(persona_type, plan_type)
            
            # Find best fit plans
            best_plans = [
                plan for plan, ratio in value_ratios.items() 
                if ratio > 1.0
            ]
            
            # Get trait descriptions
            trait_list = []
            if persona_data['reserved_visits'] > 0:
                trait_list.append(f"{persona_data['reserved_visits']} reserved visits per month")
            if persona_data['event_visits'] > 0:
                trait_list.append(f"{persona_data['event_visits']} event visits per month")
            if persona_data['guests_per_month'] > 0:
                trait_list.append(f"{persona_data['guests_per_month']} guests per month")
            if persona_data['game_checkouts'] > 0:
                trait_list.append(f"{persona_data['game_checkouts']} game checkouts per month")
            
            optimized_personas.append({
                'persona_type': persona_type,
                'price_per_visit': persona_data['price'],
                'traits': trait_list,
                'value_ratios': value_ratios,
                'best_plans': best_plans
            })
        
        return optimized_personas

    def print_optimization_results(self):
        """Print optimization results in a formatted way."""
        print("Persona Optimization Summary")
        print("=" * 50)
        
        optimized_personas = self.optimize_personas()
        
        for persona in optimized_personas:
            print(f"\n{persona['persona_type'].upper()}")
            print("-" * 30)
            print("Traits:")
            for trait in persona['traits']:
                print(f"  - {trait}")
            print(f"\nPrice per visit: ${persona['price_per_visit']}")
            print("\nPlan Value Ratios:")
            for plan, ratio in persona['value_ratios'].items():
                print(f"  - {plan.title()}: {ratio:.2f}x value")
            if persona['best_plans']:
                print("\nRecommended Plans:")
                for plan in persona['best_plans']:
                    print(f"  - {plan.title()}")
            print()

def analyze_persona_economics():
    """Main function to analyze persona economics"""
    optimizer = PersonaOptimizer()
    optimizer.print_optimization_results()

if __name__ == "__main__":
    analyze_persona_economics()

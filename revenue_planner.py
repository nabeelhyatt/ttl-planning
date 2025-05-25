# ABOUTME: Calculates monthly revenue projections based on membership plans and capacity
# ABOUTME: Integrates persona behavior, plan selection, and spending assumptions for financial modeling

import planner
from plan_optimizer import PlanOptimizer
from value_calculator import ValueCalculator

class RevenuePlanner:
    def __init__(self):
        self.plan_optimizer = PlanOptimizer()
        self.value_calculator = ValueCalculator()
        
    def get_optimal_plan_for_persona(self, persona):
        """Get the plan with highest value ratio for a persona"""
        value_ratios = {}
        for plan_type in ["basic", "standard", "family"]:
            plan_data = planner.calculate_plan_value(plan_type)
            value = self.value_calculator.calculate_persona_value(plan_data["features"], persona)
            value_ratios[plan_type] = (value / plan_data["price"], plan_data["price"])
        
        # Return plan type and price of the plan with highest value ratio
        best_plan = max(value_ratios.items(), key=lambda x: x[1][0])
        return best_plan[0], best_plan[1][1]

    def calculate_monthly_revenue(self):
        """Calculate projected monthly revenue based on capacity and persona distribution"""
        # Get member capacity from planner
        test_members = [200, 250, 300, 350, 400]
        max_capacity = 0
        for M in test_members:
            if planner.can_accommodate(M)[0]:
                max_capacity = M
        
        if max_capacity == 0:
            raise Exception("No viable member capacity found")
        
        # Calculate revenue per persona
        total_membership_revenue = 0
        total_guest_revenue = 0
        total_mixed_revenue = 0
        total_snack_revenue = 0
        total_retail_revenue = 0
        persona_revenues = {}
        
        for persona_type, distribution in planner.PERSONA_DISTRIBUTION.items():
            member_count = max_capacity * distribution
            persona_data = planner.PERSONAS[persona_type]
            spending = planner.SPENDING
            
            # Get best plan for this persona
            plan_type, plan_price = self.get_optimal_plan_for_persona(persona_type)
            
            # Calculate membership revenue
            membership_revenue = plan_price
            
            # Calculate guest revenue
            guest_revenue = (
                persona_data['guests_per_month'] * 
                planner.GUEST_PRICE * 
                planner.GUEST_SPENDING_MULTIPLIER
            )
            
            # Calculate mixed event revenue (if they have access)
            plan_features = planner.calculate_plan_value(plan_type)["features"]
            mixed_revenue = (
                persona_data['event_visits'] * 
                planner.GUEST_PRICE if plan_features["mixed_access"] else 0
            )
            
            # Calculate total visits per month
            visits_per_month = persona_data['reserved_visits'] + persona_data['event_visits']
            
            # Calculate snack and retail revenue
            snack_revenue = (
                visits_per_month * 
                spending['snacks'][persona_type] * 
                (1 - plan_features["snack_discount"])
            )
            retail_revenue = (
                spending['retail_monthly'][persona_type] * 
                (1 - plan_features["retail_discount"])
            )
            
            # Total monthly revenue for this persona
            total_persona_revenue = (
                membership_revenue + 
                guest_revenue + 
                mixed_revenue + 
                snack_revenue + 
                retail_revenue
            )
            
            # Store individual components for totals
            total_membership_revenue += membership_revenue * member_count
            total_guest_revenue += guest_revenue * member_count
            total_mixed_revenue += mixed_revenue * member_count
            total_snack_revenue += snack_revenue * member_count
            total_retail_revenue += retail_revenue * member_count
            
            # Store persona revenue details
            persona_revenues[persona_type] = {
                'membership': membership_revenue,
                'extras': guest_revenue + mixed_revenue + snack_revenue + retail_revenue,
                'total': total_persona_revenue,
                'member_count': member_count
            }
        
        # Calculate total monthly revenue
        total_revenue = (
            total_membership_revenue +
            total_guest_revenue +
            total_mixed_revenue +
            total_snack_revenue +
            total_retail_revenue
        )
        
        return {
            'max_capacity': max_capacity,
            'persona_revenues': persona_revenues,
            'total_revenue': total_revenue,
            'revenue_breakdown': {
                'memberships': total_membership_revenue,
                'guests': total_guest_revenue,
                'mixed_events': total_mixed_revenue,
                'snacks': total_snack_revenue,
                'retail': total_retail_revenue
            }
        }
    
    def print_revenue_projection(self):
        """Print revenue projection in a clear format"""
        results = self.calculate_monthly_revenue()
        
        print("\nRevenue Projection Summary")
        print("=" * 50)
        print(f"\nProjected for {results['max_capacity']} total members\n")
        
        # Print per-persona breakdown
        print("Revenue by Persona Type")
        print("-" * 50)
        for persona_type, revenue in results['persona_revenues'].items():
            member_count = int(revenue['member_count'])
            monthly = revenue['membership']
            extras = revenue['extras']
            print(f"\n{persona_type.title()} ({member_count} members):")
            print(f"${monthly + extras:.2f}/mo (${monthly:.2f} membership + ${extras:.2f} extras)")
        
        # Print total revenue breakdown
        print("\nTotal Monthly Revenue Breakdown")
        print("-" * 50)
        breakdown = results['revenue_breakdown']
        total = results['total_revenue']
        
        def print_revenue_line(label, amount):
            percentage = (amount / total) * 100
            print(f"{label}: ${amount:,.2f} ({percentage:.1f}%)")
        
        print_revenue_line("Memberships", breakdown['memberships'])
        print_revenue_line("Guests w/Reservations", breakdown['guests'])
        print_revenue_line("Guests w/Mixed Events", breakdown['mixed_events'])
        print_revenue_line("Snacks", breakdown['snacks'])
        print_revenue_line("Retail", breakdown['retail'])
        print("-" * 50)
        print(f"Total Revenue per Month: ${total:,.2f}")

if __name__ == "__main__":
    RevenuePlanner().print_revenue_projection()

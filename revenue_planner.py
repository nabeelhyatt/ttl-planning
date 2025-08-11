# ABOUTME: Calculates annual revenue projections based on membership plans and capacity
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
        for plan_type in ["visitor", "student", "member", "council"]:
            plan_data = planner.calculate_plan_value(plan_type)
            value = self.value_calculator.calculate_persona_value(plan_data["features"], persona)
            value_ratios[plan_type] = (value / plan_data["price"], plan_data["price"])
        
        # Return plan type and price of the plan with highest value ratio
        best_plan = max(value_ratios.items(), key=lambda x: x[1][0])
        return best_plan[0], best_plan[1][1]

    def calculate_annual_revenue(self, member_counts=None, total_members=200):
        """Calculate annual revenue projections based on member counts and spending patterns."""
        if member_counts is None:
            # Use total_members with distribution
            member_counts = {
                persona: int(total_members * pct) 
                for persona, pct in planner.PERSONA_DISTRIBUTION.items()
            }

        # Initialize revenue components
        membership_revenue = 0
        guest_revenue = 0
        retail_revenue = 0
        snack_revenue = 0
        family_addon_revenue = 0
        setup_fee_revenue = 0
        non_member_revenue = 0

        # Calculate revenue for each persona
        for persona, count in member_counts.items():
            # Get optimal plan for this persona
            plan_type, plan_price = self.get_optimal_plan_for_persona(persona)
            plan_features = planner.PLAN_FEATURES[plan_type]
            
            # Membership revenue
            membership_revenue += count * plan_price
            
            # Guest revenue
            if plan_features.get('guest_passes_annual'):
                # Calculate guest passes used
                guest_passes_used = min(
                    plan_features.get('guest_passes_annual', 0),
                    planner.PERSONAS[persona]['guests_per_year']
                )
                # Calculate additional guests
                additional_guests = max(
                    0,
                    planner.PERSONAS[persona]['guests_per_year'] - plan_features.get('guest_passes_annual', 0)
                )
                guest_revenue += count * (
                    additional_guests * plan_features.get('additional_guest_cost', 10)
                )
            else:
                # For plans with per-guest pricing
                guest_revenue += count * (
                    planner.PERSONAS[persona]['guests_per_year'] * plan_features.get('guest_cost', 10)
                )
            
            # Retail revenue
            retail_revenue += count * planner.SPENDING['retail_annual'][persona]
            
            # Snack revenue
            snack_revenue += count * (
                planner.PERSONAS[persona]['reserved_visits_annual'] * 
                planner.SPENDING['snacks'][persona]
            )
            
            # Family addon revenue
            if plan_features.get('family_addon_monthly'):
                family_addon_revenue += count * (
                    plan_features['family_addon_monthly'] * 12  # Annual family addon
                )

        # Setup fee revenue (assuming 20% annual turnover, $50 per new member)
        total_member_count = sum(member_counts.values())
        new_members_annual = total_member_count * 0.2  # 20% turnover
        setup_fee_amount = 50  # $50 setup fee
        setup_fee_revenue = new_members_annual * setup_fee_amount

        # Non-member retail revenue 
        # From Excel: $2,400/month = $28,800/year from non-members
        # This is roughly equal to member retail at 200 members
        non_member_revenue = retail_revenue * 1.2  # Non-members spend 20% more than members

        # Calculate total revenue
        total_revenue = (
            membership_revenue +
            guest_revenue +
            retail_revenue +
            snack_revenue +
            family_addon_revenue +
            setup_fee_revenue +
            non_member_revenue
        )

        # Return detailed breakdown
        return {
            'membership_revenue': membership_revenue,
            'guest_revenue': guest_revenue,
            'retail_revenue': retail_revenue,
            'snack_revenue': snack_revenue,
            'family_addon_revenue': family_addon_revenue,
            'setup_fee_revenue': setup_fee_revenue,
            'non_member_revenue': non_member_revenue,
            'total_revenue': total_revenue,
            'monthly_average': total_revenue / 12
        }

    def print_revenue_breakdown(self, member_counts=None):
        """Print detailed revenue breakdown."""
        revenue = self.calculate_annual_revenue(member_counts)
        
        print("Annual Revenue Projection")
        print("========================")
        print(f"Membership Revenue: ${revenue['membership_revenue']:,.2f}")
        print(f"Guest Revenue: ${revenue['guest_revenue']:,.2f}")
        print(f"Retail Revenue (Members): ${revenue['retail_revenue']:,.2f}")
        print(f"Snack Revenue: ${revenue['snack_revenue']:,.2f}")
        print(f"Family Addon Revenue: ${revenue['family_addon_revenue']:,.2f}")
        print(f"Setup Fee Revenue: ${revenue['setup_fee_revenue']:,.2f}")
        print(f"Non-Member Revenue: ${revenue['non_member_revenue']:,.2f}")
        print("------------------------")
        print(f"Total Annual Revenue: ${revenue['total_revenue']:,.2f}")
        print(f"Average Monthly Revenue: ${revenue['monthly_average']:,.2f}")

if __name__ == "__main__":
    RevenuePlanner().print_revenue_breakdown()

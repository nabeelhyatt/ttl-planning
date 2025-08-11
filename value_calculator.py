# ABOUTME: Calculates perceived value of membership plans for different customer personas
# ABOUTME: Determines value ratios based on usage patterns, features, and pricing

import planner

class ValueCalculator:
    def __init__(self):
        # Get personas from planner for value calculation
        self.personas = {}
        for persona_type, data in planner.PERSONAS.items():
            self.personas[persona_type] = {
                "visits_per_year": data['reserved_visits_annual'] + data['event_visits_annual'],
                "price_per_visit": data['price'],
                "guests_per_year": data['guests_per_year'],
                "game_checkouts_annual": data['game_checkouts_annual'],
                "weekday_preference": data['weekday_preference'],
                "coworking_hours": data['coworking_hours'],
                "advance_booking_needs": data['advance_booking_needs']
            }

    def calculate_persona_value(self, plan_features, persona_type, debug_output=None):
        """Calculate the annual value of a plan for a specific persona."""
        traits = self.personas[persona_type]
        
        # 1. Base value from visits
        if plan_features['visits_included'] != float('inf'):
            # For limited visit plans, calculate value of included visits
            visit_value = min(plan_features['visits_included'], traits["visits_per_year"]) * traits["price_per_visit"]
            # Add value for any overage visits
            if traits["visits_per_year"] > plan_features['visits_included']:
                visit_value += (traits["visits_per_year"] - plan_features['visits_included']) * plan_features['additional_visit_cost']
        else:
            # For unlimited plans, calculate full value of their visits
            visit_value = traits["visits_per_year"] * traits["price_per_visit"]
        
        # 2. Value from guest passes
        if plan_features['guest_passes_annual']:
            # Calculate value of guest passes up to their annual guest count
            guest_pass_value = min(plan_features['guest_passes_annual'], traits["guests_per_year"]) * traits["price_per_visit"]
            # Add value for any additional guests
            if traits["guests_per_year"] > plan_features['guest_passes_annual']:
                guest_pass_value += (traits["guests_per_year"] - plan_features['guest_passes_annual']) * plan_features['additional_guest_cost']
        else:
            # For plans with per-guest pricing
            guest_pass_value = traits["guests_per_year"] * plan_features['guest_cost']
        
        # 3. Value from weekday restrictions
        weekday_value = 0
        if plan_features['weekday_only']:
            # Calculate penalty for weekday-only restriction
            weekend_visits = traits["visits_per_year"] * (1 - traits["weekday_preference"])
            weekday_value = -weekend_visits * traits["price_per_visit"] * 0.5  # 50% penalty for lost weekend visits
        
        # 4. Value from coworking access
        coworking_value = 0
        if plan_features['coworking_access']:
            coworking_value = traits["coworking_hours"] * 10  # $10/hour value for coworking
        
        # 5. Value from 24/7 access
        access_value = 0
        if plan_features['24_7_access']:
            access_value = 500  # Annual value of 24/7 access
        
        # 6. Value from advance booking
        booking_value = 0
        if plan_features['advance_booking_days']:
            booking_value = min(plan_features['advance_booking_days'], traits["advance_booking_needs"]) * 2  # $2 per day of advance booking
        
        # 7. Value from gift memberships
        gift_value = 0
        if plan_features['gift_memberships']:
            gift_value = plan_features['gift_memberships'] * 100  # $100 value per gift membership
        
        # 8. Value from family addon
        family_value = 0
        if plan_features['family_addon_monthly']:
            family_value = plan_features['family_addon_monthly'] * 12  # Annual value of family addon
        
        # Store debug output if requested
        if debug_output is not None:
            debug_output.append({
                "visit_value": visit_value,
                "guest_value": guest_pass_value,
                "weekday_value": weekday_value,
                "coworking_value": coworking_value,
                "access_value": access_value,
                "booking_value": booking_value,
                "gift_value": gift_value,
                "family_value": family_value,
                "total_value": visit_value + guest_pass_value + weekday_value + coworking_value + access_value + booking_value + gift_value + family_value
            })
        
        # Total annual value is sum of all components
        annual_value = (
            visit_value +          # Value from visits
            guest_pass_value +     # Value from guest passes
            weekday_value +        # Value/penalty from weekday restrictions
            coworking_value +      # Value from coworking access
            access_value +         # Value from 24/7 access
            booking_value +        # Value from advance booking
            gift_value +           # Value from gift memberships
            family_value           # Value from family addon
        )
        
        return annual_value

    def calculate_value_ratio(self, persona_type, plan_type):
        """Calculate the value ratio for a specific persona and plan type."""
        plan_data = planner.calculate_plan_value(plan_type)
        value = self.calculate_persona_value(plan_data["features"], persona_type)
        return value / plan_data["price"]

import planner

class ValueCalculator:
    def __init__(self):
        # Get personas from planner for value calculation
        self.personas = {}
        for persona_type, data in planner.PERSONAS.items():
            self.personas[persona_type] = {
                "visits_per_month": data['reserved_visits'] + data['mixed_visits'],
                "price_per_visit": data['price'],
                "guests_per_month": data['guests_per_month'],
                "game_checkouts": data['game_checkouts']
            }

    def calculate_persona_value(self, plan_features, persona_type, debug_output=None):
        """Calculate the value of a plan for a specific persona."""
        traits = self.personas[persona_type]
        
        # 1. Base value from visits
        # Their value per visit * number of visits they plan to make
        visit_value = traits["visits_per_month"] * traits["price_per_visit"]
        
        # 2. Value from guest passes
        # They value guest passes at 75% of their own visit value (25% discount)
        guest_pass_value = traits["price_per_visit"] * 0.75
        # Only count guest passes up to their monthly guest count
        guest_value = min(plan_features["guest_passes"], traits["guests_per_month"]) * guest_pass_value
        
        # 3. Value from retail discounts
        # Assume they spend about their visit value on retail per month
        monthly_retail_spend = traits["visits_per_month"] * traits["price_per_visit"]
        retail_discount_value = monthly_retail_spend * plan_features["retail_discount"]
        
        # 4. Value from game checkouts (up to their monthly checkout count)
        game_value = min(plan_features["game_checkouts"], traits["game_checkouts"]) * planner.GAME_CHECKOUT_VALUE
        
        # 5. Value from additional members
        # For family plan, value additional members at 75% instead of 50%
        member_discount = 0.75 if plan_features.get("additional_members", 0) >= 3 else 0.5
        additional_member_value = (
            plan_features["additional_members"] * 
            (traits["visits_per_month"] * traits["price_per_visit"]) * 
            member_discount
        )
        
        # 6. Value from event access
        event_value = (getattr(planner, 'EVENT_VALUE', None) or planner.MIXED_VALUE) if plan_features["mixed_access"] else 0
        
        # Store debug output if requested
        if debug_output is not None and persona_type == 'families':
            debug_output.append({
                "visit_value": visit_value,
                "guest_value": guest_value,
                "retail_discount": retail_discount_value,
                "game_value": game_value,
                "additional_member_value": additional_member_value,
                "event_value": event_value,
                "total_value": visit_value + guest_value + retail_discount_value + game_value + additional_member_value + event_value
            })
        
        # Total monthly value is sum of all components
        monthly_value = (
            visit_value +              # Value from their own visits
            guest_value +              # Value from guest passes
            retail_discount_value +    # Value from retail discounts
            game_value +               # Value from game checkouts
            additional_member_value +  # Value from additional members
            event_value                # Value from event access
        )
        
        return monthly_value

    def calculate_value_ratio(self, persona_type, plan_type):
        """Calculate value ratio for a persona-plan pair."""
        plan_data = planner.calculate_plan_value(plan_type)
        value = self.calculate_persona_value(plan_data["features"], persona_type)
        return value / plan_data["price"]

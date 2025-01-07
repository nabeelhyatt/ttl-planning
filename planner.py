import pulp

# Time block constants (3-hour blocks)
# Weekday blocks (M-F):
# - Operating hours 5PM-11PM: 6hrs/day ÷ 3hr blocks = 2 blocks/day × 5 days = 10 blocks/week
WEEKDAY_BLOCKS = 10  # 2 blocks/day * 5 days

# Weekend blocks (S-S):
# - Operating hours 9AM-11PM: 14hrs/day ÷ 3hr blocks ≈ 4.67 blocks/day × 2 days ≈ 9 blocks/week
WEEKEND_BLOCKS = 9  # ~4.67 blocks/day * 2 days

# Total blocks per month (assuming 4.33 weeks/month)
TIME_BLOCKS_PER_MONTH = int((WEEKDAY_BLOCKS + WEEKEND_BLOCKS) * 4.33)  # ~82 blocks/month

# All weekday blocks (5PM-11PM) and weekend blocks are considered peak time
PEAK_TIME_BLOCKS = TIME_BLOCKS_PER_MONTH  # All blocks are peak time
OFFPEAK_TIME_BLOCKS = 0  # No off-peak time in new schedule

# Revenue constants
GUEST_PRICE = 8  # Price per guest
MEMBER_COUNT = None  # Will be set by analyze_capacity
BASE_VISIT_VALUE = 12  # Value of a single visit
MIXED_VALUE = 12  # Value of mixed event entry
GAME_CHECKOUT_VALUE = 5  # Value of checking out a game
BASE_VALUE_CAP = 100  # Cap on base visit value

# Plan prices
BASIC_PLAN_PRICE = 35
STANDARD_PLAN_PRICE = 75
FAMILY_PLAN_PRICE = 125

# Value of additional member is tied to standard plan price
ADDITIONAL_MEMBER_VALUE = STANDARD_PLAN_PRICE

# Guest spending multiplier (guests spend X times what members spend)
GUEST_SPENDING_MULTIPLIER = 1  # Guests tend to spend a bit more

# Distribution percentages
PERSONA_DISTRIBUTION = {
    'casual': 0.45,    # 45% casual gamers
    'students': 0.15,  # 15% students
    'families': 0.15,  # 15% families
    'hobbyists': 0.15, # 15% hobbyists
    'everyday': 0.10   # 10% everyday players
}

# Persona prices, guests, and visit mixes
PERSONAS = {
    'casual': {
        'price': 8,   # price willing to pay per visit
        'guests_per_month': 3,   # Assumes 2 guests on average for a 4-top
        'reserved_visits': 1,       # visits/month
        'mixed_visits': .5,        # mixed visits/month
        'game_checkouts': 0,          # 1 game checkout per month
        'avg_group_size': 4
    },
    'students': {
        'price': 5,   # price willing to pay per visit
        'guests_per_month': 3,   # Assumes 3 guests for a 4-top
        'reserved_visits': 8,       # visits/month
        'mixed_visits': 1,          # mixed visits/month
        'game_checkouts': 1,          # 1 game checkout per month
        'avg_group_size': 3
    },
    'families': {
        'price': 15,   # price willing to pay per visit
        'guests_per_month': 2.5, # Average between solo parent (2 kids) and family visit (3 family)
        'reserved_visits': 3,       # visits/month
        'mixed_visits': 2,          # mixed visits/month
        'game_checkouts': 1,          # 1 game checkout per month
        'avg_group_size': 4
    },
    'hobbyists': {
        'price': 10,   # price willing to pay per visit
        'guests_per_month': 3,   # Assumes 3 guests for a 4-top
        'reserved_visits': 4,       # visits/month
        'mixed_visits': 2,          # mixed visits/month
        'game_checkouts': 2,          # 2 game checkouts per month
        'avg_group_size': 4
    },
    'everyday': {
        'price': 5,   # price willing to pay per visit
        'guests_per_month': 3,   # Assumes 3 guests for a 4-top
        'reserved_visits': 8,       # visits/month
        'mixed_visits': 4,          # mixed event visits/month
        'game_checkouts': 2,          # 10 game checkouts per month
        'avg_group_size': 4
    }
}

# Per-visit spending assumptions
SPENDING = {
    'retail_monthly': {  # Average retail spending per month
        'casual': 0,     # No monthly retail
        'students': 5,   # $5/month
        'families': 10,  # $10/month
        'hobbyists': 15, # $15/month
        'everyday': 15   # $15/month
    },
    'snacks': {  # Average snack/drink spending per visit
        'casual': 10,    # $10/visit
        'students': 5,   # $5/visit
        'families': 7,   # $7/visit
        'hobbyists': 4,  # $4/visit
        'everyday': 4    # $4/visit
    }
}

def get_guest_price():
    return GUEST_PRICE

def get_member_count():
    return MEMBER_COUNT

def get_distribution():
    return PERSONA_DISTRIBUTION

def get_personas():
    return PERSONAS

def get_spending_assumptions():
    """Get spending assumptions for all personas"""
    return SPENDING

def get_guest_spending_multiplier():
    return GUEST_SPENDING_MULTIPLIER

def compute_demands(M):
    """Compute demands for each persona type based on member count M"""
    distribution = PERSONA_DISTRIBUTION
    personas = PERSONAS
    
    # Initialize demands
    demands = {
        'reserved_4_full': 0,    # Number of 4-top tables needed for 4-person reservations (monthly)
        'reserved_2_split': 0,   # Number of 2-person reservations that can share 4-top (monthly)
        'mixed_seats': 0,        # Number of individual seats needed for mixed seating (monthly)
        'type_demands': {}
    }
    
    # For each persona type
    for persona_type, pct in distribution.items():
        member_count = M * pct
        persona = personas[persona_type]
        
        # Calculate monthly visit frequencies
        reserved_visits = member_count * persona['reserved_visits']  # visits per month
        mixed_visits = member_count * persona['mixed_visits']  # visits per month
        
        # Calculate average group sizes
        avg_group_size = persona.get('avg_group_size', 2)
        
        # Calculate total monthly table needs for reservations
        # For reservations, we need enough tables to handle the monthly volume spread across blocks
        reservation_distribution_factor = 0.3  # Assume 30% of blocks will have reservations
        available_blocks = TIME_BLOCKS_PER_MONTH * reservation_distribution_factor
        
        persona_4_full = (reserved_visits * (1 if avg_group_size > 2 else 0)) / available_blocks
        persona_2_split = (reserved_visits * (1 if avg_group_size <= 2 else 0)) / available_blocks
        
        # For mixed seating, we need concurrent capacity in each block
        # Using 0.7 factor to account for better table turnover with 3-hour blocks
        utilization_factor = 0.7  # Reduced from 0.9 to be more conservative
        mixed_seats = int((mixed_visits * avg_group_size * utilization_factor) / TIME_BLOCKS_PER_MONTH)  # seats needed per block
        
        # Store type-specific demands with just this persona's contribution
        demands['type_demands'][persona_type] = {
            'reserved_4_full': persona_4_full,
            'reserved_2_split': persona_2_split,
            'mixed_seats': mixed_seats
        }
        
        # Update total demands
        demands['reserved_4_full'] += persona_4_full
        demands['reserved_2_split'] += persona_2_split
        demands['mixed_seats'] += mixed_seats
    
    return demands

def can_accommodate(M, peak_time_blocks=PEAK_TIME_BLOCKS, offpeak_time_blocks=OFFPEAK_TIME_BLOCKS):
    """Check if we can accommodate M members with current capacity
    
    Args:
        M: Number of members to accommodate
        peak_time_blocks: Number of 3-hour blocks during operating hours (5PM-11PM weekdays, 9AM-11PM weekends)
        offpeak_time_blocks: Not used in new schedule (always 0)
    """
    time_blocks = peak_time_blocks + offpeak_time_blocks  # Total time blocks for backward compatibility
    demands = compute_demands(M)
    
    # Capacity constants
    NUM_4_TOP = 6  # Number of 4-top tables
    NUM_8_TOP = 3  # Number of 8-top tables
    
    # Create optimization model
    model = pulp.LpProblem("Seating_Optimization", pulp.LpMinimize)
    
    # Decision variables for table allocation during peak hours
    peak_reserved_4_full = pulp.LpVariable("peak_reserved_4_full", 0, NUM_4_TOP)  # 4-top tables used fully
    peak_reserved_4_split = pulp.LpVariable("peak_reserved_4_split", 0, NUM_4_TOP)  # 4-top tables split into 2-tops
    peak_mixed_4_full = pulp.LpVariable("peak_mixed_4_full", 0, NUM_4_TOP)  # 4-top tables for mixed seating (full)
    peak_mixed_4_split = pulp.LpVariable("peak_mixed_4_split", 0, NUM_4_TOP)  # 4-top tables for mixed seating (split)
    peak_mixed_8 = pulp.LpVariable("peak_mixed_8", 0, NUM_8_TOP)  # 8-top tables for mixed seating

    # Decision variables for table allocation during off-peak hours
    offpeak_reserved_4_full = pulp.LpVariable("offpeak_reserved_4_full", 0, NUM_4_TOP)  # 4-top tables used fully
    offpeak_reserved_4_split = pulp.LpVariable("offpeak_reserved_4_split", 0, NUM_4_TOP)  # 4-top tables split into 2-tops
    offpeak_mixed_4_full = pulp.LpVariable("offpeak_mixed_4_full", 0, NUM_4_TOP)  # 4-top tables for mixed seating (full)
    offpeak_mixed_4_split = pulp.LpVariable("offpeak_mixed_4_split", 0, NUM_4_TOP)  # 4-top tables for mixed seating (split)
    offpeak_mixed_8 = pulp.LpVariable("offpeak_mixed_8", 0, NUM_8_TOP)  # 8-top tables for mixed seating
    
    # Objective: Maximize efficient table usage while prioritizing peak hours and reservations
    # Objective: Maximize efficient table usage while encouraging mixed seating
    # 1. Reserved seating (base weights)
    reserved_weight = 1.0
    # 2. Mixed seating (reduced weights to encourage usage)
    mixed_weight = 0.6
    # 3. Split table penalty (small penalty for splitting tables)
    split_penalty = 0.2
    
    model += (
        # Reserved seating terms
        reserved_weight * (
            peak_reserved_4_full +
            (1 + split_penalty) * peak_reserved_4_split
        ) +
        # Mixed seating terms (lower weights to encourage usage)
        mixed_weight * (
            peak_mixed_4_full +
            (1 + split_penalty) * peak_mixed_4_split +
            1.2 * peak_mixed_8  # Slightly higher weight for 8-tops
        )
    )
    
    # Constraints
    
    # All demand is during peak hours in new schedule (5PM-11PM weekdays, 9AM-11PM weekends)
    # No off-peak hours in new schedule
    PEAK_DEMAND_RATIO = 1.0  # All demand during peak hours
    OFFPEAK_DEMAND_RATIO = 0.0  # No off-peak hours

    # Meet all demand during peak hours (no off-peak in new schedule)
    model += peak_reserved_4_full * peak_time_blocks >= demands['reserved_4_full']
    model += peak_reserved_4_split * peak_time_blocks * 2 >= demands['reserved_2_split']

    # Meet all mixed seating demand during peak hours with more flexible constraints
    mixed_demand = demands['mixed_seats']
    
    # Total mixed seating capacity must meet demand
    model += (
        peak_mixed_4_full * peak_time_blocks * 4 +
        peak_mixed_4_split * peak_time_blocks * 2 +
        peak_mixed_8 * peak_time_blocks * 8
    ) >= mixed_demand

    # Soft targets for distribution (using <= instead of == to allow flexibility)
    model += peak_mixed_4_full * peak_time_blocks * 4 <= 0.5 * mixed_demand  # Target ~40-50% on full 4-tops
    model += peak_mixed_4_split * peak_time_blocks * 2 <= 0.4 * mixed_demand  # Target ~30-40% on split 4-tops
    model += peak_mixed_8 * peak_time_blocks * 8 <= 0.3 * mixed_demand  # Target ~20-30% on 8-tops

    # No off-peak constraints needed since there are no off-peak hours
    # Setting off-peak variables to 0 since they won't be used
    model += offpeak_reserved_4_full == 0
    model += offpeak_reserved_4_split == 0
    model += offpeak_mixed_4_full == 0
    model += offpeak_mixed_4_split == 0
    model += offpeak_mixed_8 == 0
    
    # Table capacity constraints - ensure total tables used doesn't exceed capacity
    # For 4-top tables during peak hours
    model += (peak_reserved_4_full + peak_reserved_4_split + 
             peak_mixed_4_full + peak_mixed_4_split) <= NUM_4_TOP
    # For 8-top tables during peak hours
    model += peak_mixed_8 <= NUM_8_TOP
    
    # For 4-top tables during off-peak hours
    model += (offpeak_reserved_4_full + offpeak_reserved_4_split + 
             offpeak_mixed_4_full + offpeak_mixed_4_split) <= NUM_4_TOP
    # For 8-top tables during off-peak hours
    model += offpeak_mixed_8 <= NUM_8_TOP

    # Solve the model
    model.solve()

    # Check if solution exists and is optimal
    if pulp.LpStatus[model.status] == 'Optimal':
        results = {
            'peak': {
                'reserved_4_full': peak_reserved_4_full.value(),
                'reserved_4_split': peak_reserved_4_split.value(),
                'mixed_4_full': peak_mixed_4_full.value(),
                'mixed_4_split': peak_mixed_4_split.value(),
                'mixed_8': peak_mixed_8.value()
            },
            'offpeak': {
                'reserved_4_full': offpeak_reserved_4_full.value(),
                'reserved_4_split': offpeak_reserved_4_split.value(),
                'mixed_4_full': offpeak_mixed_4_full.value(),
                'mixed_4_split': offpeak_mixed_4_split.value(),
                'mixed_8': offpeak_mixed_8.value()
            },
            'demands': demands,
            'time_blocks': {
                'peak': peak_time_blocks,
                'offpeak': offpeak_time_blocks,
                'total': peak_time_blocks + offpeak_time_blocks
            }
        }
        
        # Calculate utilization rates for both time periods
        peak_four_top_util = (results['peak']['reserved_4_full'] + 
                            results['peak']['reserved_4_split'] + 
                            results['peak']['mixed_4_full'] + 
                            results['peak']['mixed_4_split'])/NUM_4_TOP * 100
        peak_eight_top_util = results['peak']['mixed_8']/NUM_8_TOP * 100
        
        offpeak_four_top_util = (results['offpeak']['reserved_4_full'] + 
                               results['offpeak']['reserved_4_split'] + 
                               results['offpeak']['mixed_4_full'] + 
                               results['offpeak']['mixed_4_split'])/NUM_4_TOP * 100
        offpeak_eight_top_util = results['offpeak']['mixed_8']/NUM_8_TOP * 100
        
        # Return True if neither period exceeds capacity
        if (peak_four_top_util <= 100 and peak_eight_top_util <= 100 and
            offpeak_four_top_util <= 100 and offpeak_eight_top_util <= 100):
            return True, results
    
    return False, None

def analyze_capacity(test_members=[200, 250, 300, 350, 400]):
    """Analyze capacity for different member counts"""
    print("Capacity Analysis Summary")
    print("=" * 50)
    
    results = []
    for M in test_members:
        demands = compute_demands(M)
        total_tables = 6 + 3
        
        # Calculate tables needed
        # For 4-tops: count full tables and half for split tables
        four_top_tables = (demands['reserved_4_full'] + demands['reserved_2_split']/2)/TIME_BLOCKS_PER_MONTH
        # For mixed: assume average 4 seats per table (more realistic than optimal 8)
        mixed_tables_needed = demands['mixed_seats']/(4 * TIME_BLOCKS_PER_MONTH)  # Using 4 seats/table average
        
        total_tables_needed = four_top_tables + mixed_tables_needed
        capacity_used = (total_tables_needed / total_tables) * 100
        
        if can_accommodate(M)[0]:
            results.append(f"{M} members: {capacity_used:.0f}% capacity")
        else:
            results.append(f"{M} members: ✗ cannot accommodate ({capacity_used:.0f}% capacity)")
    
    # Print summary
    for result in results:
        print(result)
    print("\nDetailed Analysis")
    print("=" * 50)
    
    # Do detailed analysis for each member count
    for M in test_members:
        print(f"\nAnalyzing capacity for {M} members:")
        print("-" * 50)
        
        can_fit, results = can_accommodate(M)
        
        if can_fit and results is not None:
            print(f"✓ Can accommodate {M} members!")
            
            if 'demands' in results:
                demands = results['demands']
            
                print("\nPeak Hours Table Usage (evenings/weekends):")
                print("-" * 40)
                print("4-top tables:")
                if 'peak' in results:
                    print(f"Full reservations: {results['peak']['reserved_4_full']:.1f} tables")
                    print(f"Split reservations: {results['peak']['reserved_4_split']:.1f} tables ({results['peak']['reserved_4_split']*2:.1f} 2-person slots)")
                    print(f"Mixed seating (full): {results['peak']['mixed_4_full']:.1f} tables ({results['peak']['mixed_4_full']*4:.1f} seats)")
                    print(f"Mixed seating (split): {results['peak']['mixed_4_split']:.1f} tables ({results['peak']['mixed_4_split']*2:.1f} seats)")
                    print("\n8-top tables:")
                    print(f"Mixed seating: {results['peak']['mixed_8']:.1f} tables ({results['peak']['mixed_8']*8:.1f} seats)")
                
                print("\nOff-Peak Hours Table Usage (weekday daytime):")
                print("-" * 40)
                print("4-top tables:")
                if 'offpeak' in results:
                    print(f"Full reservations: {results['offpeak']['reserved_4_full']:.1f} tables")
                    print(f"Split reservations: {results['offpeak']['reserved_4_split']:.1f} tables ({results['offpeak']['reserved_4_split']*2:.1f} 2-person slots)")
                    print(f"Mixed seating (full): {results['offpeak']['mixed_4_full']:.1f} tables ({results['offpeak']['mixed_4_full']*4:.1f} seats)")
                    print(f"Mixed seating (split): {results['offpeak']['mixed_4_split']:.1f} tables ({results['offpeak']['mixed_4_split']*2:.1f} seats)")
                    print("\n8-top tables:")
                    print(f"Mixed seating: {results['offpeak']['mixed_8']:.1f} tables ({results['offpeak']['mixed_8']*8:.1f} seats)")
                
                print("\nTime Block Distribution:")
                print("-" * 20)
                if 'time_blocks' in results:
                    print(f"Peak blocks: {results['time_blocks']['peak']} ({results['time_blocks']['peak']/results['time_blocks']['total']*100:.1f}%)")
                    print(f"Off-peak blocks: {results['time_blocks']['offpeak']} ({results['time_blocks']['offpeak']/results['time_blocks']['total']*100:.1f}%)")
                    print(f"Total blocks: {results['time_blocks']['total']}")
            
            print("\nBy Persona Type:")
            print("-" * 20)
            for persona_type, type_demands in demands['type_demands'].items():
                print(f"\n{persona_type.title()}:")
                print(f"  Full 4-top reservations needed: {type_demands['reserved_4_full']:.1f}")
                print(f"  2-person reservations needed: {type_demands['reserved_2_split']:.1f}")
                print(f"  Mixed seats needed: {type_demands['mixed_seats']:.1f}")
            
            print("\nUtilization Rates:")
            print("-" * 20)
            # Calculate combined utilization from peak and off-peak
            four_top_util = ((results['peak']['reserved_4_full'] + results['peak']['reserved_4_split'] + 
                            results['peak']['mixed_4_full'] + results['peak']['mixed_4_split'] +
                            results['offpeak']['reserved_4_full'] + results['offpeak']['reserved_4_split'] + 
                            results['offpeak']['mixed_4_full'] + results['offpeak']['mixed_4_split'])/6) * 100
            eight_top_util = ((results['peak']['mixed_8'] + results['offpeak']['mixed_8'])/3) * 100
            print(f"4-top tables: {four_top_util:.1f}%")
            print(f"8-top tables: {eight_top_util:.1f}%")
            print(f"Overall: {(four_top_util * 6 + eight_top_util * 3)/(6 + 3):.1f}%")
        else:
            print(f"✗ Cannot accommodate {M} members")
            demands = compute_demands(M)
            
            print("\nDemands that couldn't be met:")
            print("-" * 20)
            print(f"Full 4-top reservations needed: {demands['reserved_4_full']/TIME_BLOCKS_PER_MONTH:.1f}")
            print(f"2-person reservations needed: {demands['reserved_2_split']/TIME_BLOCKS_PER_MONTH:.1f}")
            print(f"Mixed seats needed: {demands['mixed_seats']:.1f}")
            
            print("\nBy Persona Type:")
            print("-" * 20)
            for persona_type, type_demands in demands['type_demands'].items():
                print(f"\n{persona_type.title()}:")
                print(f"  Full 4-top reservations needed: {type_demands['reserved_4_full']:.1f}")
                print(f"  2-person reservations needed: {type_demands['reserved_2_split']:.1f}")
                print(f"  Mixed seats needed: {type_demands['mixed_seats']:.1f}")
    
    return can_fit

def calculate_plan_value(plan_type):
    """Calculate the value and features for a given plan type."""
    if plan_type.lower() == "basic":
        features = {
            "guest_passes": 1,
            "retail_discount": 0.1,  # 10%
            "snack_discount": 0.1,   # 10%
            "mixed_access": False,
            "additional_members": 0,  # No additional members
            "game_checkouts": 1
        }
        price = BASIC_PLAN_PRICE
    elif plan_type.lower() == "standard":
        features = {
            "guest_passes": 2,
            "retail_discount": 0.15,  # 15%
            "snack_discount": 0.15,   # 15%
            "mixed_access": True,
            "additional_members": 1,  # One additional member
            "game_checkouts": 2
        }
        price = STANDARD_PLAN_PRICE
    elif plan_type.lower() == "family":
        features = {
            "guest_passes": 4,
            "retail_discount": 0.2,   # 20%
            "snack_discount": 0.2,    # 20%
            "mixed_access": True,
            "additional_members": 3,  # Three additional family members
            "game_checkouts": 4
        }
        price = FAMILY_PLAN_PRICE
    else:
        raise ValueError(f"Invalid plan type: {plan_type}")
    
    # Calculate base value
    value = BASE_VISIT_VALUE
    
    # Add value for features
    value += features["guest_passes"] * GUEST_PRICE
    if features["mixed_access"]:
        value += MIXED_VALUE
    value += features["game_checkouts"] * GAME_CHECKOUT_VALUE
    
    # Cap the base value
    value = min(value, BASE_VALUE_CAP)
    
    return {
        "plan_type": plan_type,
        "price": float(price),
        "monthly_value": float(value),
        "value_ratio": float(value / price),
        "features": features
    }

def get_plan_features(plan_type):
    """Get list of features for a given plan type."""
    features = []
    
    if plan_type.lower() == "basic":
        features = [
            '1 Guest Pass',
            '10% Retail Discount',
            '1 Game Checkout'
        ]
    elif plan_type.lower() == "standard":
        features = [
            '2 Guest Passes',
            '15% Retail Discount',
            'Mixed Event Access',
            '1 Additional Member',
            '2 Game Checkouts'
        ]
    elif plan_type.lower() == "family":
        features = [
            '4 Guest Passes',
            '20% Retail Discount',
            'Mixed Event Access',
            '3 Additional Members',
            '4 Game Checkouts'
        ]
    
    return features

if __name__ == "__main__":
    analyze_capacity()

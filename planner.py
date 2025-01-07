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
        
        # Calculate raw monthly table needs for reservations
        # Distribute between 4-tops and 2-person based on group size
        # For avg_group_size=4: 80% 4-tops, 20% 2-person
        # For avg_group_size=3: 60% 4-tops, 40% 2-person
        # For avg_group_size=2: 20% 4-tops, 80% 2-person
        if avg_group_size == 4:
            four_top_pct = 0.8
        elif avg_group_size == 3:
            four_top_pct = 0.6
        else:  # avg_group_size == 2
            four_top_pct = 0.2
            
        # Calculate raw monthly table needs with stricter capacity scaling
        capacity_factor = 0.4  # Reduce raw demands to ensure we stay under physical limits
        
        # Calculate per-block demands with capacity factor only
        # This ensures we don't exceed physical capacity even at peak times
        persona_4_full_raw = (reserved_visits * four_top_pct * capacity_factor) / TIME_BLOCKS_PER_MONTH
        persona_2_split_raw = (reserved_visits * (1 - four_top_pct) * capacity_factor) / TIME_BLOCKS_PER_MONTH
        mixed_seats_raw = (mixed_visits * avg_group_size * capacity_factor) / TIME_BLOCKS_PER_MONTH
        
        # Store raw type-specific demands with just this persona's contribution
        demands['type_demands'][persona_type] = {
            'reserved_4_full': persona_4_full_raw,
            'reserved_2_split': persona_2_split_raw,
            'mixed_seats': mixed_seats_raw
        }
        
        # Update total raw demands
        demands['reserved_4_full'] += persona_4_full_raw
        demands['reserved_2_split'] += persona_2_split_raw
        demands['mixed_seats'] += mixed_seats_raw
    
    # Store raw demands for debugging
    raw_demands = {
        'reserved_4_full': demands['reserved_4_full'],
        'reserved_2_split': demands['reserved_2_split'],
        'mixed_seats': demands['mixed_seats']
    }
    
    # Apply utilization factor to all seating types
    # This represents how efficiently we can fill tables on average due to:
    # - Partial table fills (e.g. 3 people at a 4-top)
    # - Time gaps between groups
    # - Scheduling inefficiencies
    utilization_factor = 0.8
    
    # Scale all demands by utilization factor
    demands['reserved_4_full'] *= utilization_factor
    demands['reserved_2_split'] *= utilization_factor
    demands['mixed_seats'] = int(demands['mixed_seats'] * utilization_factor)
    
    # Debug output to verify calculations
    print(f"\nDemand Calculation Debug for {M} members:")
    print(f"Raw demands (before utilization factor):")
    print(f"  Reserved 4-top (full): {raw_demands['reserved_4_full']}")
    print(f"  Reserved 2-person: {raw_demands['reserved_2_split']}")
    print(f"  Mixed seats: {raw_demands['mixed_seats']}")
    print(f"\nFinal demands:")
    print(f"  Reserved 4-top (full): {demands['reserved_4_full']} (no scaling)")
    print(f"  Reserved 2-person: {demands['reserved_2_split']} (no scaling)")
    print(f"  Mixed seats: {demands['mixed_seats']} (utilization factor: {utilization_factor})")
    
    return demands

def can_accommodate(M, time_blocks=TIME_BLOCKS_PER_MONTH):
    """Check if we can accommodate M members with current capacity
    
    Args:
        M: Number of members to accommodate
        time_blocks: Number of 3-hour blocks during operating hours
                    Weekdays: 5PM-11PM (2 blocks/day * 5 days = 10 blocks/week)
                    Weekends: 9AM-11PM (~4.67 blocks/day * 2 days = 9 blocks/week)
                    Total: ~82 blocks/month
    """
    demands = compute_demands(M)
    
    # Capacity constants
    NUM_4_TOP = 6  # Number of 4-top tables
    NUM_8_TOP = 3  # Number of 8-top tables
    
    # Create optimization model
    model = pulp.LpProblem("Seating_Optimization", pulp.LpMinimize)
    
    # Decision variables for table allocation
    reserved_4_full = pulp.LpVariable("reserved_4_full", 0, NUM_4_TOP)  # 4-top tables used fully
    reserved_4_split = pulp.LpVariable("reserved_4_split", 0, NUM_4_TOP)  # 4-top tables split into 2-tops
    mixed_4_full = pulp.LpVariable("mixed_4_full", 0, NUM_4_TOP)  # 4-top tables for mixed seating (full)
    mixed_4_split = pulp.LpVariable("mixed_4_split", 0, NUM_4_TOP)  # 4-top tables for mixed seating (split)
    mixed_8 = pulp.LpVariable("mixed_8", 0, NUM_8_TOP)  # 8-top tables for mixed seating
    
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
            reserved_4_full +
            (1 + split_penalty) * reserved_4_split
        ) +
        # Mixed seating terms (lower weights to encourage usage)
        mixed_weight * (
            mixed_4_full +
            (1 + split_penalty) * mixed_4_split +
            1.2 * mixed_8  # Slightly higher weight for 8-tops
        )
    )
    
    # Constraints
    
    # Scale monthly demands to per-block requirements
    # Note: With 3-hour blocks, most groups will use the full block
    # Turnover within a block is rare since:
    # 1. Setup/cleanup time between groups
    # 2. Most games take 1-3 hours
    # 3. Reservations are for the full block
    turnover_factor = 1  # Each table typically serves 1 group per 3-hour block
    
    # Convert monthly demands to per-block requirements
    reserved_4_per_block = demands['reserved_4_full'] / time_blocks  # No turnover for reservations
    reserved_2_per_block = demands['reserved_2_split'] / time_blocks  # No turnover for reservations
    
    # For mixed seating, allow some flexibility but still mostly 1 group per block
    mixed_demand_per_block = demands['mixed_seats'] / (time_blocks * turnover_factor)
    
    # Meet reservation demands
    model += reserved_4_full >= reserved_4_per_block
    model += reserved_4_split * 2 >= reserved_2_per_block  # Each split table serves 2 groups
    
    # Meet mixed seating demand with more flexible constraints
    model += (
        mixed_4_full * 4 +  # Each full 4-top serves 4 people
        mixed_4_split * 2 +  # Each split 4-top serves 2 people
        mixed_8 * 8  # Each 8-top serves 8 people
    ) >= mixed_demand_per_block

    # Soft targets for distribution (using <= instead of == to allow flexibility)
    model += mixed_4_full * 4 <= 0.5 * mixed_demand_per_block  # Target ~40-50% on full 4-tops
    model += mixed_4_split * 2 <= 0.4 * mixed_demand_per_block  # Target ~30-40% on split 4-tops
    model += mixed_8 * 8 <= 0.3 * mixed_demand_per_block  # Target ~20-30% on 8-tops
    
    # Table capacity constraints - ensure total tables used doesn't exceed capacity
    # For 4-top tables
    model += (reserved_4_full + reserved_4_split + 
             mixed_4_full + mixed_4_split) <= NUM_4_TOP
    # For 8-top tables
    model += mixed_8 <= NUM_8_TOP

    # Solve the model
    model.solve()

    # Check if solution exists and is optimal
    if pulp.LpStatus[model.status] == 'Optimal':
        results = {
            'tables': {
                'reserved_4_full': reserved_4_full.value(),
                'reserved_4_split': reserved_4_split.value(),
                'mixed_4_full': mixed_4_full.value(),
                'mixed_4_split': mixed_4_split.value(),
                'mixed_8': mixed_8.value()
            },
            'demands': demands,
            'time_blocks': time_blocks
        }
        
        # Calculate utilization rates
        four_top_util = (results['tables']['reserved_4_full'] + 
                       results['tables']['reserved_4_split'] + 
                       results['tables']['mixed_4_full'] + 
                       results['tables']['mixed_4_split'])/NUM_4_TOP * 100
        eight_top_util = results['tables']['mixed_8']/NUM_8_TOP * 100
        
        # Return True if neither table type exceeds capacity
        if four_top_util <= 100 and eight_top_util <= 100:
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
        
        # Calculate tables needed per block
        # Note: With 3-hour blocks, most groups use the full block duration
        # - Setup/cleanup time between groups
        # - Most games take 1-3 hours
        # - Reservations are for the full block
        
        # For 4-tops: count full tables and half for split tables
        # No turnover factor since each reservation takes the full block
        four_top_tables = (demands['reserved_4_full'] + demands['reserved_2_split']/2) / TIME_BLOCKS_PER_MONTH
        
        # For mixed seating: assume average 4 seats per table
        # Allow some flexibility in mixed seating but still mostly 1 group per block
        mixed_tables_needed = demands['mixed_seats'] / (4 * TIME_BLOCKS_PER_MONTH)  # Convert to tables per block
        
        total_tables_needed = four_top_tables + mixed_tables_needed
        capacity_used = (total_tables_needed / total_tables) * 100  # Will be ~2x higher due to turnover_factor
        
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
            
                print("\nTable Usage (per 3-hour block):")
                print("-" * 40)
                print("4-top tables:")
                if 'tables' in results:
                    print(f"Full reservations: {results['tables']['reserved_4_full']:.1f} tables")
                    print(f"Split reservations: {results['tables']['reserved_4_split']:.1f} tables ({results['tables']['reserved_4_split']*2:.1f} 2-person slots)")
                    print(f"Mixed seating (full): {results['tables']['mixed_4_full']:.1f} tables ({results['tables']['mixed_4_full']*4:.1f} seats)")
                    print(f"Mixed seating (split): {results['tables']['mixed_4_split']:.1f} tables ({results['tables']['mixed_4_split']*2:.1f} seats)")
                    print("\n8-top tables:")
                    print(f"Mixed seating: {results['tables']['mixed_8']:.1f} tables ({results['tables']['mixed_8']*8:.1f} seats)")
                
                print("\nOperating Hours:")
                print("-" * 20)
                print("Weekdays: 5PM-11PM (2 blocks/day * 5 days = 10 blocks/week)")
                print("Weekends: 9AM-11PM (~4.67 blocks/day * 2 days = 9 blocks/week)")
                print(f"Total blocks per month: {TIME_BLOCKS_PER_MONTH}")
            
            print("\nBy Persona Type:")
            print("-" * 20)
            for persona_type, type_demands in demands['type_demands'].items():
                print(f"\n{persona_type.title()}:")
                print(f"  Full 4-top reservations needed: {type_demands['reserved_4_full']:.1f}")
                print(f"  2-person reservations needed: {type_demands['reserved_2_split']:.1f}")
                print(f"  Mixed seats needed: {type_demands['mixed_seats']:.1f}")
            
            print("\nUtilization Rates:")
            print("-" * 20)
            # Calculate utilization rates
            four_top_util = ((results['tables']['reserved_4_full'] + results['tables']['reserved_4_split'] + 
                           results['tables']['mixed_4_full'] + results['tables']['mixed_4_split'])/6) * 100
            eight_top_util = (results['tables']['mixed_8']/3) * 100
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

import pulp

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
        
        # Calculate this persona's specific contributions
        persona_4_full = reserved_visits * (1 if avg_group_size > 2 else 0)
        persona_2_split = reserved_visits * (1 if avg_group_size <= 2 else 0)
        mixed_seats = mixed_visits * avg_group_size  # seats needed per month
        
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

def can_accommodate(M, time_blocks=72):
    """Check if we can accommodate M members with current capacity"""
    demands = compute_demands(M)
    
    # Capacity constants
    NUM_4_TOP = 6  # Number of 4-top tables
    NUM_8_TOP = 3  # Number of 8-top tables
    
    # Create optimization model
    model = pulp.LpProblem("Seating_Optimization", pulp.LpMinimize)
    
    # Decision variables for table allocation
    # Each variable represents number of tables used in each time block
    reserved_4_full = pulp.LpVariable("reserved_4_full", 0, NUM_4_TOP)  # 4-top tables used fully
    reserved_4_split = pulp.LpVariable("reserved_4_split", 0, NUM_4_TOP)  # 4-top tables split into 2-tops
    mixed_4_full = pulp.LpVariable("mixed_4_full", 0, NUM_4_TOP)  # 4-top tables for mixed seating (full)
    mixed_4_split = pulp.LpVariable("mixed_4_split", 0, NUM_4_TOP)  # 4-top tables for mixed seating (split)
    mixed_8 = pulp.LpVariable("mixed_8", 0, NUM_8_TOP)  # 8-top tables for mixed seating
    
    # Objective: Maximize efficient table usage
    # Prefer:
    # 1. Full 4-tops for reservations (weight: 1)
    # 2. Split 4-tops for reservations when needed (weight: 2)
    # 3. Full 4-tops for mixed seating (weight: 3)
    # 4. Split 4-tops for mixed seating when needed (weight: 4)
    # 5. 8-tops for large mixed groups (weight: 5)
    model += (reserved_4_full + 
             2 * reserved_4_split + 
             3 * mixed_4_full +
             4 * mixed_4_split +
             5 * mixed_8)
    
    # Constraints
    
    # Meet demand for reserved tables (monthly)
    # Each full 4-top provides 72 slots per month
    # Each split 4-top provides 144 two-person slots per month
    model += reserved_4_full * time_blocks >= demands['reserved_4_full']
    model += reserved_4_split * time_blocks * 2 >= demands['reserved_2_split']
    
    # Meet demand for mixed seats (monthly)
    # Each full 4-top provides 288 seats per month (4 seats * 72 blocks)
    # Each split 4-top provides 144 seats per month (2 seats * 72 blocks)
    # Each 8-top provides 576 seats per month (8 seats * 72 blocks)
    model += (mixed_4_full * time_blocks * 4 + 
             mixed_4_split * time_blocks * 2 + 
             mixed_8 * time_blocks * 8) >= demands['mixed_seats']
    
    # Table capacity constraints
    model += reserved_4_full + reserved_4_split + mixed_4_full + mixed_4_split <= NUM_4_TOP
    model += mixed_8 <= NUM_8_TOP
    
    # Solve the model
    model.solve()
    
    # Check if solution exists and is optimal
    if pulp.LpStatus[model.status] == 'Optimal':
        results = {
            'reserved_4_full': reserved_4_full.value(),
            'reserved_4_split': reserved_4_split.value(),
            'mixed_4_full': mixed_4_full.value(),
            'mixed_4_split': mixed_4_split.value(),
            'mixed_8': mixed_8.value(),
            'demands': demands
        }
        
        # Calculate utilization rates
        four_top_util = (results['reserved_4_full'] + results['reserved_4_split'] + 
                        results['mixed_4_full'] + results['mixed_4_split'])/NUM_4_TOP * 100
        eight_top_util = results['mixed_8']/NUM_8_TOP * 100
        
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
        
        # Calculate tables needed
        # For 4-tops: count full tables and half for split tables
        four_top_tables = (demands['reserved_4_full'] + demands['reserved_2_split']/2)/72
        # For mixed: assume optimal filling (8 seats per table)
        mixed_tables_needed = demands['mixed_seats']/(8 * 72)
        
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
        
        if can_fit:
            print(f"✓ Can accommodate {M} members!")
            
            demands = results['demands']
            
            print("\nTable Usage Summary:")
            print("-" * 20)
            print("4-top tables:")
            print(f"Full reservations: {results['reserved_4_full']:.1f} tables")
            print(f"Split reservations: {results['reserved_4_split']:.1f} tables ({results['reserved_4_split']*2:.1f} 2-person slots)")
            print(f"Mixed seating (full): {results['mixed_4_full']:.1f} tables ({results['mixed_4_full']*4:.1f} seats)")
            print(f"Mixed seating (split): {results['mixed_4_split']:.1f} tables ({results['mixed_4_split']*2:.1f} seats)")
            
            print("\n8-top tables:")
            print(f"Mixed seating: {results['mixed_8']:.1f} tables ({results['mixed_8']*8:.1f} seats)")
            
            print("\nBy Persona Type:")
            print("-" * 20)
            for persona_type, type_demands in demands['type_demands'].items():
                print(f"\n{persona_type.title()}:")
                print(f"  Full 4-top reservations needed: {type_demands['reserved_4_full']:.1f}")
                print(f"  2-person reservations needed: {type_demands['reserved_2_split']:.1f}")
                print(f"  Mixed seats needed: {type_demands['mixed_seats']:.1f}")
            
            print("\nUtilization Rates:")
            print("-" * 20)
            four_top_util = (results['reserved_4_full'] + results['reserved_4_split'] + 
                           results['mixed_4_full'] + results['mixed_4_split'])/6 * 100
            eight_top_util = results['mixed_8']/3 * 100
            print(f"4-top tables: {four_top_util:.1f}%")
            print(f"8-top tables: {eight_top_util:.1f}%")
        else:
            print(f"✗ Cannot accommodate {M} members")
            demands = compute_demands(M)
            
            print("\nDemands that couldn't be met:")
            print("-" * 20)
            print(f"Full 4-top reservations needed: {demands['reserved_4_full']/72:.1f}")
            print(f"2-person reservations needed: {demands['reserved_2_split']/72:.1f}")
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
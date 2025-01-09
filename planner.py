import pulp
import math

# Table capacity constants
NUM_4_TOP = 8  # Number of 4-top tables (can split into 2x2)
NUM_8_TOP = 3  # Number of 8-top tables (can split into 4+2)
NUM_6_TOP = 2  # Number of 6-top tables (can split into 3x2 or 4+2)
NUM_2_TOP = 2  # Number of 2-top tables (fixed)

# Time block constants (3-hour blocks)
# Weekday blocks (M-F):
# - Operating hours 5PM-11PM: 6hrs/day ÷ 3hr blocks = 2 blocks/day × 5 days = 10 blocks/week
WEEKDAY_BLOCKS = 10  # 2 blocks/day * 5 days

# Weekend blocks (S-S):
# - Operating hours 9AM-11PM: 14hrs/day ÷ 3hr blocks ≈ 4.67 blocks/day × 2 days ≈ 9 blocks/week
WEEKEND_BLOCKS = 9  # ~4.67 blocks/day * 2 days

# Calculate total 3-hour blocks per month (assuming 4.33 weeks/month)
# Weekdays: 5PM-11PM (2 blocks/day * 5 days = 10 blocks/week)
# Weekends: 9AM-11PM (4 blocks/day * 2 days = 8 blocks/week)
# Total: ~82 blocks/month
TIME_BLOCKS_PER_MONTH = int((WEEKDAY_BLOCKS + WEEKEND_BLOCKS) * 4.33)  # ~82 blocks/month

# Total monthly table capacity
MONTHLY_4_TOP_BLOCKS = NUM_4_TOP * TIME_BLOCKS_PER_MONTH  # 8 * 82 = 656 blocks
MONTHLY_8_TOP_BLOCKS = NUM_8_TOP * TIME_BLOCKS_PER_MONTH  # 3 * 82 = 246 blocks
MONTHLY_6_TOP_BLOCKS = NUM_6_TOP * TIME_BLOCKS_PER_MONTH  # 2 * 82 = 164 blocks
MONTHLY_2_TOP_BLOCKS = NUM_2_TOP * TIME_BLOCKS_PER_MONTH  # 2 * 82 = 164 blocks

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
    'casual': 0.25,
    'students': 0.05,
    'families': 0.4,
    'hobbyists': 0.25,
    'everyday': 0.05
}

# Persona prices, guests, and visit mixes
PERSONAS = {
    'casual': {
        'price': 20,
        'guests_per_month': 6,
        'reserved_visits': 3,
        'mixed_visits': 1,
        'game_checkouts': 0,
        'avg_group_size': 4,
    },
    'everyday': {
        'price': 5,
        'guests_per_month': 3,
        'reserved_visits': 8,
        'mixed_visits': 4,
        'game_checkouts': 2,
        'avg_group_size': 4,
    },
    'families': {
        'price': 15,
        'guests_per_month': 2.5,
        'reserved_visits': 3,
        'mixed_visits': 2,
        'game_checkouts': 1,
        'avg_group_size': 4,
    },
    'hobbyists': {
        'price': 10,
        'guests_per_month': 3,
        'reserved_visits': 4,
        'mixed_visits': 2,
        'game_checkouts': 2,
        'avg_group_size': 4,
    },
    'students': {
        'price': 5,
        'guests_per_month': 3,
        'reserved_visits': 8,
        'mixed_visits': 1,
        'game_checkouts': 1,
        'avg_group_size': 3,
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
    
    # Initialize monthly demands
    monthly_demands = {
        'reserved_8_blocks': 0,    # Number of 8-top blocks needed
        'reserved_6_blocks': 0,    # Number of 6-top blocks needed
        'reserved_4_blocks': 0,    # Number of 4-top blocks needed
        'reserved_2_blocks': 0,    # Number of 2-person blocks needed
        'mixed_seat_blocks': 0,    # Number of individual seat blocks needed
        'type_demands': {}       # Per-persona type demands
    }
    
    print(f"\nDetailed Demand Analysis for {M} members:")
    print("=" * 50)
    
    # For each persona type
    for persona_type, pct in distribution.items():
        member_count = int(M * pct)  # Integer number of members
        persona = personas[persona_type]
        
        # Calculate total monthly reserved blocks (1 visit = 1 block)
        monthly_reserved_visits = member_count * persona['reserved_visits']
        monthly_reserved_blocks = monthly_reserved_visits  # Each visit takes one block
        
        # For reserved visits, calculate group size (member + guests)
        group_size = 1 + persona['guests_per_month']  # member + average guests
        
        print(f"\n{persona_type.title()}:")
        print(f"  Members: {member_count}")
        print(f"  Reserved visits per month: {monthly_reserved_visits}")
        print(f"  Monthly blocks needed: {monthly_reserved_blocks}")
        print(f"  Group size (member + {persona['guests_per_month']} guests): {group_size}")
        
        # Determine table blocks needed based on group size
        if group_size <= 2:
            monthly_demands['reserved_2_blocks'] += monthly_reserved_blocks
            print(f"  → Needs {monthly_reserved_blocks} 2-top blocks")
        elif group_size <= 4:
            monthly_demands['reserved_4_blocks'] += monthly_reserved_blocks
            print(f"  → Needs {monthly_reserved_blocks} 4-top blocks")
        elif group_size <= 6:
            monthly_demands['reserved_6_blocks'] += monthly_reserved_blocks
            print(f"  → Needs {monthly_reserved_blocks} 6-top blocks")
        else:  # group_size <= 8
            monthly_demands['reserved_8_blocks'] += monthly_reserved_blocks
            print(f"  → Needs {monthly_reserved_blocks} 8-top blocks")
        
        # Calculate mixed seating demand (1 seat per person, no guests)
        monthly_mixed_visits = member_count * persona['mixed_visits']
        monthly_mixed_blocks = monthly_mixed_visits  # Each mixed visit takes one block
        monthly_demands['mixed_seat_blocks'] += monthly_mixed_blocks
        print(f"  Mixed visits per month: {monthly_mixed_visits}")
        print(f"  Mixed blocks needed: {monthly_mixed_blocks} (1 seat each)")
        
        # Store per-persona demands
        monthly_demands['type_demands'][persona_type] = {
            'reserved_8_blocks': monthly_reserved_blocks if group_size > 6 else 0,
            'reserved_6_blocks': monthly_reserved_blocks if 4 < group_size <= 6 else 0,
            'reserved_4_blocks': monthly_reserved_blocks if 2 < group_size <= 4 else 0,
            'reserved_2_blocks': monthly_reserved_blocks if group_size <= 2 else 0,
            'mixed_seat_blocks': monthly_mixed_blocks
        }
    
    print("\nTotal Monthly Block Demands:")
    print("-" * 30)
    print(f"Reserved 8-tops: {monthly_demands['reserved_8_blocks']} blocks ({monthly_demands['reserved_8_blocks']/MONTHLY_8_TOP_BLOCKS*100:.1f}% of capacity)")
    print(f"Reserved 6-tops: {monthly_demands['reserved_6_blocks']} blocks ({monthly_demands['reserved_6_blocks']/MONTHLY_6_TOP_BLOCKS*100:.1f}% of capacity)")
    print(f"Reserved 4-tops: {monthly_demands['reserved_4_blocks']} blocks ({monthly_demands['reserved_4_blocks']/MONTHLY_4_TOP_BLOCKS*100:.1f}% of capacity)")
    print(f"Reserved 2-tops: {monthly_demands['reserved_2_blocks']} blocks ({monthly_demands['reserved_2_blocks']/MONTHLY_2_TOP_BLOCKS*100:.1f}% of capacity)")
    print(f"Mixed seats: {monthly_demands['mixed_seat_blocks']} seat blocks")
    
    return monthly_demands

def can_accommodate(M):
    """Check if we can accommodate M members with current monthly capacity"""
    demands = compute_demands(M)
    
    # Create optimization model
    model = pulp.LpProblem("Seating_Optimization", pulp.LpMinimize)
    
    # Decision variables for monthly block allocation
    # 4-top tables (8 tables * 82 blocks = 656 blocks/month)
    reserved_4_full = pulp.LpVariable("reserved_4_full", 0, MONTHLY_4_TOP_BLOCKS, cat='Integer')  # Used as full 4-tops
    reserved_4_split = pulp.LpVariable("reserved_4_split", 0, MONTHLY_4_TOP_BLOCKS, cat='Integer')  # Split into 2x2
    mixed_4_full = pulp.LpVariable("mixed_4_full", 0, MONTHLY_4_TOP_BLOCKS, cat='Integer')  # Used as full 4-tops for mixed
    mixed_4_split = pulp.LpVariable("mixed_4_split", 0, MONTHLY_4_TOP_BLOCKS, cat='Integer')  # Split into 2x2 for mixed
    
    # 8-top tables (3 tables * 82 blocks = 246 blocks/month)
    reserved_8_full = pulp.LpVariable("reserved_8_full", 0, MONTHLY_8_TOP_BLOCKS, cat='Integer')  # Used as full 8-tops
    reserved_8_split = pulp.LpVariable("reserved_8_split", 0, MONTHLY_8_TOP_BLOCKS, cat='Integer')  # Split into 4+2
    mixed_8_full = pulp.LpVariable("mixed_8_full", 0, MONTHLY_8_TOP_BLOCKS, cat='Integer')  # Used as full 8-tops for mixed
    mixed_8_split = pulp.LpVariable("mixed_8_split", 0, MONTHLY_8_TOP_BLOCKS, cat='Integer')  # Split into 4+2 for mixed
    
    # 6-top tables (2 tables * 82 blocks = 164 blocks/month)
    reserved_6_full = pulp.LpVariable("reserved_6_full", 0, MONTHLY_6_TOP_BLOCKS, cat='Integer')  # Used as full 6-tops
    reserved_6_split_3x2 = pulp.LpVariable("reserved_6_split_3x2", 0, MONTHLY_6_TOP_BLOCKS, cat='Integer')  # Split into 3x2
    reserved_6_split_4_2 = pulp.LpVariable("reserved_6_split_4_2", 0, MONTHLY_6_TOP_BLOCKS, cat='Integer')  # Split into 4+2
    mixed_6_full = pulp.LpVariable("mixed_6_full", 0, MONTHLY_6_TOP_BLOCKS, cat='Integer')  # Used as full 6-tops for mixed
    mixed_6_split_3x2 = pulp.LpVariable("mixed_6_split_3x2", 0, MONTHLY_6_TOP_BLOCKS, cat='Integer')  # Split into 3x2 for mixed
    mixed_6_split_4_2 = pulp.LpVariable("mixed_6_split_4_2", 0, MONTHLY_6_TOP_BLOCKS, cat='Integer')  # Split into 4+2 for mixed
    
    # 2-top tables (2 tables * 82 blocks = 164 blocks/month)
    reserved_2 = pulp.LpVariable("reserved_2", 0, MONTHLY_2_TOP_BLOCKS, cat='Integer')  # Used for 2-person reservations
    mixed_2 = pulp.LpVariable("mixed_2", 0, MONTHLY_2_TOP_BLOCKS, cat='Integer')  # Used for mixed seating
    
    # Objective: Balance table usage between reserved and mixed seating
    # 1. Reserved seating gets priority
    reserved_weight = 1.0
    # 2. Mixed seating fills remaining capacity
    mixed_weight = 1.0
    # 3. Small penalty for splitting tables (to prefer keeping tables whole when possible)
    split_penalty = 0.1
    
    model += (
        # Reserved seating terms
        reserved_weight * (
            # 4-tops
            reserved_4_full +
            (1 + split_penalty) * reserved_4_split +
            # 8-tops
            1.2 * reserved_8_full +
            (1.2 + split_penalty) * reserved_8_split +
            # 6-tops
            1.1 * reserved_6_full +
            (1.1 + split_penalty) * (reserved_6_split_3x2 + reserved_6_split_4_2) +
            # 2-tops
            0.8 * reserved_2
        ) +
        # Mixed seating terms (lower weights to encourage usage)
        mixed_weight * (
            # 4-tops
            mixed_4_full +
            (1 + split_penalty) * mixed_4_split +
            # 8-tops
            1.2 * mixed_8_full +
            (1.2 + split_penalty) * mixed_8_split +
            # 6-tops
            1.1 * mixed_6_full +
            (1.1 + split_penalty) * (mixed_6_split_3x2 + mixed_6_split_4_2) +
            # 2-tops
            0.8 * mixed_2
        )
    )
    
    # Monthly capacity constraints
    # 4-top tables
    model += (reserved_4_full + reserved_4_split + 
             mixed_4_full + mixed_4_split) <= MONTHLY_4_TOP_BLOCKS, "4_top_capacity"
             
    # 8-top tables
    model += (reserved_8_full + reserved_8_split +
             mixed_8_full + mixed_8_split) <= MONTHLY_8_TOP_BLOCKS, "8_top_capacity"
             
    # 6-top tables
    model += (reserved_6_full + reserved_6_split_3x2 + reserved_6_split_4_2 +
             mixed_6_full + mixed_6_split_3x2 + mixed_6_split_4_2) <= MONTHLY_6_TOP_BLOCKS, "6_top_capacity"
             
    # 2-top tables
    model += (reserved_2 + mixed_2) <= MONTHLY_2_TOP_BLOCKS, "2_top_capacity"
    
    # Meet monthly reservation demands
    # Each group size can be accommodated by its size table or larger
    # 8-person groups
    model += reserved_8_full >= demands['reserved_8_blocks'], "8_person_demand"
    
    # 6-person groups (can use 8-tops or 6-tops)
    model += (reserved_6_full + 
             reserved_8_split) >= demands['reserved_6_blocks'], "6_person_demand"
    
    # 4-person groups (can use 4-tops, 6-tops, or 8-tops)
    model += (reserved_4_full + 
             reserved_6_split_4_2 +
             reserved_8_split) >= demands['reserved_4_blocks'], "4_person_demand"
    
    # 2-person groups (can use 2-tops or split tables)
    model += (reserved_2 +
             2 * reserved_4_split +
             2 * reserved_6_split_3x2 +
             reserved_6_split_4_2 +
             reserved_8_split) >= demands['reserved_2_blocks'], "2_person_demand"
    
    # Mixed seating demand (can use any table configuration)
    model += (
        # Full tables
        4 * mixed_4_full +
        8 * mixed_8_full +
        6 * mixed_6_full +
        2 * mixed_2 +
        # Split tables
        2 * mixed_4_split +  # 2x2
        (3 + 3) * mixed_6_split_3x2 +  # 3x2
        (4 + 2) * mixed_6_split_4_2 +  # 4+2
        (4 + 2) * mixed_8_split  # 4+2
    ) >= demands['mixed_seat_blocks'], "mixed_seating_demand"
    
    # Solve the optimization problem
    model.solve()
    
    # Check if a solution was found
    if pulp.LpStatus[model.status] == 'Optimal':
        return True, None
    else:
        return False, None

def analyze_bottleneck(M):
    """Analyze what's causing capacity issues at M members"""
    demands = compute_demands(M)
    
    # Calculate utilization percentages
    utilization = {
        '8_top': demands['reserved_8_blocks'] / MONTHLY_8_TOP_BLOCKS * 100,
        '6_top': demands['reserved_6_blocks'] / MONTHLY_6_TOP_BLOCKS * 100,
        '4_top': demands['reserved_4_blocks'] / MONTHLY_4_TOP_BLOCKS * 100,
        '2_top': demands['reserved_2_blocks'] / MONTHLY_2_TOP_BLOCKS * 100
    }
    
    # Find the highest utilization
    max_util = max(utilization.values())
    bottlenecks = [size for size, util in utilization.items() if util > 80]
    
    if bottlenecks:
        return f"High utilization ({max_util:.1f}%) of {', '.join(bottlenecks)} tables"
    else:
        return "No clear bottleneck identified"

def generate_summary(test_members, results):
    """Generate a summary of capacity analysis results"""
    summary = []
    summary.append("Capacity Analysis Overview")
    summary.append("=" * 30)
    summary.append("")
    
    # Find maximum viable membership
    max_viable = None
    for M, can_fit in results:
        if can_fit:
            max_viable = M
    
    if max_viable:
        summary.append(f"Maximum Viable Membership: {max_viable}")
        bottleneck = analyze_bottleneck(max_viable + 50)
        summary.append(f"Limiting Factor: {bottleneck}")
    else:
        summary.append("Error: Could not determine maximum viable membership")
    
    summary.append("")
    summary.append("Detailed Results:")
    for M, can_fit in results:
        status = "✓" if can_fit else "✗"
        summary.append(f"{status} {M:4d} members")
    
    return "\n".join(summary)

def analyze_capacity():
    """Analyze capacity and determine optimal member count"""
    test_members = [200, 250, 300, 350, 400]
    results = []
    
    print("Running Capacity Analysis")
    print("=" * 30)
    
    for M in test_members:
        print(f"\nTesting {M} members...")
        can_fit, _ = can_accommodate(M)
        results.append((M, can_fit))
        print(f"Can accommodate {M} members: {'Yes' if can_fit else 'No'}")
        
        if can_fit:
            # Set the member count for value calculations
            global MEMBER_COUNT
            MEMBER_COUNT = M
    
    print("\nCapacity Analysis Complete")
    print("=" * 30)
    print(generate_summary(test_members, results))

def calculate_plan_value(plan_type):
    """Calculate the value and features of a membership plan"""
    if plan_type == 'basic':
        return {
            'price': BASIC_PLAN_PRICE,
            'features': {
                'guest_passes': 2,
                'mixed_access': False,
                'game_checkouts': 0
            }
        }
    elif plan_type == 'standard':
        return {
            'price': STANDARD_PLAN_PRICE,
            'features': {
                'guest_passes': 4,
                'mixed_access': True,
                'game_checkouts': 2
            }
        }
    elif plan_type == 'family':
        return {
            'price': FAMILY_PLAN_PRICE,
            'features': {
                'guest_passes': 8,
                'mixed_access': True,
                'game_checkouts': 4
            }
        }
    else:
        raise ValueError(f"Unknown plan type: {plan_type}")

def get_plan_features(plan_type):
    """Get list of features for a plan type"""
    plan = calculate_plan_value(plan_type)
    features = []
    
    if plan['features']['guest_passes'] > 0:
        features.append(f"{plan['features']['guest_passes']} guest passes per month")
    if plan['features']['mixed_access']:
        features.append("Access to mixed events")
    if plan['features']['game_checkouts'] > 0:
        features.append(f"{plan['features']['game_checkouts']} game checkouts per month")
    
    return features

def calculate_total_guests(persona_type):
    """Calculate total monthly guests for a persona type"""
    persona = PERSONAS[persona_type]
    return persona['guests_per_month'] * persona['reserved_visits']

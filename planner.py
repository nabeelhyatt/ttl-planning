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
    'casual': 0.253,
    'everyday': 0.106,
    'families': 0.266,
    'hobbyists': 0.16,
    'students': 0.214,
}

# Persona prices, guests, and visit mixes
PERSONAS = {
    'casual': {
        'price': 5,   # price willing to pay per visit
        'guests_per_month': 1,   # Average guests brought per month
        'reserved_visits': 1,    # visits/month
        'mixed_visits': 1,       # mixed visits/month
        'game_checkouts': 0,     # game checkouts per month
        'avg_group_size': 2      # member + average guests
    },
    'everyday': {
        'price': 5,   # price willing to pay per visit
        'guests_per_month': 3,   # Assumes 3 guests for a 4-top
        'reserved_visits': 8,    # visits/month
        'mixed_visits': 4,       # mixed event visits/month
        'game_checkouts': 2,     # game checkouts per month
        'avg_group_size': 4      # member + average guests
    },
    'families': {
        'price': 15,   # price willing to pay per visit
        'guests_per_month': 2.5, # Average between solo parent (2 kids) and family visit (3 family)
        'reserved_visits': 3,    # visits/month
        'mixed_visits': 2,       # mixed visits/month
        'game_checkouts': 1,     # game checkouts per month
        'avg_group_size': 4      # member + average guests
    },
    'hobbyists': {
        'price': 10,   # price willing to pay per visit
        'guests_per_month': 3,   # Assumes 3 guests for a 4-top
        'reserved_visits': 4,    # visits/month
        'mixed_visits': 2,       # mixed visits/month
        'game_checkouts': 2,     # game checkouts per month
        'avg_group_size': 4      # member + average guests
    },
    'students': {
        'price': 5,   # price willing to pay per visit
        'guests_per_month': 3,   # Assumes 3 guests for a 4-top
        'reserved_visits': 8,    # visits/month
        'mixed_visits': 1,       # mixed visits/month
        'game_checkouts': 1,     # game checkouts per month
        'avg_group_size': 3      # member + average guests
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
    
    # 2-person groups (can use 2-tops or split larger tables)
    model += (reserved_2 + 
             reserved_4_split * 2 +  # Each split 4-top gives two 2-person slots
             reserved_6_split_3x2 * 2 +  # Each split 6-top gives two 2-person slots
             reserved_8_split) >= demands['reserved_2_blocks'], "2_person_demand"
    
    # Meet mixed seating demand
    model += (
        # 4-tops contribution
        mixed_4_full * 4 + mixed_4_split * 2 +
        # 8-tops contribution
        mixed_8_full * 8 + mixed_8_split * 6 +
        # 6-tops contribution
        mixed_6_full * 6 + mixed_6_split_3x2 * 5 + mixed_6_split_4_2 * 6 +
        # 2-tops contribution
        mixed_2 * 2
    ) >= demands['mixed_seat_blocks'], "mixed_seating_demand"
    
    # Solve the model
    model.solve()

    # Check if solution exists and is optimal
    if pulp.LpStatus[model.status] == 'Optimal':
        results = {
            'tables': {
                # 4-tops
                'reserved_4_full': reserved_4_full.value(),
                'reserved_4_split': reserved_4_split.value(),
                'mixed_4_full': mixed_4_full.value(),
                'mixed_4_split': mixed_4_split.value(),
                # 8-tops
                'reserved_8_full': reserved_8_full.value(),
                'reserved_8_split': reserved_8_split.value(),
                'mixed_8_full': mixed_8_full.value(),
                'mixed_8_split': mixed_8_split.value(),
                # 6-tops
                'reserved_6_full': reserved_6_full.value(),
                'reserved_6_split_3x2': reserved_6_split_3x2.value(),
                'reserved_6_split_4_2': reserved_6_split_4_2.value(),
                'mixed_6_full': mixed_6_full.value(),
                'mixed_6_split_3x2': mixed_6_split_3x2.value(),
                'mixed_6_split_4_2': mixed_6_split_4_2.value(),
                # 2-tops
                'reserved_2': reserved_2.value(),
                'mixed_2': mixed_2.value()
            },
            'demands': demands
        }
        
        # Calculate utilization rates
        results['utilization'] = {
            '4_top': (results['tables']['reserved_4_full'] + 
                     results['tables']['reserved_4_split'] + 
                     results['tables']['mixed_4_full'] + 
                     results['tables']['mixed_4_split']) / MONTHLY_4_TOP_BLOCKS * 100,
            
            '8_top': (results['tables']['mixed_8_full'] / MONTHLY_8_TOP_BLOCKS) * 100,
            
            '6_top': (results['tables']['reserved_6_full'] +
                     results['tables']['reserved_6_split_3x2'] +
                     results['tables']['reserved_6_split_4_2'] +
                     results['tables']['mixed_6_full'] +
                     results['tables']['mixed_6_split_3x2'] +
                     results['tables']['mixed_6_split_4_2']) / MONTHLY_6_TOP_BLOCKS * 100,
            
            '2_top': (results['tables']['reserved_2'] +
                     results['tables']['mixed_2']) / MONTHLY_2_TOP_BLOCKS * 100
        }
        
        return True, results
    else:
        return False, None

def generate_summary(test_members, results_list):
    """Generate a high-level summary of capacity analysis"""
    max_feasible = 0
    bottleneck_info = {}
    
    for M in test_members:
        can_fit, results = can_accommodate(M)
        if can_fit:
            max_feasible = M
        else:
            demands = compute_demands(M)
            # Find which table type and persona is causing the bottleneck
            bottleneck = {'table_type': None, 'persona': None, 'utilization': 0, 'total_utilization': 0}
            
            # Calculate total demand across all personas
            total_4_top_demand = sum(
                type_demands['reserved_4_blocks'] + 
                type_demands['reserved_2_blocks']/2 + 
                type_demands['mixed_seat_blocks']/4
                for type_demands in demands['type_demands'].values()
            )
            total_utilization = (total_4_top_demand / MONTHLY_4_TOP_BLOCKS) * 100
            
            # Find which persona has highest individual demand
            for persona, type_demands in demands['type_demands'].items():
                persona_4_top_demand = (type_demands['reserved_4_blocks'] + 
                                    type_demands['reserved_2_blocks']/2 + 
                                    type_demands['mixed_seat_blocks']/4)
                utilization = (persona_4_top_demand / MONTHLY_4_TOP_BLOCKS) * 100
                if utilization > bottleneck['utilization']:
                    bottleneck['utilization'] = utilization
                    bottleneck['table_type'] = '4-top'
                    bottleneck['persona'] = persona
            
            bottleneck['total_utilization'] = total_utilization
            bottleneck_info[M] = bottleneck
            break  # We only need the first failing case
    
    summary = []
    summary.append("🎲 Capacity Analysis Overview")
    summary.append("=" * 35)
    summary.append("")  # Add spacing
    
    if max_feasible > 0:
        summary.append(f"✅ Maximum Feasible Members: {max_feasible}")
    else:
        summary.append("❌ Cannot accommodate even the minimum tested member count")
    
    first_fail = min([m for m in test_members if m > max_feasible], default=None)
    if first_fail and first_fail in bottleneck_info:
        bottleneck = bottleneck_info[first_fail]
        summary.append("")  # Add spacing
        summary.append(f"📊 Bottleneck at {first_fail} members:")
        summary.append(f"• Total Table Utilization: {bottleneck['total_utilization']:.1f}%")
        summary.append("")  # Add spacing
        summary.append("Highest Individual Impact:")
        summary.append(f"• Persona Type: {bottleneck['persona'].title()}")
        summary.append(f"• Their Utilization: {bottleneck['utilization']:.1f}%")
        summary.append(f"• Table Type: {bottleneck['table_type']}")
    
    return "\n".join(summary)

def analyze_capacity(test_members=[200, 250, 300, 350, 400]):
    """Analyze capacity for different member counts"""
    results = []
    for M in test_members:
        demands = compute_demands(M)
        if can_accommodate(M)[0]:
            results.append((M, True))
        else:
            results.append((M, False))
    
    # Generate and print the summary first
    summary = generate_summary(test_members, results)
    print(summary)
    
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
                    print(f"Mixed seating: {results['tables']['mixed_8_full']:.1f} tables ({results['tables']['mixed_8_full']*8:.1f} seats)")
                
                print("\nOperating Hours:")
                print("-" * 20)
                print("Weekdays: 5PM-11PM (2 blocks/day * 5 days = 10 blocks/week)")
                print("Weekends: 9AM-11PM (~4.67 blocks/day * 2 days = 9 blocks/week)")
                print(f"Total blocks per month: {TIME_BLOCKS_PER_MONTH}")
            
            print("\nBy Persona Type:")
            print("-" * 20)
            for persona_type, type_demands in demands['type_demands'].items():
                print(f"\n{persona_type.title()}:")
                print(f"  Full 4-top reservations needed: {type_demands['reserved_4_blocks']:.1f}")
                print(f"  2-person reservations needed: {type_demands['reserved_2_blocks']:.1f}")
                print(f"  Mixed seats needed: {type_demands['mixed_seat_blocks']:.1f}")
            
            print("\nUtilization Rates:")
            print("-" * 20)
            # Calculate utilization rates
            four_top_util = ((results['tables']['reserved_4_full'] + results['tables']['reserved_4_split'] + 
                           results['tables']['mixed_4_full'] + results['tables']['mixed_4_split'])/MONTHLY_4_TOP_BLOCKS) * 100
            eight_top_util = (results['tables']['mixed_8_full']/MONTHLY_8_TOP_BLOCKS) * 100
            print(f"4-top tables: {four_top_util:.1f}%")
            print(f"8-top tables: {eight_top_util:.1f}%")
            print(f"Overall: {(four_top_util * NUM_4_TOP + eight_top_util * NUM_8_TOP)/(NUM_4_TOP + NUM_8_TOP):.1f}%")
        else:
            print(f"✗ Cannot accommodate {M} members")
            demands = compute_demands(M)
            
            print("\nDemands that couldn't be met:")
            print("-" * 20)
            print(f"Full 4-top blocks needed: {demands['reserved_4_blocks']}")
            print(f"2-person blocks needed: {demands['reserved_2_blocks']}")
            print(f"Mixed seat blocks needed: {demands['mixed_seat_blocks']}")
            
            print("\nBy Persona Type:")
            print("-" * 20)
            for persona_type, type_demands in demands['type_demands'].items():
                print(f"\n{persona_type.title()}:")
                print(f"  Full 4-top blocks needed: {type_demands['reserved_4_blocks']}")
                print(f"  2-person blocks needed: {type_demands['reserved_2_blocks']}")
                print(f"  Mixed seat blocks needed: {type_demands['mixed_seat_blocks']}")
    
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

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
TIME_BLOCKS_PER_MONTH = int((WEEKDAY_BLOCKS + WEEKEND_BLOCKS) * 4.33)  # ~82 blocks/month

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
    # Initialize tracking variables
    total_4_tops_used = 0
    total_2_tops_used = 0
    total_mixed_seats = 0
    
    # Track maximum allowed tables (integer-based)
    MAX_4_TOPS = NUM_4_TOP  # 8 four-tops total
    MAX_2_TOPS = NUM_2_TOP  # 2 two-tops total
    MAX_MIXED_SEATS = (NUM_4_TOP * 4 + NUM_2_TOP * 2 + 
                      NUM_6_TOP * 6 + NUM_8_TOP * 8)  # Total seat capacity
    
    distribution = PERSONA_DISTRIBUTION
    personas = PERSONAS
    
    # Initialize demands
    demands = {
        'reserved_4_full': 0,    # Number of 4-top tables needed for 4-person reservations (monthly)
        'reserved_2_split': 0,   # Number of 2-person reservations that can share 4-top (monthly)
        'reserved_8_full': 0,    # Number of 8-top tables needed for large group reservations (monthly)
        'reserved_6_full': 0,    # Number of 6-top tables needed for medium group reservations (monthly)
        'mixed_seats': 0,        # Number of individual seats needed for mixed seating (monthly)
        'type_demands': {}
    }
    
    # For each persona type
    for persona_type, pct in distribution.items():
        member_count = M * pct
        persona = personas[persona_type]
        
        # Calculate per-block visit frequencies
        # Convert to per-block immediately to prevent overflow
        reserved_visits = member_count * persona['reserved_visits'] / TIME_BLOCKS_PER_MONTH  # visits per block
        mixed_visits = member_count * persona['mixed_visits'] / TIME_BLOCKS_PER_MONTH  # visits per block
        
        # Apply ceiling after table distribution to prevent accumulation of roundups
        
        # Calculate average group sizes
        avg_group_size = persona.get('avg_group_size', 2)
        
        # Calculate per-block table needs for reservations
        # Distribute between table sizes based on group size
        # Note: These are now per-block calculations
        if avg_group_size == 4:
            four_top_pct = 0.8  # 80% prefer 4-tops
        elif avg_group_size == 3:
            four_top_pct = 0.6  # 60% prefer 4-tops
        else:  # avg_group_size == 2
            four_top_pct = 0.2  # 20% prefer 4-tops (most use 2-tops)
            
        # Calculate per-block demands with better distribution
        # Distribute reserved visits based on group size and table availability
        if avg_group_size >= 7:  # Large groups prefer 8-tops but can use 6-tops
            persona_8_full_raw = min(reserved_visits * 0.5, NUM_8_TOP)  # Up to 50% to 8-tops
            remaining_after_8 = max(0, reserved_visits * 0.5)
            persona_6_full_raw = min(remaining_after_8 * 0.7, NUM_6_TOP)  # Up to 70% of remainder to 6-tops
            persona_4_full_raw = remaining_after_8 * 0.3  # Rest to 4-tops
            persona_2_split_raw = 0
        elif avg_group_size >= 5:  # Medium groups prefer 6-tops but can use 4-tops
            persona_8_full_raw = 0  # Don't use 8-tops for medium groups
            persona_6_full_raw = min(reserved_visits * 0.6, NUM_6_TOP)  # Up to 60% to 6-tops
            persona_4_full_raw = reserved_visits * 0.4  # Rest to 4-tops
            persona_2_split_raw = 0
        else:  # Small groups use 4-tops and 2-tops
            persona_8_full_raw = 0
            persona_6_full_raw = 0
            
            # Calculate scaled demand for this persona (limit to 1-2 tables per persona)
            max_tables_per_persona = 2  # Limit each persona to at most 2 tables of each type
            total_tables_needed = min(reserved_visits, max_tables_per_persona)
            
            # Calculate maximum available tables considering global limits
            max_4_tops_available = min(
                2,  # Max 2 tables per persona
                MAX_4_TOPS - total_4_tops_used  # Remaining global capacity
            )
            max_2_tops_available = min(
                2,  # Max 2 tables per persona
                MAX_2_TOPS - total_2_tops_used  # Remaining global capacity
            )
            
            # Calculate desired tables within available limits
            desired_4_tops = min(
                total_tables_needed * four_top_pct,
                max_4_tops_available
            )
            desired_2_tops = min(
                total_tables_needed * (1 - four_top_pct),
                max_2_tops_available
            )
            
            # Allocate tables and update global tracking
            allocated_4_tops = int(desired_4_tops)  # Ensure integer values
            allocated_2_tops = int(desired_2_tops)
            
            total_4_tops_used += allocated_4_tops
            total_2_tops_used += allocated_2_tops
            
            # Only consider splitting 4-tops if we absolutely need to and have capacity
            remaining_2_top_demand = max(0, desired_2_tops - allocated_2_tops)
            remaining_4_top_capacity = MAX_4_TOPS - total_4_tops_used
            
            if remaining_2_top_demand > 0 and remaining_4_top_capacity > 0:
                # Limit splits to available capacity and need
                four_tops_to_split = min(
                    math.ceil(remaining_2_top_demand / 2),  # How many 4-tops needed
                    remaining_4_top_capacity,  # How many 4-tops available
                    1  # Maximum 1 split per persona to prevent overconsumption
                )
                total_4_tops_used += four_tops_to_split
                allocated_2_tops += four_tops_to_split * 2
                
            # Track mixed seating (ensure it stays within total seat capacity)
            persona_mixed_seats = int(mixed_visits)  # One seat per mixed visit
            if total_mixed_seats + persona_mixed_seats <= MAX_MIXED_SEATS:
                total_mixed_seats += persona_mixed_seats
            else:
                # Cap mixed seating at remaining capacity
                persona_mixed_seats = max(0, MAX_MIXED_SEATS - total_mixed_seats)
                total_mixed_seats = MAX_MIXED_SEATS
            
            persona_4_full_raw = allocated_4_tops
            persona_2_split_raw = allocated_2_tops
        
        mixed_seats_raw = mixed_visits * avg_group_size
        
        # Store per-block type-specific demands with proper rounding
        demands['type_demands'][persona_type] = {
            'reserved_8_full': math.ceil(persona_8_full_raw),  # Round up to ensure integer tables
            'reserved_6_full': math.ceil(persona_6_full_raw),
            'reserved_4_full': math.ceil(persona_4_full_raw),
            'reserved_2_split': math.ceil(persona_2_split_raw),
            'mixed_seats': math.ceil(mixed_seats_raw)
        }
        
        # Update total demands using rounded per-persona values
        demands['reserved_8_full'] += math.ceil(persona_8_full_raw)
        demands['reserved_6_full'] += math.ceil(persona_6_full_raw)
        demands['reserved_4_full'] += math.ceil(persona_4_full_raw)
        demands['reserved_2_split'] += math.ceil(persona_2_split_raw)
        demands['mixed_seats'] += math.ceil(mixed_seats_raw)
    
    # Store raw demands for debugging
    raw_demands = {
        'reserved_8_full': demands['reserved_8_full'],
        'reserved_6_full': demands['reserved_6_full'],
        'reserved_4_full': demands['reserved_4_full'],
        'reserved_2_split': demands['reserved_2_split'],
        'mixed_seats': demands['mixed_seats']
    }
    
    # Note: Demands are already in per-block format since we calculated them that way
    # Just ensure all values are integers through rounding up
    demands['reserved_8_full'] = math.ceil(demands['reserved_8_full'])
    demands['reserved_6_full'] = math.ceil(demands['reserved_6_full'])
    demands['reserved_4_full'] = math.ceil(demands['reserved_4_full'])
    demands['reserved_2_split'] = math.ceil(demands['reserved_2_split'])
    demands['mixed_seats'] = math.ceil(demands['mixed_seats'])
    
    # Debug output to verify calculations
    print(f"\nDemand Calculation Debug for {M} members:")
    print(f"Raw monthly demands:")
    print(f"  Reserved 8-top (full): {raw_demands['reserved_8_full']}")
    print(f"  Reserved 6-top (full): {raw_demands['reserved_6_full']}")
    print(f"  Reserved 4-top (full): {raw_demands['reserved_4_full']}")
    print(f"  Reserved 2-person: {raw_demands['reserved_2_split']}")
    print(f"  Mixed seats: {raw_demands['mixed_seats']}")
    print(f"\nPer-block requirements:")
    print(f"  Reserved 8-top (full): {demands['reserved_8_full']} tables/block")
    print(f"  Reserved 6-top (full): {demands['reserved_6_full']} tables/block")
    print(f"  Reserved 4-top (full): {demands['reserved_4_full']} tables/block")
    print(f"  Reserved 2-person: {demands['reserved_2_split']} tables/block")
    print(f"  Mixed seats: {demands['mixed_seats']} seats/block")
    
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
    
    # Create optimization model
    model = pulp.LpProblem("Seating_Optimization", pulp.LpMinimize)
    
    # Decision variables for table allocation
    # 4-top tables (8 tables that can split into 2x2)
    reserved_4_full = pulp.LpVariable("reserved_4_full", 0, NUM_4_TOP, cat='Integer')  # Used as full 4-tops
    reserved_4_split = pulp.LpVariable("reserved_4_split", 0, NUM_4_TOP, cat='Integer')  # Split into 2x2
    mixed_4_full = pulp.LpVariable("mixed_4_full", 0, NUM_4_TOP, cat='Integer')  # Used as full 4-tops for mixed
    mixed_4_split = pulp.LpVariable("mixed_4_split", 0, NUM_4_TOP, cat='Integer')  # Split into 2x2 for mixed
    
    # 8-top tables (3 tables that can split into 4+2)
    reserved_8_full = pulp.LpVariable("reserved_8_full", 0, NUM_8_TOP, cat='Integer')  # Used as full 8-tops
    reserved_8_split = pulp.LpVariable("reserved_8_split", 0, NUM_8_TOP, cat='Integer')  # Split into 4+2
    mixed_8_full = pulp.LpVariable("mixed_8_full", 0, NUM_8_TOP, cat='Integer')  # Used as full 8-tops for mixed
    mixed_8_split = pulp.LpVariable("mixed_8_split", 0, NUM_8_TOP, cat='Integer')  # Split into 4+2 for mixed
    
    # 6-top tables (2 tables that can split into 3x2 or 4+2)
    reserved_6_full = pulp.LpVariable("reserved_6_full", 0, NUM_6_TOP, cat='Integer')  # Used as full 6-tops
    reserved_6_split_3x2 = pulp.LpVariable("reserved_6_split_3x2", 0, NUM_6_TOP, cat='Integer')  # Split into 3x2
    reserved_6_split_4_2 = pulp.LpVariable("reserved_6_split_4_2", 0, NUM_6_TOP, cat='Integer')  # Split into 4+2
    mixed_6_full = pulp.LpVariable("mixed_6_full", 0, NUM_6_TOP, cat='Integer')  # Used as full 6-tops for mixed
    mixed_6_split_3x2 = pulp.LpVariable("mixed_6_split_3x2", 0, NUM_6_TOP, cat='Integer')  # Split into 3x2 for mixed
    mixed_6_split_4_2 = pulp.LpVariable("mixed_6_split_4_2", 0, NUM_6_TOP, cat='Integer')  # Split into 4+2 for mixed
    
    # 2-top tables (2 fixed tables)
    reserved_2 = pulp.LpVariable("reserved_2", 0, NUM_2_TOP, cat='Integer')  # Used for 2-person reservations
    mixed_2 = pulp.LpVariable("mixed_2", 0, NUM_2_TOP, cat='Integer')  # Used for mixed seating
    
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
    
    # Constraints
    
    # Use the already-rounded per-block requirements from compute_demands()
    # Note: Each 3-hour block is treated as a discrete unit
    # - One table per reservation for the full block
    # - Mixed seating fills available seats in the block
    reserved_8_per_block = demands['reserved_8_full']  # Already rounded up
    reserved_6_per_block = demands['reserved_6_full']  # Already rounded up
    reserved_4_per_block = demands['reserved_4_full']  # Already rounded up
    reserved_2_per_block = demands['reserved_2_split']  # Already rounded up
    mixed_demand_per_block = demands['mixed_seats']  # Already rounded up
    
    # Meet reservation demands
    model += reserved_4_full >= reserved_4_per_block
    model += reserved_4_split * 2 >= reserved_2_per_block  # Each split table serves 2 groups
    
    # Meet mixed seating demand with more flexible constraints
    model += (
        # 4-tops
        mixed_4_full * 4 +  # Each full 4-top serves 4 people
        mixed_4_split * 2 +  # Each split 4-top serves 2 people
        # 8-tops
        mixed_8_full * 8 +  # Each full 8-top serves 8 people
        mixed_8_split * 6 +  # Each split 8-top serves 6 people (4+2)
        # 6-tops
        mixed_6_full * 6 +  # Each full 6-top serves 6 people
        mixed_6_split_3x2 * 5 +  # Each 3x2 split serves 5 people
        mixed_6_split_4_2 * 6 +  # Each 4+2 split serves 6 people
        # 2-tops
        mixed_2 * 2  # Each 2-top serves 2 people
    ) >= mixed_demand_per_block

    # Mixed seating distribution constraints
    # Total mixed seating across all table types must meet but not exceed demand
    model += (
        # 4-tops contribution
        mixed_4_full * 4 + mixed_4_split * 2 +
        # 8-tops contribution
        mixed_8_full * 8 + mixed_8_split * 6 +
        # 6-tops contribution
        mixed_6_full * 6 + mixed_6_split_3x2 * 5 + mixed_6_split_4_2 * 6 +
        # 2-tops contribution
        mixed_2 * 2
    ) == mixed_demand_per_block  # Total mixed seating must exactly meet demand
    
    # Soft upper bounds on each table type's contribution (to encourage distribution)
    model += mixed_4_full * 4 + mixed_4_split * 2 <= mixed_demand_per_block * 0.4  # 4-tops handle up to 40%
    model += mixed_8_full * 8 + mixed_8_split * 6 <= mixed_demand_per_block * 0.3  # 8-tops handle up to 30%
    model += mixed_6_full * 6 + mixed_6_split_3x2 * 5 + mixed_6_split_4_2 * 6 <= mixed_demand_per_block * 0.2  # 6-tops handle up to 20%
    model += mixed_2 * 2 <= mixed_demand_per_block * 0.1  # 2-tops handle up to 10%
    
    # Table capacity constraints - ensure total tables used doesn't exceed capacity
    # 4-top tables (8 tables)
    model += (reserved_4_full + reserved_4_split + 
             mixed_4_full + mixed_4_split) <= NUM_4_TOP, "4_top_capacity"
             
    # 8-top tables (3 tables)
    model += (reserved_8_full + reserved_8_split +
             mixed_8_full + mixed_8_split) <= NUM_8_TOP, "8_top_capacity"
             
    # 6-top tables (2 tables)
    model += (reserved_6_full + reserved_6_split_3x2 + reserved_6_split_4_2 +
             mixed_6_full + mixed_6_split_3x2 + mixed_6_split_4_2) <= NUM_6_TOP, "6_top_capacity"
             
    # 2-top tables (2 fixed tables)
    model += (reserved_2 + mixed_2) <= NUM_2_TOP, "2_top_capacity"
    
    # Splitting priority constraints using binary variables
    # Define binary variables for when splitting is allowed
    can_split_4 = pulp.LpVariable("can_split_4", 0, 1, cat='Binary')
    can_split_8 = pulp.LpVariable("can_split_8", 0, 1, cat='Binary')
    can_split_6 = pulp.LpVariable("can_split_6", 0, 1, cat='Binary')
    
    # Big-M constant (should be larger than maximum possible demand)
    M = NUM_4_TOP + NUM_8_TOP + NUM_6_TOP + NUM_2_TOP
    
    # 4-tops: Only split if full table demand is satisfied
    model += reserved_4_full >= reserved_4_per_block - M * (1 - can_split_4), "4_top_full_priority"
    model += reserved_4_split <= M * can_split_4, "4_top_split_limit"
    
    # 8-tops: Only split if smaller table demands are satisfied
    model += reserved_8_full >= reserved_8_per_block - M * (1 - can_split_8), "8_top_full_priority"
    model += reserved_8_split <= M * can_split_8, "8_top_split_limit"
    
    # 6-tops: Only split if smaller table demands are satisfied
    model += reserved_6_full >= reserved_6_per_block - M * (1 - can_split_6), "6_top_full_priority"
    model += (reserved_6_split_3x2 + reserved_6_split_4_2) <= M * can_split_6, "6_top_split_limit"

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
            'demands': demands,
            'time_blocks': time_blocks
        }
        
        # Calculate utilization rates for each table type
        four_top_util = (results['tables']['reserved_4_full'] + 
                       results['tables']['reserved_4_split'] + 
                       results['tables']['mixed_4_full'] + 
                       results['tables']['mixed_4_split'])/NUM_4_TOP * 100
        
        eight_top_util = (results['tables']['reserved_8_full'] +
                        results['tables']['reserved_8_split'] +
                        results['tables']['mixed_8_full'] +
                        results['tables']['mixed_8_split'])/NUM_8_TOP * 100
        
        six_top_util = (results['tables']['reserved_6_full'] +
                      results['tables']['reserved_6_split_3x2'] +
                      results['tables']['reserved_6_split_4_2'] +
                      results['tables']['mixed_6_full'] +
                      results['tables']['mixed_6_split_3x2'] +
                      results['tables']['mixed_6_split_4_2'])/NUM_6_TOP * 100
        
        two_top_util = (results['tables']['reserved_2'] +
                      results['tables']['mixed_2'])/NUM_2_TOP * 100
        
        # Return True if no table type exceeds capacity
        if (four_top_util <= 100 and eight_top_util <= 100 and 
            six_top_util <= 100 and two_top_util <= 100):
            return True, results
    
    return False, None

def analyze_capacity(test_members=[200, 250, 300, 350, 400]):
    """Analyze capacity for different member counts"""
    print("Capacity Analysis Summary")
    print("=" * 50)
    
    results = []
    for M in test_members:
        demands = compute_demands(M)
        total_tables = NUM_4_TOP + NUM_8_TOP + NUM_6_TOP + NUM_2_TOP
        
        # Calculate tables needed per block
        # Note: Each 3-hour block is treated as a discrete unit
        # - One table per reservation for the full block
        # - Mixed seating fills available seats in the block
        
        # For 4-tops: count full tables and tables needed for 2-person splits
        four_top_tables = demands['reserved_4_full']
        split_tables_needed = math.ceil(demands['reserved_2_split'] / 2)  # Each 4-top gives two 2-person slots
        
        # For mixed seating: calculate total seats needed per block
        mixed_seats = demands['mixed_seats']
        
        if can_accommodate(M)[0]:
            results.append(f"{M} members: ✓ can accommodate")
        else:
            results.append(f"{M} members: ✗ cannot accommodate")
    
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

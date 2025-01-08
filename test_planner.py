import math
from planner import (
    compute_demands,
    NUM_4_TOP,
    NUM_2_TOP,
    NUM_6_TOP,
    NUM_8_TOP
)

def test_demands():
    """Test demand calculations for different member counts"""
    member_counts = [100, 200, 300, 400]  # Test up to 400 members
    
    for M in member_counts:
        print(f"\nTesting with {M} members:")
        print("=" * 40)
        demands = compute_demands(M)
        
        print("\nTotal Per-Block Demands:")
        total_demands = {k:v for k,v in demands.items() if k != 'type_demands'}
        print(f"Reserved 4-tops: {total_demands['reserved_4_full']:.2f} tables/block")
        print(f"Reserved 2-person: {total_demands['reserved_2_split']:.2f} tables/block")
        print(f"Mixed seats: {total_demands['mixed_seats']:.2f} seats/block")
        
        print("\nPer-Persona Per-Block Demands:")
        for persona, values in demands['type_demands'].items():
            print(f"\n{persona.title()}:")
            print(f"  4-tops: {values['reserved_4_full']:.2f} tables/block")
            print(f"  2-person: {values['reserved_2_split']:.2f} tables/block")
            print(f"  Mixed seats: {values['mixed_seats']:.2f} seats/block")
            
        # Calculate total available table capacity
        total_2_person_capacity = NUM_2_TOP  # Fixed 2-tops
        total_4_top_capacity = NUM_4_TOP     # Available 4-tops
        total_6_top_capacity = NUM_6_TOP     # Available 6-tops
        total_8_top_capacity = NUM_8_TOP     # Available 8-tops
        
        # Track table usage
        used_2_tops = min(total_demands['reserved_2_split'], NUM_2_TOP)  # Use fixed 2-tops first
        remaining_2_top_demand = max(0, total_demands['reserved_2_split'] - used_2_tops)
        four_tops_for_splits = math.ceil(remaining_2_top_demand / 2)  # How many 4-tops needed for remaining 2-person demand
        four_tops_for_full = total_demands['reserved_4_full']  # 4-tops used as full tables
        
        # Verify table usage stays within physical limits
        total_4_tops_needed = four_tops_for_full + four_tops_for_splits
        assert total_4_tops_needed <= NUM_4_TOP, f"Total 4-top usage ({total_4_tops_needed}) exceeds capacity ({NUM_4_TOP})"
        assert used_2_tops <= NUM_2_TOP, f"2-top usage ({used_2_tops}) exceeds capacity ({NUM_2_TOP})"
        
        # Verify mixed seating stays within total seat capacity
        total_seats = (NUM_4_TOP * 4) + (NUM_2_TOP * 2) + (NUM_6_TOP * 6) + (NUM_8_TOP * 8)
        assert total_demands['mixed_seats'] <= total_seats, f"Mixed seating demand ({total_demands['mixed_seats']}) exceeds total seat capacity ({total_seats})"
        
        # Verify all demands are non-negative integers
        assert isinstance(total_demands['reserved_4_full'], int), "4-top demand must be an integer"
        assert isinstance(total_demands['reserved_2_split'], int), "2-person demand must be an integer"
        assert isinstance(total_demands['mixed_seats'], int), "Mixed seating demand must be an integer"
        assert total_demands['reserved_4_full'] >= 0, "4-top demand cannot be negative"
        assert total_demands['reserved_2_split'] >= 0, "2-person demand cannot be negative"
        assert total_demands['mixed_seats'] >= 0, "Mixed seating demand cannot be negative"
        
        print(f"\nTable Usage Analysis:")
        print(f"4-tops used as full tables: {four_tops_for_full}")
        print(f"4-tops used for 2-person splits: {four_tops_for_splits}")
        print(f"Total 4-tops needed: {total_4_tops_needed} (capacity: {NUM_4_TOP})")
        print(f"Fixed 2-tops used: {used_2_tops} (capacity: {NUM_2_TOP})")
        print(f"Mixed seating demand: {total_demands['mixed_seats']} seats (total capacity: {total_seats} seats)")

if __name__ == "__main__":
    test_demands()

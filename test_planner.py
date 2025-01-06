from planner import compute_demands

def test_demands():
    print("Testing with 100 members:\n")
    demands = compute_demands(100)
    
    print("Total Demands:")
    total_demands = {k:v for k,v in demands.items() if k != 'type_demands'}
    print(total_demands)
    
    print("\nPer-Persona Demands:")
    for persona, values in demands['type_demands'].items():
        print(f"{persona}:")
        print(f"  4-tops: {values['reserved_4_full']:.1f}")
        print(f"  2-tops: {values['reserved_2_split']:.1f}")
        print(f"  Mixed seats: {values['mixed_seats']:.1f}\n")

if __name__ == "__main__":
    test_demands()

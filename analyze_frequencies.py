import csv
from collections import defaultdict

def analyze_frequencies():
    frequencies = defaultdict(int)
    raw_frequencies = []
    
    with open('OBG_Members_Processed.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            freq = row['How often you want to play']
            raw_frequencies.append(freq)
            
    print("\nAll unique raw frequencies:")
    for freq in sorted(set(raw_frequencies)):
        print(f"- {freq}")
        
    print("\nSuggested normalized frequencies (times per month):")
    for freq in sorted(set(raw_frequencies)):
        normalized = normalize_frequency(freq)
        print(f"'{freq}' -> {normalized}")

def normalize_frequency(freq):
    if not freq:
        return None
    
    freq = freq.lower()
    
    # Daily or more
    if any(term in freq for term in ['daily', '25 hours', 'insatiable', 'all the time']):
        return 30
    
    # Multiple times per week
    if ('2-3' in freq and 'week' in freq) or ('twice' in freq and 'week' in freq):
        return 10
    
    # Weekly
    if any(term in freq for term in ['weekly', 'once a week', '1x week', 'per week']):
        return 4
    
    # Bi-weekly
    if any(term in freq for term in ['bi-weekly', 'every other week', 'biweekly']):
        return 2
    
    # Monthly
    if 'month' in freq:
        if '1-2' in freq or 'once or twice' in freq:
            return 1.5
        if '2-3' in freq:
            return 2.5
        return 1
    
    return None

if __name__ == "__main__":
    analyze_frequencies()

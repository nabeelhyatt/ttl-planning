import re
import csv

def normalize_frequency(freq):
    if not freq:
        return 0
    
    freq = freq.lower()
    
    # Daily or more
    if any(term in freq for term in ['daily', '25 hours', 'insatiable', 'all the time', 'everyday']):
        return 30
    
    # Multiple times per week
    if any(term in freq for term in ['2-3 week', '3-4 week', 'twice week', '2x week']):
        return 10
    
    # Weekly
    if any(term in freq for term in ['weekly', 'once a week', '1x week', 'per week', 'biweekly', 'every other week']):
        return 4
    
    # Multiple times per month
    if any(term in freq for term in ['1-2 month', '2-3 month', 'twice month', '2x month']):
        return 2
    
    # Monthly
    if 'month' in freq:
        return 1
    
    # Default to monthly if unclear
    return 1

def extract_member_info(text):
    members = []
    current_member = {}
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line or ' — ' in line or 'Thread' in line or 'Messages' in line:
            if current_member and 'Name' in current_member:
                if 'How often you want to play' in current_member:
                    current_member['Visits per month'] = normalize_frequency(current_member['How often you want to play'])
                members.append(current_member)
                current_member = {}
            continue
            
        if line.startswith('Name:'):
            if current_member and 'Name' in current_member:
                if 'How often you want to play' in current_member:
                    current_member['Visits per month'] = normalize_frequency(current_member['How often you want to play'])
                members.append(current_member)
                current_member = {}
            current_member['Name'] = line.replace('Name:', '').strip()
        elif line.startswith('City:'):
            current_member['City'] = line.replace('City:', '').strip()
        elif line.startswith('Fave game (today):'):
            current_member['Fav game today'] = line.replace('Fave game (today):', '').strip()
        elif line.startswith('Looking to play:'):
            current_member['Looking to play'] = line.replace('Looking to play:', '').strip()
        elif line.startswith('How often'):
            freq = line.replace('How often you want to play:', '').replace('How often do you want to play:', '').strip()
            current_member['How often you want to play'] = freq
            current_member['Visits per month'] = normalize_frequency(freq)
    
    if current_member and 'Name' in current_member:
        if 'How often you want to play' in current_member:
            current_member['Visits per month'] = normalize_frequency(current_member['How often you want to play'])
        members.append(current_member)
    
    return members

def clean_members(members):
    cleaned = []
    for member in members:
        if not member.get('Name'):
            continue
            
        clean_member = {
            'Name': member.get('Name', '').split('(')[0].strip(),
            'City': member.get('City', '').split('(')[0].strip(),
            'Fav game today': member.get('Fav game today', ''),
            'Looking to play': member.get('Looking to play', ''),
            'How often you want to play': member.get('How often you want to play', ''),
            'Visits per month': member.get('Visits per month', 0)
        }
        
        if len([v for v in clean_member.values() if v]) > 1:
            cleaned.append(clean_member)
    
    return cleaned

def write_csv(members, filename):
    fieldnames = ['Name', 'City', 'Fav game today', 'Looking to play', 'How often you want to play', 'Visits per month']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(members)

# Read the input file
with open('OBG Members.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Process the data
members = extract_member_info(text)
cleaned_members = clean_members(members)

# Write to CSV
write_csv(cleaned_members, 'OBG_Members_Processed.csv')

# Excel vs Web App Comparison Report

## Executive Summary

The Excel Profitability Calculator reveals a more comprehensive revenue and expense model than currently implemented in the web application. Key differences include multiple revenue streams, detailed cost breakdowns, and simpler member counting.

## Key Findings from Excel Analysis

### 1. Revenue Structure (Monthly)
The Excel model tracks **5 revenue streams** totaling $34,850/month:

1. **Membership Revenue: $25,000 (71.7%)**
   - 200 total members
   - Mix of membership tiers (Standard, Family, etc.)
   - Simple member count × price calculation

2. **Guest Passes: $500 (1.4%)**
   - Visit-based add-on revenue

3. **Setup Fees: $1,000 (2.9%)**
   - One-time fees from new members

4. **Retail: $4,400 (12.6%)**
   - Member purchases: $2,000
   - Non-member purchases: $2,400
   - Based on spending assumptions per visit

5. **Visit Add-ons: $1,950 (5.6%)**
   - Food/beverage revenue per visit
   - Calculated from visit frequency × spend per visit

### 2. Expense Structure (Monthly)
Total expenses: $42,965.49/month

1. **Payroll: $26,825 (62.4%)**
   - Fixed salaries: $20,000 (managers/full-time)
   - Hourly wages: $6,825 (based on hours)

2. **Facilities: $10,359 (24.1%)**
   - Rent: $7,778 (primary cost)
   - Utilities, insurance, etc.

3. **Software: $1,735.99 (4.0%)**
   - Mail Chimp, Twilio, and other services

### 3. Profitability
- **Monthly Loss: -$8,115.49**
- **Break-even needs**: Additional revenue or cost reduction

## Comparison with Current Web App

### What the Excel Does Better:

1. **Multiple Revenue Streams**
   - Web app focuses only on membership revenue
   - Excel includes retail, add-ons, setup fees, guest passes

2. **Simpler Member Model**
   - Excel: Simple member count (200 members)
   - Web app: Complex personas with visit patterns and capacity constraints

3. **Detailed Cost Breakdown**
   - Excel: Itemized costs with specific vendors/amounts
   - Web app: No cost modeling

4. **Easy Editing**
   - Excel: Direct cell editing with immediate recalculation
   - Web app: Requires code changes for model adjustments

5. **Clear Profitability View**
   - Excel: Overview sheet shows revenue vs expenses at a glance
   - Web app: Focuses on capacity planning, not P&L

### What the Web App Does Better:

1. **Capacity Planning**
   - Sophisticated table allocation using linear programming
   - Time-based capacity constraints
   - Peak/off-peak modeling

2. **Persona-Based Analysis**
   - Different customer segments with unique behaviors
   - Visit frequency patterns
   - Group size variations

3. **Plan Optimization**
   - Value calculations for different membership tiers
   - Persona-specific plan recommendations

## Recommendations for Web App Enhancement

### 1. Add Financial Dashboard
Create an overview page similar to Excel's Overview sheet:
```python
# New module: financial_dashboard.py
def calculate_monthly_revenue(members, config):
    revenue = {
        'membership': calculate_membership_revenue(members),
        'guest_passes': calculate_guest_revenue(members),
        'setup_fees': calculate_setup_fees(new_members),
        'retail': calculate_retail_revenue(members, visits),
        'visit_addons': calculate_addon_revenue(members, visits)
    }
    return revenue

def calculate_monthly_expenses(config):
    expenses = {
        'payroll': calculate_payroll_costs(),
        'facilities': calculate_facility_costs(),
        'software': calculate_software_costs(),
        'other': calculate_other_costs()
    }
    return expenses
```

### 2. Implement Configuration UI
Make key parameters editable without code changes:
- Member counts by tier
- Pricing for each revenue stream
- Visit frequency assumptions
- Cost inputs

### 3. Add Revenue Projections
Incorporate retail and add-on revenue calculations:
```python
# Enhanced revenue calculation
def calculate_total_revenue(members, visits_per_member):
    membership_revenue = sum(m.price for m in members)
    
    # New: Retail revenue
    retail_per_visit = 10  # configurable
    total_visits = members * visits_per_member
    retail_revenue = total_visits * retail_per_visit * 0.5  # 50% purchase rate
    
    # New: Add-on revenue
    addon_per_visit = 7.50  # configurable
    addon_revenue = total_visits * addon_per_visit * 0.2  # 20% purchase rate
    
    return membership_revenue + retail_revenue + addon_revenue
```

### 4. Create P&L View
Add profit/loss calculation and visualization:
- Monthly revenue breakdown by source
- Monthly expense breakdown by category
- Net profit/loss
- Break-even analysis

### 5. Simplify Member Input
Option to use simple member counts like Excel:
- Quick mode: Enter member counts directly
- Advanced mode: Use persona-based projections

### 6. Export/Import Functionality
- Export current projections to Excel format
- Import member counts and assumptions from spreadsheets

## Implementation Priority

1. **High Priority**: Add revenue streams (retail, add-ons)
2. **High Priority**: Create P&L dashboard
3. **Medium Priority**: Configuration UI for key parameters
4. **Medium Priority**: Expense tracking
5. **Low Priority**: Excel import/export

## Code Structure Suggestions

```
/ttl-planning
├── financial_model/
│   ├── __init__.py
│   ├── revenue.py         # All revenue calculations
│   ├── expenses.py        # All expense calculations
│   ├── profitability.py   # P&L calculations
│   └── config.py          # Editable parameters
├── templates/
│   ├── index.html         # Current capacity view
│   ├── financial.html     # New P&L dashboard
│   └── config.html        # Parameter editing UI
```

This approach maintains the sophisticated capacity planning while adding the financial clarity and ease of use from the Excel model.
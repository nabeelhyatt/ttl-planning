# Tabletop Library Financial Enhancement Project Plan

## Overview
This project will enhance the current web application by incorporating the financial visibility and ease of use from the Excel Profitability Calculator while maintaining the sophisticated capacity planning features.

## Goals
1. Add complete expense tracking and P&L calculation
2. Create a unified financial dashboard similar to Excel's Overview
3. Enable easy parameter editing without code changes
4. Add missing revenue streams (setup fees, non-member retail)
5. Provide simple member count input option

## Phase 1: Core Financial Infrastructure (Week 1)

### 1.1 Expense Tracking Module ⭐ HIGHEST PRIORITY
**File**: `expenses.py`
- Create ExpenseCalculator class
- Track monthly expenses:
  - Payroll: $26,825 (salaries + hourly wages)
  - Facilities: $10,359 (rent, utilities, insurance, supplies)
  - Software: $1,735.99 (subscriptions)
- Make expenses configurable via config.json

### 1.2 Enhanced Revenue Module
**File**: `revenue_planner.py` (update existing)
- Add setup/onboarding fees revenue stream
- Add non-member retail revenue
- Fix the 24_7_access KeyError bug
- Ensure all revenue streams match Excel

### 1.3 Financial Dashboard Backend
**File**: `financial_dashboard.py`
- Calculate total revenue from all sources
- Calculate total expenses from all categories
- Compute net profit/loss
- Generate break-even analysis
- Provide monthly and annual views

## Phase 2: User Interface (Week 2)

### 2.1 P&L Dashboard View
**File**: `templates/financial.html`
- Summary cards showing:
  - Total Revenue with breakdown percentages
  - Total Expenses with breakdown percentages
  - Net Profit/Loss
  - Key metrics (member count, break-even point)
- Charts for visual representation
- Monthly vs Annual toggle

### 2.2 Configuration UI
**File**: `templates/setup.html` (enhance existing)
- Add expense configuration section
- Add revenue assumptions section
- Enable editing of:
  - Setup fee amount
  - Retail spending per visit
  - Add-on purchase rates
  - All expense categories
- Save/load different scenarios

### 2.3 Simple Member Input Mode
**Update**: `templates/index.html`
- Add toggle: "Simple Mode" vs "Advanced Mode"
- Simple Mode: Just enter total member count
- Advanced Mode: Current persona distribution
- Default to Simple Mode for ease of use

## Phase 3: Integration & Polish (Week 3)

### 3.1 API Endpoints
**Update**: `app.py`
- `/api/expenses` - Get/update expense data
- `/api/financial-summary` - Get P&L summary
- `/api/scenarios` - Save/load scenarios
- Update `/api/config` to include all new parameters

### 3.2 Break-Even Analysis
**File**: `break_even.py`
- Calculate members needed to break even
- Show impact of different parameters
- Generate what-if scenarios
- Visualize path to profitability

### 3.3 Export/Import
**File**: `export_manager.py`
- Export current projections to CSV
- Generate PDF reports
- Import data from CSV
- Maintain compatibility with Excel

## Implementation Order

1. **Day 1-2**: Expense module (Critical - currently missing entirely)
2. **Day 3-4**: Fix revenue bugs and add missing streams
3. **Day 5-6**: Financial dashboard backend
4. **Day 7-8**: P&L dashboard frontend
5. **Day 9-10**: Simple member input mode
6. **Day 11-12**: Configuration UI
7. **Day 13-14**: Testing and polish

## Success Metrics

1. **Visibility**: Can see profit/loss at a glance like Excel
2. **Editability**: Can change assumptions without touching code
3. **Accuracy**: Revenue/expense calculations match Excel
4. **Usability**: New users can understand finances in < 1 minute
5. **Completeness**: All Excel revenue streams are captured

## Technical Considerations

1. **Data Flow**:
   ```
   config.json → ExpenseCalculator → FinancialDashboard → UI
                 RevenuePlanner ↗
   ```

2. **Configuration Structure**:
   ```json
   {
     "financial": {
       "expenses": {
         "payroll": {...},
         "facilities": {...},
         "software": {...}
       },
       "revenue_assumptions": {
         "setup_fee": 50,
         "retail_per_visit": 10,
         "addon_purchase_rate": 0.2
       }
     }
   }
   ```

3. **Error Handling**:
   - Fix KeyError issues in value calculations
   - Validate all configuration inputs
   - Provide sensible defaults

## Immediate Next Steps

1. Create `expenses.py` with basic expense tracking
2. Update `config.json` with expense data
3. Fix the 24_7_access KeyError in planner.py
4. Create financial_dashboard.py to combine revenue & expenses

This plan prioritizes the most critical missing functionality (expense tracking and P&L) while maintaining backward compatibility with the existing system.
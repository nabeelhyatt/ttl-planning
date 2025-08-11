# Annual Migration Plan for Tabletop Library Planning Tools

## Overview
This document outlines the plan to migrate the TTL Planning Tools from monthly to annual membership planning, with new membership tiers and updated features.

## Current State
- **Time Frame**: Monthly planning (all calculations based on per-month metrics)
- **Plans**: Basic ($35/mo), Standard ($75/mo), Family ($125/mo)
- **Features**: Guest passes, mixed event access, game checkouts, retail discounts
- **Personas**: Casual, Students, Families, Hobbyists, Everyday

## Target State
- **Time Frame**: Annual planning
- **New Plans**:
  1. **Visitor** ($200/year): 7 visits/year, 3 guests/visit, 18 guest passes, $12 additional visits/guests
  2. **Student** (price TBD): Unlimited Mon-Thu visits, $10/guest
  3. **Member** ($740/year): Unlimited visits, host events, 5 guest passes/mo (60/year), $10/guest, +$75/mo family
  4. **Council Member** ($1800/year): 24/7 access, co-working, 8 guest passes/mo (96/year), advance booking

## Migration Tasks

### 1. Core Data Model Changes

#### 1.1 Update Time Constants (planner.py)
- [x] Add `WEEKS_PER_YEAR = 52` and `MONTHS_PER_YEAR = 12` constants
- [ ] Add `TIME_BLOCKS_PER_YEAR = TIME_BLOCKS_PER_MONTH * 12`
- [ ] Update capacity calculations to use annual blocks
- [ ] Add annual table capacity constants

#### 1.2 Update Plan Structure (planner.py)
- [ ] Replace `BASIC_PLAN_PRICE`, `STANDARD_PLAN_PRICE`, `FAMILY_PLAN_PRICE` with:
  - `VISITOR_PLAN_PRICE = 200`
  - `STUDENT_PLAN_PRICE = TBD`  # Need price from user
  - `MEMBER_PLAN_PRICE = 740`
  - `COUNCIL_PLAN_PRICE = 1800`
- [ ] Update `calculate_plan_value()` to handle new plan types
- [ ] Update `get_plan_features()` for new features

#### 1.3 Update Persona Behavior (planner.py)
- [ ] Convert monthly visit patterns to annual:
  - `reserved_visits` → `reserved_visits_annual`
  - `event_visits` → `event_visits_annual`
  - `guests_per_month` → `guests_per_year`
  - `game_checkouts` → `game_checkouts_annual`
- [ ] Add new fields:
  - `weekday_preference` (for Student plan)
  - `coworking_hours` (for Council plan)
  - `advance_booking_needs` (for Council plan)

### 2. Plan Features Updates

#### 2.1 New Feature Structure
```python
PLAN_FEATURES = {
    'visitor': {
        'visits_included': 7,
        'guests_per_visit': 3,
        'guest_passes_annual': 18,
        'additional_visit_cost': 12,
        'additional_guest_cost': 12,
        'unlimited_visits': False,
        'weekday_only': False,
        'event_hosting': False,
        'coworking_access': False,
        'advance_booking_days': 0
    },
    'student': {
        'visits_included': float('inf'),
        'guest_cost': 10,
        'unlimited_visits': True,
        'weekday_only': True,
        'event_hosting': False,
        'coworking_access': False,
        'advance_booking_days': 0
    },
    'member': {
        'visits_included': float('inf'),
        'guest_passes_monthly': 5,
        'guest_passes_annual': 60,
        'additional_guest_cost': 10,
        'family_addon_monthly': 75,
        'unlimited_visits': True,
        'weekday_only': False,
        'event_hosting': True,
        'coworking_access': False,
        'advance_booking_days': 7,
        'gift_memberships': 3
    },
    'council': {
        'visits_included': float('inf'),
        'guest_passes_monthly': 8,
        'guest_passes_annual': 96,
        'additional_guest_cost': 10,
        'family_addon_monthly': 75,
        'unlimited_visits': True,
        'weekday_only': False,
        'event_hosting': True,
        'coworking_access': True,
        '24_7_access': True,
        'advance_booking_days': 30,
        'gift_memberships': 3
    }
}
```

### 3. Value Calculator Updates (value_calculator.py)

#### 3.1 Update Value Calculations
- [ ] Convert all monthly value calculations to annual
- [ ] Add logic for:
  - Limited visits (Visitor plan)
  - Weekday-only access (Student plan)
  - Co-working value (Council plan)
  - 24/7 access value (Council plan)
  - Gift membership value

#### 3.2 New Value Components
- [ ] `visit_overage_value` - for plans with visit limits
- [ ] `weekday_restriction_penalty` - for Student plan
- [ ] `coworking_value` - for Council plan
- [ ] `advance_booking_value` - for Member/Council plans
- [ ] `gift_membership_value` - for Member/Council plans

### 4. Revenue Planner Updates (revenue_planner.py)

#### 4.1 Annual Revenue Calculations
- [ ] Update `calculate_monthly_revenue()` to `calculate_annual_revenue()`
- [ ] Add monthly breakdown display (annual / 12)
- [ ] Update guest revenue calculations for new pricing models
- [ ] Add family addon revenue calculations

### 5. Plan Optimizer Updates (plan_optimizer.py)

#### 5.1 New Optimization Logic
- [ ] Update to compare 4 plans instead of 3
- [ ] Add logic for:
  - Visit frequency thresholds (when Visitor → Student/Member)
  - Weekday vs weekend usage patterns
  - Co-working space value calculations
  - Family addon recommendations

### 6. UI/Frontend Updates (templates/index.html)

#### 6.1 Setup Tab Updates
- [ ] Update plan names and prices to annual
- [ ] Add new feature fields
- [ ] Update persona behavior fields to annual metrics
- [ ] Add "per year" / "per month" toggle for display

#### 6.2 Revenue Tab Updates
- [ ] Show annual revenue with monthly breakdown
- [ ] Add family addon revenue display
- [ ] Show gift membership impact

### 7. API Updates (app.py, api/index.py)

#### 7.1 Config Structure Updates
- [ ] Update config.json schema for annual data
- [ ] Add migration logic to convert existing monthly configs
- [ ] Update validation for annual values

### 8. Testing & Validation

#### 8.1 Data Validation
- [ ] Ensure capacity calculations work with annual timeframes
- [ ] Verify value calculations produce reasonable ratios
- [ ] Test edge cases (very low/high visit frequencies)

#### 8.2 Migration Testing
- [ ] Test config migration from monthly to annual
- [ ] Verify backwards compatibility handling
- [ ] Test all API endpoints with new data structure

## Implementation Order

1. **Phase 1 - Core Model** (planner.py)
   - Update time constants
   - Add new plan structures
   - Update persona definitions

2. **Phase 2 - Calculations** (value_calculator.py, revenue_planner.py)
   - Update value calculations
   - Update revenue projections

3. **Phase 3 - Optimization** (plan_optimizer.py, persona_optimization.py)
   - Update optimization logic
   - Update persona matching

4. **Phase 4 - API & Config** (app.py, api/index.py, config.json)
   - Update API endpoints
   - Add migration logic
   - Update config structure

5. **Phase 5 - Frontend** (templates/index.html)
   - Update UI for annual display
   - Add new fields
   - Update save/load logic

## Migration Notes

### Backwards Compatibility
- Keep monthly calculation functions with deprecation warnings
- Add `time_period` parameter to key functions
- Provide conversion utilities

### Data Migration
- Create migration script for existing configs
- Default persona annual values = monthly * 12 (initially)
- Adjust based on actual annual patterns

### Key Assumptions
- Annual memberships paid upfront
- Family addon billed monthly even with annual membership
- Guest passes accumulate monthly but tracked annually
- Visit tracking remains on per-visit basis

## Risks & Mitigations

1. **Risk**: Breaking existing functionality
   - **Mitigation**: Implement changes incrementally with tests

2. **Risk**: Incorrect annual projections
   - **Mitigation**: Validate against current monthly * 12 baseline

3. **Risk**: Complex value calculations
   - **Mitigation**: Add detailed logging and debugging output

4. **Risk**: UI confusion between monthly/annual
   - **Mitigation**: Clear labeling and optional toggle views 
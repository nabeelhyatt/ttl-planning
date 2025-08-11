# ABOUTME: Calculates monthly and annual expense projections for the tabletop library
# ABOUTME: Tracks payroll, facilities, software, and other operational costs

import json
import os

class ExpenseCalculator:
    """Calculate and manage expense projections based on Excel model"""
    
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.load_config()
    
    def load_config(self):
        """Load expense configuration from config file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.expense_config = config.get('expenses', self.get_default_expenses())
        except (FileNotFoundError, json.JSONDecodeError):
            self.expense_config = self.get_default_expenses()
    
    def get_default_expenses(self):
        """Get default expense values based on Excel analysis"""
        return {
            'payroll': {
                'salaries': {
                    'description': 'Fixed monthly salaries (managers, full-time staff)',
                    'amount': 20000.0
                },
                'hourly_wages': {
                    'description': 'Variable hourly wages',
                    'hourly_rate': 24.5,
                    'hours_per_week': 65,
                    'amount': 6825.0  # (65 hours/week * 4.33 weeks/month * $24.5/hour)
                }
            },
            'facilities': {
                'rent': {
                    'description': 'Monthly rent',
                    'amount': 7778.0
                },
                'utilities': {
                    'description': 'Electricity, water, gas',
                    'amount': 500.0
                },
                'insurance': {
                    'description': 'Business insurance',
                    'amount': 800.0
                },
                'supplies': {
                    'description': 'Cleaning, office supplies, etc.',
                    'amount': 500.0
                },
                'maintenance': {
                    'description': 'Repairs and maintenance',
                    'amount': 250.0
                },
                'other': {
                    'description': 'Miscellaneous facility costs',
                    'amount': 531.0
                }
            },
            'software': {
                'mail_chimp': {
                    'description': 'Email marketing',
                    'amount': 20.0
                },
                'twilio': {
                    'description': 'SMS notifications',
                    'amount': 50.0
                },
                'square': {
                    'description': 'Payment processing',
                    'amount': 150.0
                },
                'quickbooks': {
                    'description': 'Accounting software',
                    'amount': 35.0
                },
                'google_workspace': {
                    'description': 'Email and productivity',
                    'amount': 30.0
                },
                'website_hosting': {
                    'description': 'Website and app hosting',
                    'amount': 200.0
                },
                'other_software': {
                    'description': 'Other software subscriptions',
                    'amount': 1250.99
                }
            }
        }
    
    def calculate_monthly_expenses(self):
        """Calculate total monthly expenses by category"""
        monthly_expenses = {
            'payroll': self._calculate_payroll(),
            'facilities': self._calculate_facilities(),
            'software': self._calculate_software()
        }
        
        # Add totals
        monthly_expenses['total_by_category'] = {
            'payroll': sum(item['amount'] for item in monthly_expenses['payroll'].values()),
            'facilities': sum(item['amount'] for item in monthly_expenses['facilities'].values()),
            'software': sum(item['amount'] for item in monthly_expenses['software'].values())
        }
        
        monthly_expenses['total_expenses'] = sum(monthly_expenses['total_by_category'].values())
        
        return monthly_expenses
    
    def calculate_annual_expenses(self):
        """Calculate annual expenses (monthly * 12)"""
        monthly = self.calculate_monthly_expenses()
        
        annual_expenses = {
            'payroll': {k: {**v, 'annual_amount': v['amount'] * 12} for k, v in monthly['payroll'].items()},
            'facilities': {k: {**v, 'annual_amount': v['amount'] * 12} for k, v in monthly['facilities'].items()},
            'software': {k: {**v, 'annual_amount': v['amount'] * 12} for k, v in monthly['software'].items()}
        }
        
        annual_expenses['total_by_category'] = {
            k: v * 12 for k, v in monthly['total_by_category'].items()
        }
        
        annual_expenses['total_expenses'] = monthly['total_expenses'] * 12
        
        return annual_expenses
    
    def _calculate_payroll(self):
        """Calculate payroll expenses"""
        payroll = self.expense_config.get('payroll', {})
        return {
            'salaries': {
                'description': payroll.get('salaries', {}).get('description', 'Fixed salaries'),
                'amount': payroll.get('salaries', {}).get('amount', 20000.0)
            },
            'hourly_wages': {
                'description': payroll.get('hourly_wages', {}).get('description', 'Hourly wages'),
                'amount': payroll.get('hourly_wages', {}).get('amount', 6825.0)
            }
        }
    
    def _calculate_facilities(self):
        """Calculate facility expenses"""
        facilities = self.expense_config.get('facilities', {})
        result = {}
        
        for key, default in [
            ('rent', 7778.0),
            ('utilities', 500.0),
            ('insurance', 800.0),
            ('supplies', 500.0),
            ('maintenance', 250.0),
            ('other', 531.0)
        ]:
            result[key] = {
                'description': facilities.get(key, {}).get('description', key.replace('_', ' ').title()),
                'amount': facilities.get(key, {}).get('amount', default)
            }
        
        return result
    
    def _calculate_software(self):
        """Calculate software expenses"""
        software = self.expense_config.get('software', {})
        result = {}
        
        for key, default in [
            ('mail_chimp', 20.0),
            ('twilio', 50.0),
            ('square', 150.0),
            ('quickbooks', 35.0),
            ('google_workspace', 30.0),
            ('website_hosting', 200.0),
            ('other_software', 1250.99)
        ]:
            result[key] = {
                'description': software.get(key, {}).get('description', key.replace('_', ' ').title()),
                'amount': software.get(key, {}).get('amount', default)
            }
        
        return result
    
    def get_expense_breakdown_percentages(self):
        """Get expense breakdown as percentages of total"""
        monthly = self.calculate_monthly_expenses()
        total = monthly['total_expenses']
        
        if total == 0:
            return {}
        
        return {
            'payroll': round(monthly['total_by_category']['payroll'] / total * 100, 1),
            'facilities': round(monthly['total_by_category']['facilities'] / total * 100, 1),
            'software': round(monthly['total_by_category']['software'] / total * 100, 1)
        }
    
    def update_expense(self, category, subcategory, amount):
        """Update a specific expense amount"""
        if category in self.expense_config and subcategory in self.expense_config[category]:
            self.expense_config[category][subcategory]['amount'] = amount
            self.save_config()
            return True
        return False
    
    def save_config(self):
        """Save expense configuration back to config file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}
        
        config['expenses'] = self.expense_config
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def print_expense_summary(self):
        """Print a formatted expense summary"""
        monthly = self.calculate_monthly_expenses()
        percentages = self.get_expense_breakdown_percentages()
        
        print("Monthly Expense Summary")
        print("=" * 50)
        
        # Payroll
        print(f"\nPayroll: ${monthly['total_by_category']['payroll']:,.2f} ({percentages['payroll']}%)")
        for key, data in monthly['payroll'].items():
            print(f"  - {data['description']}: ${data['amount']:,.2f}")
        
        # Facilities
        print(f"\nFacilities: ${monthly['total_by_category']['facilities']:,.2f} ({percentages['facilities']}%)")
        for key, data in monthly['facilities'].items():
            print(f"  - {data['description']}: ${data['amount']:,.2f}")
        
        # Software
        print(f"\nSoftware: ${monthly['total_by_category']['software']:,.2f} ({percentages['software']}%)")
        for key, data in monthly['software'].items():
            print(f"  - {data['description']}: ${data['amount']:,.2f}")
        
        print("\n" + "-" * 50)
        print(f"Total Monthly Expenses: ${monthly['total_expenses']:,.2f}")
        print(f"Total Annual Expenses: ${monthly['total_expenses'] * 12:,.2f}")

if __name__ == "__main__":
    calculator = ExpenseCalculator()
    calculator.print_expense_summary()
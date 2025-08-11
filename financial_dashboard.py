# ABOUTME: Combines revenue and expense calculations to provide complete P&L view
# ABOUTME: Calculates profitability, break-even analysis, and financial metrics

from revenue_planner import RevenuePlanner
from expenses import ExpenseCalculator
import json

class FinancialDashboard:
    """Financial dashboard for P&L analysis and break-even calculations"""
    
    def __init__(self):
        self.revenue_planner = RevenuePlanner()
        self.expense_calculator = ExpenseCalculator()
    
    def calculate_monthly_pl(self, total_members=200):
        """Calculate monthly profit/loss statement"""
        # Get annual revenue and convert to monthly
        annual_revenue = self.revenue_planner.calculate_annual_revenue(total_members=total_members)
        monthly_revenue = {k: v/12 for k, v in annual_revenue.items() if k not in ['total_revenue', 'monthly_average']}
        monthly_revenue['total'] = annual_revenue['monthly_average']
        
        # Get monthly expenses
        monthly_expenses = self.expense_calculator.calculate_monthly_expenses()
        
        # Calculate profit/loss
        net_profit = monthly_revenue['total'] - monthly_expenses['total_expenses']
        
        return {
            'revenue': monthly_revenue,
            'expenses': monthly_expenses,
            'net_profit': net_profit,
            'profit_margin': (net_profit / monthly_revenue['total'] * 100) if monthly_revenue['total'] > 0 else 0
        }
    
    def calculate_annual_pl(self, total_members=200):
        """Calculate annual profit/loss statement"""
        # Get annual revenue
        annual_revenue = self.revenue_planner.calculate_annual_revenue(total_members=total_members)
        
        # Get annual expenses
        annual_expenses = self.expense_calculator.calculate_annual_expenses()
        
        # Calculate profit/loss
        net_profit = annual_revenue['total_revenue'] - annual_expenses['total_expenses']
        
        return {
            'revenue': annual_revenue,
            'expenses': annual_expenses,
            'net_profit': net_profit,
            'profit_margin': (net_profit / annual_revenue['total_revenue'] * 100) if annual_revenue['total_revenue'] > 0 else 0
        }
    
    def calculate_break_even(self):
        """Calculate break-even member count"""
        # Binary search for break-even point
        low, high = 1, 1000
        break_even_members = 0
        
        while low <= high:
            mid = (low + high) // 2
            pl = self.calculate_monthly_pl(total_members=mid)
            
            if abs(pl['net_profit']) < 100:  # Within $100 of break-even
                break_even_members = mid
                break
            elif pl['net_profit'] < 0:
                low = mid + 1
            else:
                high = mid - 1
                break_even_members = mid  # Keep the last profitable count
        
        # Calculate exact break-even metrics
        pl_at_break_even = self.calculate_monthly_pl(total_members=break_even_members)
        
        return {
            'break_even_members': break_even_members,
            'monthly_revenue_at_break_even': pl_at_break_even['revenue']['total'],
            'monthly_expenses': pl_at_break_even['expenses']['total_expenses'],
            'current_gap': pl_at_break_even['net_profit']
        }
    
    def get_revenue_breakdown_percentages(self, revenue_data):
        """Calculate revenue breakdown as percentages"""
        total = revenue_data.get('total', revenue_data.get('total_revenue', 0))
        if total == 0:
            return {}
        
        percentages = {}
        for key, value in revenue_data.items():
            if key not in ['total', 'total_revenue', 'monthly_average']:
                percentages[key] = round(value / total * 100, 1)
        
        return percentages
    
    def generate_summary_metrics(self, total_members=200):
        """Generate key metrics for dashboard display"""
        monthly_pl = self.calculate_monthly_pl(total_members)
        annual_pl = self.calculate_annual_pl(total_members)
        break_even = self.calculate_break_even()
        
        # Revenue percentages
        revenue_percentages = self.get_revenue_breakdown_percentages(monthly_pl['revenue'])
        expense_percentages = self.expense_calculator.get_expense_breakdown_percentages()
        
        return {
            'current_members': total_members,
            'monthly': {
                'revenue': monthly_pl['revenue']['total'],
                'expenses': monthly_pl['expenses']['total_expenses'],
                'net_profit': monthly_pl['net_profit'],
                'profit_margin': monthly_pl['profit_margin']
            },
            'annual': {
                'revenue': annual_pl['revenue']['total_revenue'],
                'expenses': annual_pl['expenses']['total_expenses'],
                'net_profit': annual_pl['net_profit'],
                'profit_margin': annual_pl['profit_margin']
            },
            'break_even': break_even,
            'revenue_breakdown': revenue_percentages,
            'expense_breakdown': expense_percentages,
            'members_to_break_even': break_even['break_even_members'] - total_members
        }
    
    def print_financial_summary(self, total_members=200):
        """Print a comprehensive financial summary"""
        metrics = self.generate_summary_metrics(total_members)
        monthly_pl = self.calculate_monthly_pl(total_members)
        
        print("=" * 60)
        print("FINANCIAL DASHBOARD SUMMARY")
        print("=" * 60)
        
        # Current Status
        print(f"\nCurrent Members: {metrics['current_members']}")
        print(f"Break-even Members: {metrics['break_even']['break_even_members']}")
        print(f"Members Needed: {max(0, metrics['members_to_break_even'])}")
        
        # Monthly P&L
        print("\n" + "-" * 30)
        print("MONTHLY PROFIT & LOSS")
        print("-" * 30)
        
        print("\nRevenue:")
        for key, pct in metrics['revenue_breakdown'].items():
            amount = monthly_pl['revenue'].get(key, 0)
            print(f"  {key.replace('_', ' ').title()}: ${amount:,.2f} ({pct}%)")
        print(f"  Total Revenue: ${metrics['monthly']['revenue']:,.2f}")
        
        print("\nExpenses:")
        for key, pct in metrics['expense_breakdown'].items():
            amount = monthly_pl['expenses']['total_by_category'].get(key, 0)
            print(f"  {key.title()}: ${amount:,.2f} ({pct}%)")
        print(f"  Total Expenses: ${metrics['monthly']['expenses']:,.2f}")
        
        print(f"\nNet Profit/Loss: ${metrics['monthly']['net_profit']:,.2f}")
        print(f"Profit Margin: {metrics['monthly']['profit_margin']:.1f}%")
        
        # Annual Summary
        print("\n" + "-" * 30)
        print("ANNUAL PROJECTIONS")
        print("-" * 30)
        print(f"Annual Revenue: ${metrics['annual']['revenue']:,.2f}")
        print(f"Annual Expenses: ${metrics['annual']['expenses']:,.2f}")
        print(f"Annual Net Profit/Loss: ${metrics['annual']['net_profit']:,.2f}")
        print(f"Annual Profit Margin: {metrics['annual']['profit_margin']:.1f}%")
        
        # Status
        print("\n" + "-" * 30)
        if metrics['monthly']['net_profit'] >= 0:
            print("✅ PROFITABLE")
        else:
            print("❌ OPERATING AT A LOSS")
            print(f"   Need {metrics['members_to_break_even']} more members to break even")
        print("=" * 60)

if __name__ == "__main__":
    dashboard = FinancialDashboard()
    
    # Test with Excel's 200 members
    print("\nAnalysis at 200 members (Excel baseline):")
    dashboard.print_financial_summary(200)
    
    # Test at break-even
    break_even = dashboard.calculate_break_even()
    print(f"\n\nAnalysis at break-even ({break_even['break_even_members']} members):")
    dashboard.print_financial_summary(break_even['break_even_members'])
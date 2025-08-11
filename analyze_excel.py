#!/usr/bin/env python3
"""
ABOUTME: Analyzes the Profitability Calculator Excel file to extract structure, data, and formulas
ABOUTME: Outputs a comprehensive report to understand the spreadsheet's business logic
"""

import pandas as pd
import openpyxl
from openpyxl.utils import get_column_letter
import json
import sys
from pathlib import Path

def analyze_excel_file(filename):
    """Analyze Excel file structure, data, and formulas"""
    
    print(f"Analyzing Excel file: {filename}")
    print("=" * 80)
    
    # Check if file exists
    if not Path(filename).exists():
        print(f"Error: File {filename} not found!")
        return
    
    # Load workbook with openpyxl to access formulas
    try:
        wb = openpyxl.load_workbook(filename, data_only=False)
        wb_values = openpyxl.load_workbook(filename, data_only=True)
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return
    
    # Also load with pandas for easier data analysis
    excel_file = pd.ExcelFile(filename)
    
    # Analyze each sheet
    sheet_analysis = {}
    
    for sheet_name in wb.sheetnames:
        print(f"\n\nSheet: {sheet_name}")
        print("-" * 40)
        
        sheet = wb[sheet_name]
        sheet_values = wb_values[sheet_name]
        
        # Get sheet dimensions
        max_row = sheet.max_row
        max_col = sheet.max_column
        print(f"Dimensions: {max_row} rows x {max_col} columns")
        
        # Read data with pandas for structure analysis
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            print(f"\nColumn Headers: {list(df.columns)}")
            print(f"Data rows: {len(df)}")
        except Exception as e:
            print(f"Could not read sheet with pandas: {e}")
            df = None
        
        # Find and analyze formulas
        formulas = {}
        key_cells = {}
        
        print("\nKey Formulas Found:")
        formula_count = 0
        
        for row in range(1, min(max_row + 1, 100)):  # Limit to first 100 rows for efficiency
            for col in range(1, min(max_col + 1, 26)):  # Limit to first 26 columns
                cell = sheet.cell(row=row, column=col)
                cell_values = sheet_values.cell(row=row, column=col)
                cell_ref = f"{get_column_letter(col)}{row}"
                
                # Check if cell contains a formula
                if cell.value and isinstance(cell.value, str) and cell.value.startswith('='):
                    formula_count += 1
                    formulas[cell_ref] = {
                        'formula': cell.value,
                        'value': cell_values.value
                    }
                    
                    # Print first 20 formulas as examples
                    if formula_count <= 20:
                        print(f"  {cell_ref}: {cell.value} = {cell_values.value}")
                
                # Identify key cells (headers, labels)
                if row <= 5 and cell.value and isinstance(cell.value, str):
                    key_cells[cell_ref] = cell.value
        
        if formula_count > 20:
            print(f"  ... and {formula_count - 20} more formulas")
        
        # Analyze data patterns
        if df is not None and len(df) > 0:
            print("\nData Summary:")
            # Show first few rows
            print("\nFirst few rows:")
            print(df.head(3).to_string())
            
            # Identify numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                print(f"\nNumeric columns: {numeric_cols}")
                
                # Show basic statistics for numeric columns
                print("\nBasic statistics:")
                print(df[numeric_cols].describe().round(2).to_string())
        
        # Store analysis for this sheet
        sheet_analysis[sheet_name] = {
            'dimensions': {'rows': max_row, 'cols': max_col},
            'formulas': formulas,
            'key_cells': key_cells,
            'formula_count': formula_count,
            'columns': list(df.columns) if df is not None else []
        }
    
    # Look for cross-sheet references
    print("\n\nCross-Sheet References:")
    print("-" * 40)
    
    for sheet_name, analysis in sheet_analysis.items():
        for cell_ref, formula_info in analysis['formulas'].items():
            formula = formula_info['formula']
            # Look for sheet references (Sheet!Cell pattern)
            for other_sheet in wb.sheetnames:
                if other_sheet != sheet_name and other_sheet in formula:
                    print(f"{sheet_name} {cell_ref} references {other_sheet}: {formula}")
    
    # Save detailed analysis to JSON file
    output_file = 'excel_analysis.json'
    with open(output_file, 'w') as f:
        # Convert formulas dict to be JSON serializable
        json_safe_analysis = {}
        for sheet, data in sheet_analysis.items():
            json_safe_analysis[sheet] = {
                'dimensions': data['dimensions'],
                'formula_count': data['formula_count'],
                'columns': data['columns'],
                'key_cells': data['key_cells'],
                'sample_formulas': dict(list(data['formulas'].items())[:10])  # First 10 formulas
            }
        
        json.dump(json_safe_analysis, f, indent=2, default=str)
    
    print(f"\n\nDetailed analysis saved to: {output_file}")
    
    # Generate summary report
    print("\n\nSUMMARY REPORT")
    print("=" * 80)
    print(f"Total sheets: {len(wb.sheetnames)}")
    print(f"Sheet names: {', '.join(wb.sheetnames)}")
    
    total_formulas = sum(analysis['formula_count'] for analysis in sheet_analysis.values())
    print(f"Total formulas found: {total_formulas}")
    
    print("\n\nRECOMMENDATIONS FOR WEB APP INTEGRATION:")
    print("-" * 40)
    print("1. Key calculations to implement:")
    print("   - Look at the formulas above to identify core business logic")
    print("   - Cross-sheet references indicate data dependencies")
    print("   - Numeric columns show what metrics are being tracked")
    print("\n2. Data structure insights:")
    print("   - Column headers show the data model")
    print("   - Sheet names indicate functional areas")
    print("   - Formula patterns reveal calculation methods")
    
    return sheet_analysis

if __name__ == "__main__":
    filename = "Profitability Calculator.xlsx"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    analyze_excel_file(filename)
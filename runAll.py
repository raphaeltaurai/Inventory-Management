"""
Master script to run the complete inventory aging analysis pipeline.
Executes all three steps in sequence: data prep, aging analysis, and summary report.
"""
import subprocess
import sys
import os

def run_script(script_name, description):
    """Run a Python script and handle any errors."""
    print("\n" + "=" * 80)
    print(f"STEP: {description}")
    print("=" * 80)
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✓ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running {script_name}")
        print(f"Exit code: {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"✗ Error: {script_name} not found")
        return False

def main():
    print("\n" + "=" * 80)
    print("INVENTORY AGING ANALYSIS - FULL PIPELINE")
    print("=" * 80)
    print("\nThis will run the complete analysis in 3 steps:")
    print("  1. Data Preparation (quantities.py)")
    print("  2. Aging Analysis & Visualization (binAging.py)")
    print("  3. Summary Report Generation (summaryReport.py)")
    print("\n" + "=" * 80)
    
    # Step 1: Data Preparation
    if not run_script("quantities.py", "Data Preparation - Merging transaction and quantity files"):
        print("\n✗ Pipeline failed at Step 1")
        sys.exit(1)
    
    # Step 2: Aging Analysis
    if not run_script("binAging.py", "Aging Analysis - FIFO calculation and visualizations"):
        print("\n✗ Pipeline failed at Step 2")
        sys.exit(1)
    
    # Step 3: Summary Report
    if not run_script("summaryReport.py", "Summary Report - Statistics and insights"):
        print("\n✗ Pipeline failed at Step 3")
        sys.exit(1)
    
    # Success message
    print("\n" + "=" * 80)
    print("✓ PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\nGenerated outputs in Aged_Bins folder:")
    print("  • CSV: Transaction data with aging calculations")
    print("  • PNG: Visualization charts (aging analysis & trends)")
    print("  • TXT: Detailed summary report")
    print("  • CSV: Bin statistics and slowest-moving products")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

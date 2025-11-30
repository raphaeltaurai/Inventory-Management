import pandas as pd
import os
from datetime import datetime

# Read the aged bins data
aged_bins_dir = 'Aged_Bins'
csv_files = [f for f in os.listdir(aged_bins_dir) if f.startswith('binAgingFrom') and f.endswith('.csv')]

if not csv_files:
    print("Error: No aged bins CSV file found. Please run binAging.py first.")
    exit(1)

# Use the most recent file
latest_file = sorted(csv_files)[-1]
file_path = os.path.join(aged_bins_dir, latest_file)
df = pd.read_csv(file_path)

print("=" * 80)
print("INVENTORY AGING SUMMARY REPORT")
print("=" * 80)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Data Source: {latest_file}")
print(f"Total Transactions: {len(df):,}")
print("=" * 80)

# Convert age labels to numeric values for average calculation
age_mapping = {
    '0': 0,
    '0 to 1': 0.5,
    '2 to 3': 2.5,
    '4 to 5': 4.5,
    '6+': 7  # Conservative estimate
}

df['AgeNumeric'] = df['Age'].map(age_mapping)

# Filter to active inventory (closing balance > 0)
active_df = df[df['ClosingBalance'] > 0].copy()

print("\n" + "=" * 80)
print("1. AVERAGE AGE PER BIN")
print("=" * 80)

# Calculate weighted average age per bin
bin_stats = active_df.groupby('Bin').agg({
    'ClosingBalance': 'sum',
    'AgeNumeric': lambda x: (x * active_df.loc[x.index, 'ClosingBalance']).sum() / active_df.loc[x.index, 'ClosingBalance'].sum()
}).round(2)

bin_stats.columns = ['Total_Inventory', 'Avg_Age_Days']
bin_stats = bin_stats.sort_values('Avg_Age_Days', ascending=False)

print("\nTop 15 Bins by Average Age (days):")
print("-" * 80)
print(f"{'Bin':<20} {'Total Inventory':>18} {'Avg Age (days)':>20}")
print("-" * 80)
for idx, (bin_name, row) in enumerate(bin_stats.head(15).iterrows(), 1):
    print(f"{idx:2}. {bin_name:<15} {row['Total_Inventory']:>18,.2f} {row['Avg_Age_Days']:>20.2f}")

print("\n" + "=" * 80)
print("2. TOTAL INVENTORY BY AGE CATEGORY")
print("=" * 80)

age_inventory = active_df.groupby('Age').agg({
    'ClosingBalance': ['sum', 'count']
}).round(2)

age_inventory.columns = ['Total_Inventory', 'Num_Entries']
age_order = ['0 to 1', '2 to 3', '4 to 5', '6+', '0']
age_inventory = age_inventory.reindex([a for a in age_order if a in age_inventory.index])

total_inventory = age_inventory['Total_Inventory'].sum()
age_inventory['Percentage'] = (age_inventory['Total_Inventory'] / total_inventory * 100).round(2)

print(f"\n{'Age Category':<15} {'Total Inventory':>18} {'Entries':>12} {'Percentage':>12}")
print("-" * 80)
for age_cat, row in age_inventory.iterrows():
    print(f"{age_cat:<15} {row['Total_Inventory']:>18,.2f} {int(row['Num_Entries']):>12,} {row['Percentage']:>11.2f}%")

print(f"\n{'TOTAL':<15} {total_inventory:>18,.2f} {int(age_inventory['Num_Entries'].sum()):>12,} {'100.00':>11}%")

print("\n" + "=" * 80)
print("3. TOP 10 SLOWEST-MOVING PRODUCTS")
print("=" * 80)

# Calculate product movement metrics
# Get the latest state for each product
latest_dates = df.groupby('Product')['TransactionDate'].max()
latest_records = df.set_index(['Product', 'TransactionDate']).loc[
    [(prod, date) for prod, date in latest_dates.items()]
].reset_index()

# Filter products with remaining inventory
products_with_stock = latest_records[latest_records['ClosingBalance'] > 0].copy()

# Calculate days since last transaction
df['TransactionDate'] = pd.to_datetime(df['TransactionDate'])
max_date = df['TransactionDate'].max()

product_metrics = df.groupby('Product').agg({
    'TransactionDate': ['min', 'max', 'count'],
    'TransactionQty': lambda x: (x != 0).sum()  # Count non-zero transactions
}).reset_index()

product_metrics.columns = ['Product', 'First_Transaction', 'Last_Transaction', 'Total_Transactions', 'Active_Transactions']
product_metrics['Days_Since_Last'] = (max_date - product_metrics['Last_Transaction']).dt.days
product_metrics['Days_Active'] = (product_metrics['Last_Transaction'] - product_metrics['First_Transaction']).dt.days + 1
product_metrics['Transaction_Frequency'] = (product_metrics['Active_Transactions'] / product_metrics['Days_Active'].replace(0, 1)).round(4)

# Merge with closing balance
product_stock = products_with_stock.groupby('Product').agg({
    'ClosingBalance': 'sum',
    'AgeNumeric': lambda x: (x * products_with_stock.loc[x.index, 'ClosingBalance']).sum() / products_with_stock.loc[x.index, 'ClosingBalance'].sum()
}).round(2)

slowest_movers = product_metrics.merge(product_stock, on='Product', how='inner')
slowest_movers = slowest_movers.sort_values(['Days_Since_Last', 'Transaction_Frequency'], ascending=[False, True])

print("\nRanked by Days Since Last Transaction & Movement Frequency:")
print("-" * 80)
print(f"{'Product':<25} {'Closing Bal':>12} {'Days Idle':>12} {'Avg Age':>10} {'Freq/Day':>10}")
print("-" * 80)

for idx, row in slowest_movers.head(10).iterrows():
    print(f"{str(row['Product'])[:24]:<25} {row['ClosingBalance']:>12,.2f} {row['Days_Since_Last']:>12} "
          f"{row['AgeNumeric']:>10.2f} {row['Transaction_Frequency']:>10.4f}")

print("\n" + "=" * 80)
print("4. KEY INSIGHTS")
print("=" * 80)

# Calculate overall statistics
total_bins = active_df['Bin'].nunique()
total_products = active_df['Product'].nunique()
avg_age_overall = (active_df['AgeNumeric'] * active_df['ClosingBalance']).sum() / active_df['ClosingBalance'].sum()
oldest_stock_pct = age_inventory.loc[age_inventory.index == '6+', 'Percentage'].values[0] if '6+' in age_inventory.index else 0

print(f"\n• Total Active Bins: {total_bins:,}")
print(f"• Total Unique Products: {total_products:,}")
print(f"• Overall Average Age: {avg_age_overall:.2f} days")
print(f"• Percentage of Stock 6+ days old: {oldest_stock_pct:.2f}%")
print(f"• Total Active Inventory Balance: {total_inventory:,.2f}")

# Identify problem areas
critical_bins = bin_stats[bin_stats['Avg_Age_Days'] > 5].shape[0]
critical_products = slowest_movers[slowest_movers['Days_Since_Last'] > 5].shape[0]

print(f"\n! ATTENTION NEEDED:")
print(f"   - {critical_bins} bins have average age > 5 days")
print(f"   - {critical_products} products haven't moved in > 5 days")

# Save the report to a text file
report_output = os.path.join(aged_bins_dir, f'summary_report_{datetime.now().strftime("%Y-%m-%d_%H%M%S")}.txt')
with open(report_output, 'w') as f:
    # Redirect output to file
    import sys
    original_stdout = sys.stdout
    sys.stdout = f
    
    # Re-run the print statements (simplified version)
    print("=" * 80)
    print("INVENTORY AGING SUMMARY REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Data Source: {latest_file}")
    print(f"Total Transactions: {len(df):,}")
    print("=" * 80)
    
    print("\n1. AVERAGE AGE PER BIN (Top 15)")
    print("-" * 80)
    print(f"{'Bin':<20} {'Total Inventory':>18} {'Avg Age (days)':>20}")
    print("-" * 80)
    for idx, (bin_name, row) in enumerate(bin_stats.head(15).iterrows(), 1):
        print(f"{idx:2}. {bin_name:<15} {row['Total_Inventory']:>18,.2f} {row['Avg_Age_Days']:>20.2f}")
    
    print("\n2. TOTAL INVENTORY BY AGE CATEGORY")
    print("-" * 80)
    print(f"{'Age Category':<15} {'Total Inventory':>18} {'Entries':>12} {'Percentage':>12}")
    print("-" * 80)
    for age_cat, row in age_inventory.iterrows():
        print(f"{age_cat:<15} {row['Total_Inventory']:>18,.2f} {int(row['Num_Entries']):>12,} {row['Percentage']:>11.2f}%")
    print(f"\n{'TOTAL':<15} {total_inventory:>18,.2f} {int(age_inventory['Num_Entries'].sum()):>12,} {'100.00':>11}%")
    
    print("\n3. TOP 10 SLOWEST-MOVING PRODUCTS")
    print("-" * 80)
    print(f"{'Product':<25} {'Closing Bal':>12} {'Days Idle':>12} {'Avg Age':>10} {'Freq/Day':>10}")
    print("-" * 80)
    for idx, row in slowest_movers.head(10).iterrows():
        print(f"{str(row['Product'])[:24]:<25} {row['ClosingBalance']:>12,.2f} {row['Days_Since_Last']:>12} "
              f"{row['AgeNumeric']:>10.2f} {row['Transaction_Frequency']:>10.4f}")
    
    print("\n4. KEY INSIGHTS")
    print("-" * 80)
    print(f"• Total Active Bins: {total_bins:,}")
    print(f"• Total Unique Products: {total_products:,}")
    print(f"• Overall Average Age: {avg_age_overall:.2f} days")
    print(f"• Percentage of Stock 6+ days old: {oldest_stock_pct:.2f}%")
    print(f"• Total Active Inventory Balance: {total_inventory:,.2f}")
    print(f"\n! ATTENTION NEEDED:")
    print(f"   - {critical_bins} bins have average age > 5 days")
    print(f"   - {critical_products} products haven't moved in > 5 days")
    
    sys.stdout = original_stdout

print("\n" + "=" * 80)
print(f"Report saved to: {report_output}")
print("=" * 80)

# Also save detailed CSV reports
bin_stats_csv = os.path.join(aged_bins_dir, f'bin_statistics_{datetime.now().strftime("%Y-%m-%d")}.csv')
bin_stats.to_csv(bin_stats_csv)
print(f"Bin statistics saved to: {bin_stats_csv}")

slowest_csv = os.path.join(aged_bins_dir, f'slowest_movers_{datetime.now().strftime("%Y-%m-%d")}.csv')
slowest_movers.to_csv(slowest_csv, index=False)
print(f"Slowest-moving products saved to: {slowest_csv}")

print("\nAll reports generated successfully!")

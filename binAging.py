import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

fn = 'quantified_transactions/transactions.csv'
df = pd.read_csv(fn)

# Ensure headings are coming from the first row only (default of read_csv already skips them as data)
# Re-map using 0-based indices as per your spec:
# 0: TransactionID (Transaction)
# 1: TransactionType (mtype)
# 3: Bin (loc_name)
# 5: Product (pk)
# 6: TransactionDate (moveDate)
# 7: TransactionQty (moveQty)

mapped = pd.DataFrame({
    'TransactionID': df.iloc[:, 0],
    'TransactionType': df.iloc[:, 1],
    'Bin': df.iloc[:, 3],
    'Product': df.iloc[:, 5],
    'TransactionDate': df.iloc[:, 6],
    'TransactionQty': df.iloc[:, 7]
})

mapped['TransactionDate'] = pd.to_datetime(mapped['TransactionDate'], format='%Y-%m-%d')

# Sort by date (and TransactionID for determinism)
mapped = mapped.sort_values(['TransactionDate', 'TransactionID']).reset_index(drop=True)

from collections import defaultdict, deque
fifo_layers = defaultdict(deque)  # (Bin, Product) -> deque([qty, date])

records = []

for _, row in mapped.iterrows():
    key = (row['Bin'], row['Product'])
    tdate = row['TransactionDate']
    qty = float(row['TransactionQty'])

    opening = sum(q for q, d in fifo_layers[key])

    if qty > 0:
        fifo_layers[key].append([qty, tdate])
    elif qty < 0:
        remaining = -qty
        while remaining > 0 and fifo_layers[key]:
            layer_qty, layer_date = fifo_layers[key][0]
            if layer_qty <= remaining:
                remaining -= layer_qty
                fifo_layers[key].popleft()
            else:
                fifo_layers[key][0][0] = layer_qty - remaining
                remaining = 0

    closing = sum(q for q, d in fifo_layers[key])

    # Determine single Age band label for remaining stock
    if closing <= 0:
        age_label = '0'
    else:
        # Compute weighted average age by quantity
        total_qty = 0.0
        total_age_days = 0.0
        for layer_qty, layer_date in fifo_layers[key]:
            days = (tdate - layer_date).days
            total_qty += layer_qty
            total_age_days += layer_qty * days
        avg_age = total_age_days / total_qty if total_qty > 0 else 0

        if avg_age <= 1:
            age_label = '0 to 1'
        elif avg_age <= 3:
            age_label = '2 to 3'
        elif avg_age <= 5:
            age_label = '4 to 5'
        else:
            age_label = '6+'

    records.append({
        'TransactionID': row['TransactionID'],
        'Bin': row['Bin'],
        'Product': row['Product'],
        'TransactionDate': tdate,
        'TransactionType': row['TransactionType'],
        'TransactionQty': qty,
        'OpeningBalance': opening,
        'ClosingBalance': closing,
        'Age': age_label
    })

out_df = pd.DataFrame(records)

os.makedirs('Aged_Bins', exist_ok=True)
start_date = mapped['TransactionDate'].min().strftime('%Y-%m-%d')
out_path = os.path.join('Aged_Bins', f'binAgingFrom{start_date}.csv')
out_df.to_csv(out_path, index=False)

print(f"\nData saved to: {out_path}")
print(f"Total transactions processed: {len(out_df)}")

# VISUALIZATION
print("\nGenerating visualizations...")

# Filter to only rows with closing balance > 0 for aging analysis
active_inventory = out_df[out_df['ClosingBalance'] > 0].copy()

# 1. Pie Chart - Overall Age Distribution
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Inventory Aging Analysis', fontsize=16, fontweight='bold')

age_counts = active_inventory['Age'].value_counts()
age_order = ['0 to 1', '2 to 3', '4 to 5', '6+', '0']
age_counts = age_counts.reindex([a for a in age_order if a in age_counts.index], fill_value=0)

colors = ['#2ecc71', '#f39c12', '#e67e22', '#e74c3c', '#95a5a6']
axes[0, 0].pie(age_counts.values, labels=age_counts.index, autopct='%1.1f%%', 
               colors=colors, startangle=90)
axes[0, 0].set_title('Distribution of Inventory by Age Category')

# 2. Stacked Area Chart - Aging Trends Over Time
age_over_time = active_inventory.groupby(['TransactionDate', 'Age'])['ClosingBalance'].sum().unstack(fill_value=0)
age_over_time = age_over_time.reindex(columns=[a for a in age_order if a in age_over_time.columns], fill_value=0)

axes[0, 1].stackplot(age_over_time.index, 
                     *[age_over_time[col] for col in age_over_time.columns],
                     labels=age_over_time.columns, colors=colors[:len(age_over_time.columns)], alpha=0.8)
axes[0, 1].set_title('Inventory Aging Trends Over Time')
axes[0, 1].set_xlabel('Date')
axes[0, 1].set_ylabel('Total Closing Balance')
axes[0, 1].legend(loc='upper left')
axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
axes[0, 1].tick_params(axis='x', rotation=45)
axes[0, 1].grid(True, alpha=0.3)

# 3. Bar Chart - Top 10 Bins with Oldest Inventory (6+ days)
oldest_stock = active_inventory[active_inventory['Age'] == '6+']
bin_old_stock = oldest_stock.groupby('Bin')['ClosingBalance'].sum().sort_values(ascending=False).head(10)

if not bin_old_stock.empty:
    axes[1, 0].barh(range(len(bin_old_stock)), bin_old_stock.values, color='#e74c3c')
    axes[1, 0].set_yticks(range(len(bin_old_stock)))
    axes[1, 0].set_yticklabels(bin_old_stock.index)
    axes[1, 0].set_xlabel('Total Closing Balance (6+ days old)')
    axes[1, 0].set_title('Top 10 Bins with Oldest Inventory')
    axes[1, 0].grid(True, alpha=0.3, axis='x')
else:
    axes[1, 0].text(0.5, 0.5, 'No inventory aged 6+ days', 
                    ha='center', va='center', fontsize=12)
    axes[1, 0].set_title('Top 10 Bins with Oldest Inventory')

# 4. Grouped Bar Chart - Age Distribution by Top Bins
top_bins = active_inventory.groupby('Bin')['ClosingBalance'].sum().sort_values(ascending=False).head(8).index
bin_age_dist = active_inventory[active_inventory['Bin'].isin(top_bins)].groupby(['Bin', 'Age'])['ClosingBalance'].sum().unstack(fill_value=0)
bin_age_dist = bin_age_dist.reindex(columns=[a for a in age_order if a in bin_age_dist.columns], fill_value=0)

bin_age_dist.plot(kind='bar', stacked=False, ax=axes[1, 1], color=colors[:len(bin_age_dist.columns)], width=0.8)
axes[1, 1].set_title('Age Distribution Across Top 8 Bins')
axes[1, 1].set_xlabel('Bin')
axes[1, 1].set_ylabel('Total Closing Balance')
axes[1, 1].legend(title='Age Category', bbox_to_anchor=(1.05, 1), loc='upper left')
axes[1, 1].tick_params(axis='x', rotation=45)
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
chart_path = os.path.join('Aged_Bins', f'aging_analysis_{start_date}.png')
plt.savefig(chart_path, dpi=300, bbox_inches='tight')
print(f"Visualization saved to: {chart_path}")

# Additional standalone chart - Inventory Level Trends
fig2, ax = plt.subplots(figsize=(14, 6))
total_inventory = out_df.groupby('TransactionDate')['ClosingBalance'].sum()
ax.plot(total_inventory.index, total_inventory.values, linewidth=2, color='#3498db', marker='o', markersize=3)
ax.fill_between(total_inventory.index, total_inventory.values, alpha=0.3, color='#3498db')
ax.set_title('Total Inventory Level Over Time', fontsize=14, fontweight='bold')
ax.set_xlabel('Date')
ax.set_ylabel('Total Closing Balance')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.tick_params(axis='x', rotation=45)
ax.grid(True, alpha=0.3)
plt.tight_layout()

trend_path = os.path.join('Aged_Bins', f'inventory_trend_{start_date}.png')
plt.savefig(trend_path, dpi=300, bbox_inches='tight')
print(f"Inventory trend chart saved to: {trend_path}")

print("\n=== Analysis Complete ===")
print(f"Charts generated: 2 files in Aged_Bins folder")

out_path, out_df.head(5).to_dict(orient='records')
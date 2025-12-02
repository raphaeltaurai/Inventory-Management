# Overview

I have been working in retail for a while now, and I have always been curious about how inventory moves through our warehouse bins. I wanted to challenge myself to build something practical that could actually help me understand our stock better, so I decided to dive into data analysis using Python. This project has been a great way to sharpen my programming skills while solving a real problem I see at work every day. The dataset I am analyzing comes from my workplace - a retail store where I got permission to export transaction and inventory data. The dataset includes two main CSV files, one tracking all inventory transactions (purchases, sales, transfers) and another showing current quantities on hand for each product in different warehouse locations. The data spans 2 days and includes thousands of transactions across multiple bins and products.

[Software Demo Video](https://youtu.be/sRb6__vPAew)

# How to Run the Analysis

The project runs in three sequential steps. Either run all steps at once or execute them individually:

**Option 1: Run Everything (Recommended)**

python runAll.py

This master script runs all three steps automatically and provides progress updates.

**Option 2: Run Steps Individually**

1. **Data Preparation** Merges transaction and quantity data:
   
   python quantities.py
   

2. **Aging Analysis & Visualization** Calculates FIFO aging and generates charts:
   
   python binAging.py
   

3. **Summary Report** Generates detailed statistics and insights:
   
   python summaryReport.py
   

All output files (CSV reports, charts, and text summaries) are saved in the `Aged_Bins` folder.

# Data Analysis Results

**Question 1: Which bins contain the oldest inventory, and how is stock distributed across different age categories?**

After running the analysis, I found that several bins have stock that has been sitting there for 6+ days, which is our oldest age category. The FIFO aging system I built categorizes inventory into age bands: 0-1 days (fresh), 2-3 days, 4-5 days, and 6+ days (aging stock). By grouping the data by bin and age category, I discovered that certain bins consistently hold older inventory, which suggests those locations might be harder to access or contain slower-moving products. This was really eye-opening because it shows exactly where we need to focus our stock rotation efforts.

**Question 2: How do opening and closing balances change over time for each bin-product combination?**

This one was interesting. By sorting all transactions chronologically and calculating running balances, I could see the flow of inventory in and out of each bin. Some bins show steady movement with balanced ins and outs, while others accumulate stock over time without much outflow. The data revealed patterns where certain products get stuck in specific locations, building up inventory that just sits there. This helps identify which bin-product combinations are problematic and might need better placement or merchandising strategies.

**Question 3: What types of transactions are most common, and how do they impact inventory levels?**

Looking at the TransactionType field, I aggregated transactions by type to see the distribution. The majority are standard sales (negative quantities) and restocks (positive quantities), but there are also transfers between bins. By counting and averaging transaction quantities by type, I found that transfers tend to be smaller quantities compared to direct restocks, and certain transaction types correlate with specific age patterns. This helps understand how different operational activities affect our inventory aging.

# Development Environment

I used Visual Studio Code as my main editor because it's what I'm most comfortable with, and it has great Python support. I ran everything locally on my Windows machine using PowerShell for terminal commands. For version control, I'm using Git and have the project hosted on GitHub, which has been helpful for tracking my changes as I iterate on the code.

I chose Python because of its strong data analysis libraries. I used the built-in `csv` module for the initial data merging in `quantities.py`, which joins the transaction data with the quantity-on-hand data. For the more complex aging analysis in `binAging.py`, I relied heavily on Pandas for data manipulation which includes reading CSVs, datetime conversion, sorting, grouping, and DataFrame operations. I also used Python's `collections` module (specifically `defaultdict` and `deque`) to implement the FIFO inventory layers efficiently. The `os` module helped me create output directories and manage file paths programmatically. For data visualization, I incorporated Matplotlib to generate charts showing inventory aging trends over time, age distribution across bins, and overall inventory levels. This makes the analysis results much easier to understand at a glance. I also created a separate summary report script (`summaryReport.py`) that generates comprehensive statistics including weighted average ages per bin, inventory breakdowns by age category, and identifies the top 10 slowest-moving products based on transaction frequency and idle time.

# Useful Websites

* [Pandas Official Documentation](https://pandas.pydata.org/docs/)
* [Stack Overflow](https://stackoverflow.com/)
* [Real Python - Pandas Tutorials](https://realpython.com/learning-paths/pandas-data-science/)
* [Python CSV Module Docs](https://docs.python.org/3/library/csv.html)
* [GeeksforGeeks - Python Collections](https://www.geeksforgeeks.org/python-collections-module/)

# Future Work
* Implement error handling for edge cases like missing data or malformed CSV entries - right now the code assumes clean data
* Optimize the FIFO calculation performance - for larger datasets, the nested loops might get slow, so I could look into vectorized operations
* Add command-line arguments so I can specify input files and date ranges without editing the code directly
* Build a simple dashboard or web interface where managers could upload new data and see results without running Python scripts
* Add interactive visualizations using Plotly so users can zoom and filter the charts dynamically
* Incorporate actual product pricing data to calculate monetary value of aged inventory instead of just quantities
* Add email notification system to alert managers when critical bins exceed age thresholds
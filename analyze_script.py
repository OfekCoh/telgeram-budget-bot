import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import sys

#using Pandas for data manipulation and analysis, and Matplotlib for creating visual summaries of the data (e.g., charts, graphs).

# Define a function to parse dates in the format "yyyy-mm-dd" and ignore the time component
def date_parser(s):
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")

excel_file_name = sys.argv[1]  # Get the Excel file name from command-line argument

# Read the Excel file and parse the 'Date' column as datetime with the specified date parser function
df = pd.read_excel(excel_file_name, parse_dates=['Date'], date_parser=date_parser)

# Get the user's ID from the filename (assuming the filename is 'user_{user_id}_expenses.xlsx')
user_id = int(os.path.basename(excel_file_name).split('_')[1])

# Create a folder for the user if it doesn't exist
user_folder = f'user_{user_id}_images'
os.makedirs(user_folder, exist_ok=True)

# Clear existing images (if any)
for existing_image in os.listdir(user_folder):
    os.remove(os.path.join(user_folder, existing_image))

# Group expenses by category
category_totals = df.groupby('Category')['Amount'].sum()

# Create a bar chart and save it
bar_chart_path = os.path.join(user_folder, 'expenses_by_category.png')
category_totals.plot(kind='bar')
plt.title('Expenses by Category')
plt.xlabel('Category')
plt.ylabel('Amount')
plt.savefig(bar_chart_path)
plt.close()

# ... (similarly create and save other charts)

# Loop through the months and create and save pie charts for each month
grouped = df.groupby([pd.Grouper(key='Date', freq='M'), 'Category'])['Amount'].sum().reset_index()
for month in grouped['Date'].unique():
    df_month = grouped[grouped['Date'] == month]
    month_datetime = pd.Timestamp(month).to_pydatetime()
    plt.figure()
    plt.pie(df_month['Amount'], labels=df_month['Category'], autopct='%1.1f%%')
    plt.title(month_datetime.strftime('%B %Y'))
    pie_chart_path = os.path.join(user_folder, f'expenses_pie_{month_datetime.strftime("%Y%m")}.png')
    plt.savefig(pie_chart_path)
    plt.close()

print("Images saved successfully.")

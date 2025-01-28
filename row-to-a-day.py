import pandas as pd

# Define a function to preprocess and handle different date formats and Excel-style serial dates
def parse_dates(value):
    
    # Define a list of formats to try
    formats = ['%Y%m%d', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']
    
    # Iterate through each format and try to convert
    for date_format in formats:
        # Convert using the current format, coerce invalid values to NaT
        try:
            parsed_date = pd.to_datetime(value, format=date_format, errors='coerce')
            if pd.notna(parsed_date):
                return parsed_date
        except Exception as e:
            pass
        
    # If the value is numeric (int or float), treat it as an Excel serial date
    if isinstance(value, (int, float)):
        try:
            # Convert using Excel serial date handling (origin: '1900-01-01') and adjust for 1 day mistake in Excel
            return pd.to_datetime(value, errors='coerce', origin='1900-01-01', unit='D')  - pd.Timedelta(days=1)
        except Exception as e:
            return pd.NaT  # Return NaT if serial date parsing fails
    
     # If no format worked, fallback to pandas' default to_datetime
    try:
        return pd.to_datetime(value, errors='coerce')
    except Exception as e:
        return pd.NaT  # Return NaT if parsing fails after all attempts

# Read CSV file into a DataFrame
csv_path = "E:\\Learning Python\\multi time test 2.csv"
df = pd.read_csv(csv_path, header = 0)

# Drop columns that are completely filled with NaNs
df = df.dropna(axis=1, how='all')

# Drop rows that are completely filled with NaNs
df = df.dropna(axis=0, how='all')

user_use_filter = input("Use a filter on first column?\n Enter Y or N: ")

filter_in_use = False
filter_value = '0'

if user_use_filter.lower() in ['y', 'yes', 'yeah', 'ok', 'okay']:
    filter_value = input("Enter filter value/text: ")
    filter_in_use = True
    print(f'"{filter_value}" will be used as the filter.')

if filter_in_use:
    # Create df with filtered rows and then drop the filter column
    df[df.columns[0]] = df[df.columns[0]].astype(str)
    filter_value = str(filter_value)
    df = df[df[df.columns[0]] == filter_value]
    df.drop(df.columns[0], axis=1, inplace=True)

# Convert date column to date values and sort data (first column in the file, ideal format d/m/yyyy)
df[df.columns[0]] = df[df.columns[0]].apply(parse_dates)
df = df.dropna(subset=[df.columns[0]])
df.sort_values(by = df.columns[0])

# Check row lengths
df['row_lengths'] = df.count(axis=1) - 1
common_length = df['row_lengths'].value_counts().idxmax()

# Keep all rows that have the same row length as the most common row length
df = df[df['row_lengths'] == common_length]

# Check the number of required columns by calculating the time interval and then remove the extra columns
time_interval = round(1440/common_length)
keep_column = int((1440/time_interval) + 1) # +1 for adjusting for the first date column 
df = df.iloc[:, :keep_column]

# Sum kWh values of all duplicate days
df_sum = df.groupby(df.columns[0], as_index = False).sum()
df_sum.sort_values(by = df_sum.columns[0], inplace = True)

# Select first and last indices where time intervals match the most common time interval
first_day = df.iloc[0, 0]
last_day = df.iloc[-1, 0]

# Create a new dataframe with range between the start and end date identified above
print(f"Creating a new file starting from {first_day.date()} and ending on {last_day.date()} with a time interval of {time_interval} minutes.")

date_values = pd.date_range(start = first_day, end = last_day, freq = 'D')

new_df = pd.DataFrame({
 df_sum.columns[0]: date_values
})

# Copy kWh values from previous dataframe to the new dataframe
new_df = pd.merge(new_df, df_sum, left_on = new_df.columns[0], right_on = df_sum.columns[0], how = "left")

# Notify number of missing datapoints or NaNs
print(f"{new_df.isna().all().sum()} consumption records were missing. They will be filled with the consumption value of their respective preceding day's timestamps.")

# Change all columns except the first date column to numeric
new_df.iloc[:, 1:] = new_df.iloc[:, 1:].apply(pd.to_numeric, errors='coerce').round(4)

# Create a mask for rows that checks if all values after the first column are NaN (applies to dates missing from original dataset)
mask = new_df.iloc[:, 1:].isna().all(axis=1)

# Copy the previous day's (row's) values where the mask is True
for i in range(1, len(new_df)):  # Start from the second row (index 1)
    if mask.iloc[i]:  # Check if the mask is True for this row
        new_df.iloc[i, 1:] = new_df.iloc[i - 1, 1:]  # Copy data from the previous row

# Apply forward fill to fill other NaNs along the rows
new_df = new_df.fillna(method = "ffill", axis=1)

# Set the date format as YYYYMMDD
new_df[new_df.columns[0]] = new_df[new_df.columns[0]].dt.strftime('%Y%m%d')

# Add the filter column
if filter_in_use:
    new_df.insert(0, 'filter', filter_value)
else:
    new_df.insert(0, 'filter', 300)

# Export as CSV
new_df.set_index(new_df.columns[0], inplace=True)

filename = csv_path.split("\\")[-1].split(".")[0]
new_df.to_csv(f'{filename} - edited.csv', sep=",")

print("The edited file has been exported.")

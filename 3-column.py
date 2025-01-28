import pandas as pd

def convert_date(value):
    # Check if the value is numeric (Excel-style serial date)
    if isinstance(value, str):
         # Try to convert the string to a float (in case it's a serial number in string format)
        try:
            value = float(value)
        except ValueError:
            # If the conversion fails, it means it's a date in string format
            return pd.to_datetime(value, dayfirst = True, format = "mixed", errors='coerce')
    
    # Now that the value is numeric, handle the Excel serial dates
    if isinstance(value, (int, float)):
        return pd.to_datetime(value, origin='1900-01-01', unit='D') - pd.Timedelta(days=1)
    
    # If we reach here, something is wrong with the value type
    return pd.NaT  # Return Not a Time (NaT) for any invalid case

# Read CSV file into a DataFrame
csv_path = "E:\\Learning Python\\3 column test.csv"
df = pd.read_csv(csv_path, header = 0)

# Check that the CSV has only 3 columns
if len(df.columns) == 3:
    print("CSV file loaded successfully.")
else:
    raise ValueError(f"Error: The CSV file has {len(df.columns)} columns, but only 3 columns are allowed. The 3 columns should be [Date | time | kWh]")

# Add new datetime concat column and rearrange the columns
df['DT'] = df[df.columns[0]] + ' ' + df[df.columns[1]]
df = df.iloc[:, [3,2,0,1]]

# Convert datetime column to datetime values and sort data
df.iloc[:,0] = df.iloc[:,0].apply(convert_date)
df.dropna(subset=[df.columns[0]], inplace=True)
df.sort_values(by = df.columns[0])

# Sum kWh values of all duplicate datetime stamps
df_sum = df.groupby(df.columns[0], as_index = False).sum()
df_sum.sort_values(by = df_sum.columns[0], inplace = True)

# Check time interval difference between consecutive rows and set the first row time difference same as 2nd row (since it returns NaT otherwise)
df_sum['time-diff'] = df_sum[df_sum.columns[0]].diff()
df_sum.loc[0, 'time-diff'] = df_sum.loc[1, 'time-diff']

# Choose the most common time interval gap (in case of multiple time intervals in the file) 
time_diff = df_sum['time-diff'].value_counts().idxmax()

# Select timestamp of first and last row that has the same time difference as the most common time interval gap
first_same_time_diff = df_sum[df_sum['time-diff'] == time_diff].iloc[0, 0]
last_same_time_diff = df_sum[df_sum['time-diff'] == time_diff].iloc[-1, 0]

# Create a new dataframe with start and end date and time identified above with the most common time interval step
print(f"Creating a new file starting from {first_same_time_diff} and ending on {last_same_time_diff} with a timestep of {time_diff.total_seconds() / 60} minutes.")

time_values = pd.date_range(start = first_same_time_diff, end = last_same_time_diff, freq = time_diff)

new_df = pd.DataFrame({
 df_sum.columns[0]: time_values
})

# Copy kWh values from old dataframe to the new dataframe where datetime stamps match
new_df = pd.merge(new_df, df_sum[[df_sum.columns[0], df_sum.columns[1]]], left_on = new_df.columns[0], right_on = df_sum.columns[0], how = "left")

# Fill NaN or missing interval values with last interval's valid value
print(f"{new_df[new_df.columns[1]].isna().sum()} consumption records were missing. They will be filled with the consumption value of their respective preceding timestamps.")
new_df[new_df.columns[1]] = pd.to_numeric(new_df[new_df.columns[1]], errors='coerce').round(4)
new_df[new_df.columns[1]] = new_df[new_df.columns[1]].fillna(method = "ffill")

# Split datetime column into 2 separate columns, drop the single datetime column, and rearrange columns to create a 3 column file
new_df[[df.columns[2], df.columns[3]]] = new_df[new_df.columns[0]].astype(str).str.split(' ', expand=True)
new_df.drop(columns=[new_df.columns[0]], inplace=True)
new_df = new_df.iloc[:, [1,2,0]]

# Export new dataframe as a CSV file ready for upload
new_df.set_index(new_df.columns[0], inplace = True)

filename = csv_path.split("\\")[-1].split(".")[0]
new_df.to_csv(f'{filename} - edited.csv', sep=",")

print("The edited file has been exported.")
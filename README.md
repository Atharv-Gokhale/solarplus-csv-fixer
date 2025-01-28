# Consumption CSV file fixer for SolarPlus (solarplus-csv-fixer)

## Description
This repository contains 3 Python scripts that you can use for converting your CSV consumption files to the specific data formats that SolarPlus accepts.  
I have developed these scripts as an exercise to improve my Python skills with the help of ChatGPT. So if you have any suggestions or would like to contribute, feel free to do so.  

## How to use
You can simply clone the repository or copy the code from the Python files. The script relies on the basic functions supported by Pandas.

1. Clone the repo.
2. Set up a virtual environment.
3. Install dependencies using ```pip install -r requirements.txt```.

The input files **must** be in a CSV format.

The steps to use are similar for all 3 scripts. You just need to select the appropriate script for it:
* **2 column** - when the CSV file contains data in a format where you can cut down the content to just 2 columns - [Datetime] and [kWh or kW]
* **3 column** - when the CSV file contains data in a format where you can cut down the content to just 3 columns - [Date], [Time], and [kWh or kW]
* **row to a day** - when CSV file contains data in a format where the kWh or kW readings are recorded along the columns (for example, each date has 48 columns of records i.e. 30 min data)

**The steps are as follows:**
* Locate and edit the ```csv_path```
* Run the script  
  * for the ```row-to-a-day.py``` script, you'll be prompted for some inputs
    * type ```Y``` and press ```Enter``` on your keyboard if you want to use a filter, else type ```N``` and press  ```Enter```
      *use filter when you have an identifier in the first column of the CSV that can identify which rows have consumption data

## Data handling logic

### 2-column method
<img src="images/2-column-format.png" alt="2 column sample" width="30%" />

* The first 2 columns of the CSV file are read into a Pandas DataFrame
* First column is converted to a datetime value
* Duplicate datetime stamps are grouped into 1 value by summing their kWh or kW values
* The time invterval between each consecutive rows is checked
* Most common time interval is kept (for example, if there are 200 records with 30 min time intervals and 100 records with 5 min time intervals, 5 min records are removed - this is a common case and helps in handling inconsistent time intervals)
* Any missing kWh/kW values are set with the same value as their last valid predecessor value 

### 3-column method
<img src="images/3-column-format.png" alt="3 column sample" width="40%" /> 

* The first 3 columns of the CSV file are read into a Pandas DataFrame
* The first 2 columns of the dataframe are combined into 1 so that the format becomes the same as 2 column method to work with
* The rest of the data handling logic is the same as the 2-column method

### Row to a day method
#### First column has some IDs (needs for filters)
> **Note: If the first column has same IDs for all rows, you can enter that ID as the filter value**

![row to a day with filter sample](images/row-to-a-day-format-with-filter.png)
#### First column has dates (no need for filters)
![row to a day with no filter sample](images/row-to-a-day-format-no-filter.png)  

* Full CSV file is read into a Pandas DataFrame
* Empty rows are columns are deleted
* User is prompted to confirm whether a filter is to be used
  * If the user answers with ```Y```, a filter value needs to be passed
    * The DataFrame uses the filter value to keep only rows where the first column value matches the filter value - the rest of the rows are deleted
    * After filtering, the first column is then deleted. The first column is now expected to be the date column.
* The first column is converted to a datetime value
* A column count is made for each row (to figure out the time interval - 48 columns would mean 30 min time interval)
* Rows with the same column count as the most common column count (time interval) are kept while the rest of the rows are deleted
* To address cases where there are extra columns after the useful columns in the CSV file (like identifier column values that appear at the end of each row), the usable number of columns are calculated using the time interval identifed and all columns after the usable columns are deleted
* Any missing kWh/kW values are set with the same value as their last valid predecessor column's value
* Any missing days are set with the same values as the last valid day's values 

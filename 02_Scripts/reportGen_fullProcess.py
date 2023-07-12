import sys
import datetime
import numpy as np
import pandas as pd

# Step 1: Created filtered jtl files during tests steady states
sourceFile = (r"original_test.jtl")

# Open the source file for reading
with open(sourceFile, 'r') as source_file:
    # Read the contents of the source file
    content = source_file.readlines()

# Copy header and Remove it
header = content[0]
content = content[1:]

# Sort the contents based on timestamplen
sorted_content = sorted(content)

# Get the first and last timestamp in milliseconds
first_timestamp = int(sorted_content[0].split(",")[0])
last_timestamp = int(sorted_content[-1].split(",")[0])

Rampup_time = 60*1000  # 10 minutes in milliseconds
Rampdown_time = 60*1000  # 10 minutes in milliseconds
Slicetime_after_first = first_timestamp + Rampup_time
Slicetime_before_last = last_timestamp - Rampdown_time

print("First timestamp:", datetime.datetime.fromtimestamp(first_timestamp/1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
print("Last timestamp:", datetime.datetime.fromtimestamp(last_timestamp/1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])

print("Slicing time After First Timestamp:", datetime.datetime.fromtimestamp(Slicetime_after_first/1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
print("Slicing time before Last Timestamp:", datetime.datetime.fromtimestamp(Slicetime_before_last/1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])

# System Error if ramping time not within input window
if Slicetime_after_first > last_timestamp or Slicetime_before_last < first_timestamp:
    sys.exit("Error: Ramping time not within input window")
    
# Find row number with timestamp according to the conditions
for i in range(len(sorted_content)):
    if  int(sorted_content[i].split(",")[0]) > Slicetime_after_first :
        first_row = i
        break

for i in reversed(range(len(sorted_content))):
    if  int(sorted_content[i].split(",")[0]) < Slicetime_before_last :
        last_row = i
        break
    
filtered_content = sorted_content[first_row:last_row + 1]
print("\nLength of original content:",len(content))
print("Length of filtered content:",len(filtered_content))

# Write the filtered_content to the output file
with open(r"filtered.jtl", 'w') as output_file:
    output_file.write(header)
    output_file.writelines(filtered_content)

#-----------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------
# Step 2: Create a summary stats jtl for the filtered jtl files

data_df = pd.read_csv("filtered.jtl",sep=',')

# Define the aggregate functions

# Throughput per second give NaN if unique timeStamp available
# Received and sent bytes in Kb/s and give NaN if unique timeStamp available

agg_func = {
    'label': 'count',
    'elapsed' :['mean','median',lambda x: x.quantile(0.9),
                lambda x: x.quantile(0.95),
                lambda x: x.quantile(0.99),'min','max'],
    'success': lambda x: (1 - sum(x) / len(x)) * 100,
    'timeStamp': lambda x: (len(x) / (max(x) - min(x))) * 1000 if max(x) != min(x) else np.NaN,
    'bytes': lambda x: sum(x) / 1024 / (max(data_df.loc[x.index, 'timeStamp']) - min(data_df.loc[x.index, 'timeStamp'])) * 1000
    if max(data_df.loc[x.index, 'timeStamp']) != min(data_df.loc[x.index, 'timeStamp']) else np.NaN,
    'sentBytes': lambda x: sum(x) / 1024 / (max(data_df.loc[x.index, 'timeStamp']) - min(data_df.loc[x.index, 'timeStamp'])) * 1000
    if max(data_df.loc[x.index, 'timeStamp']) != min(data_df.loc[x.index, 'timeStamp']) else np.NaN
}

# Group the input dataframe data_df by 'label' and apply the aggregate functions
Summary_df = data_df.groupby('label').agg(agg_func)

# Flatten the hierarchical column index of the summary dataframe Summary_df
Summary_df.columns = ['_'.join(col).strip() for col in Summary_df.columns.values]

# Rename the columns of the summary dataframe Summary_df
Summary_df = Summary_df.rename(columns={
    'label_count': '# Samples',
    'elapsed_mean': 'Average',
    'elapsed_median': 'Median',
    'elapsed_<lambda_0>': '90% Line',
    'elapsed_<lambda_1>': '95% Line',
    'elapsed_<lambda_2>': '99% Line',
    'elapsed_min': 'Minimum',
    'elapsed_max': 'Maximum',
    'success_<lambda>': 'Error %',
    'timeStamp_<lambda>': 'Throughput /s',
    'bytes_<lambda>' : 'Received KB/s',
    'sentBytes_<lambda>' : 'Sent KB/s'
})

# Round columns to second decimal
Summary_df['Average'] = Summary_df['Average'].round(2)
Summary_df['Error %'] = Summary_df['Error %'].round(2)
Summary_df['Throughput /s'] = Summary_df['Throughput /s'].round(2)
Summary_df['Received KB/s'] = Summary_df['Received KB/s'].round(2)
Summary_df['Sent KB/s'] = Summary_df['Sent KB/s'].round(2)

Summary_df.to_csv('Summary.jtl', encoding='utf-8')

#-----------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------
# Step 3: Generate HTML Report based on Throughput and Response Time SLAs for endpoints

def filter_dataframe(df, sla_values):
    filtered_df = df[df['transactionName'].isin(sla_values.keys())].copy()
    return filtered_df

def add_sla_status(df, sla_values, sla_throughput_values):
    for transaction, sla_value in sla_values.items():
        filter_condition = df['transactionName'] == transaction
        df.loc[filter_condition, 'Response Time SLA Status'] = pd.cut(df.loc[filter_condition, 'responseTime'], bins=[float('-inf'), sla_value, sla_value*1.1, float('inf')], labels=['Pass', 'Amber', 'Fail'])
        df.loc[filter_condition, 'SampleCount SLA Status'] = df.loc[filter_condition, 'sampleCount'].apply(lambda x: 'Pass' if x >= sla_throughput_values.get(transaction, 0) else 'Amber' if x >= (0.9 * sla_throughput_values.get(transaction, 0)) else 'Fail')
    return df

# Example usage
input_filename = 'Summary.jtl'  # Replace with your input CSV file path
output_filename = 'summary_report.html'  # Output HTML file name

df = pd.read_csv(input_filename)

sla_avgResponseTime_values1 = {'t1': 3, 't2': 3}  # Define the SLA average response time values for the first set of transactions
sla_throughput_values1 = {'t1': 100, 't2': 102}  # Define the SLA throughput values for the first set of transactions

sla_avgResponseTime_values2 = {'t3': 3, 't4': 4}  # Define the SLA average response time values for the second set of transactions
sla_throughput_values2 = {'t3': 103, 't4': 115}  # Define the SLA throughput values for the second set of transactions

filtered_data1 = filter_dataframe(df, sla_avgResponseTime_values1)
filtered_data1 = add_sla_status(filtered_data1, sla_avgResponseTime_values1, sla_throughput_values1)

filtered_data2 = filter_dataframe(df, sla_avgResponseTime_values2)
filtered_data2 = add_sla_status(filtered_data2, sla_avgResponseTime_values2, sla_throughput_values2)

# Create HTML tables
html_table1 = filtered_data1[['transactionName', 'sampleCount', 'pass', 'responseTime', 'Response Time SLA Status', 'SampleCount SLA Status']].to_html(index=False)
html_table2 = filtered_data2[['transactionName', 'sampleCount', 'pass', 'responseTime', 'Response Time SLA Status', 'SampleCount SLA Status']].to_html(index=False)

# Modify HTML for collapsible tables
table_script1 = f'''
<script>
function toggleTable1() {{
  var table1 = document.getElementById("summaryTable1");
  table1.style.display = table1.style.display === "none" ? "table" : "none";
}}
</script>
'''

table_script2 = f'''
<script>
function toggleTable2() {{
  var table2 = document.getElementById("summaryTable2");
  table2.style.display = table2.style.display === "none" ? "table" : "none";
}}
</script>
'''

html_table1 = html_table1.replace('<table', '<table id="summaryTable1" style="border-collapse: collapse; display: none;"')
html_table2 = html_table2.replace('<table', '<table id="summaryTable2" style="border-collapse: collapse; display: none;"')

# Write HTML report to file
with open(output_filename, 'w') as file:
    file.write('<html>\n')
    file.write('<head>\n')
    file.write('<style>\n')
    file.write('table { border-collapse: collapse; }\n')
    file.write('</style>\n')
    file.write(table_script1)
    file.write(table_script2)
    file.write('</head>\n')
    file.write('<body>\n')
    file.write('<h1>Summary Report</h1>\n')

    file.write('<h2 onclick="toggleTable1()">Summary Table 1</h2>\n')
    file.write(html_table1)
    file.write('\n')

    file.write('<h2 onclick="toggleTable2()">Summary Table 2</h2>\n')
    file.write(html_table2)
    file.write('\n')

    file.write('</body>\n')
    file.write('</html>\n')

print(f"Filtered data with Response Time SLA status and SampleCount SLA status saved to {output_filename}")

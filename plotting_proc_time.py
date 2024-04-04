# Generic imports
import pandas as pd
import plotly
import plotly.graph_objects as go

# 5G visualization logic
import trace_plotting
import logging
import re

# Wireshark trace with 5GC messages
# wireshark_trace = 'doc/free5gc.pcap'
wireshark_trace = 'pcaps/fast2.pcap'


if isinstance(wireshark_trace, list):
    output_name_files = wireshark_trace[0]
else:
    output_name_files = wireshark_trace
output_name_files = '.'.join(output_name_files.split('.')[0:-1])

# DEBUG loggig level for big traces so that you can see if processing is stuck or not
packets_df = trace_plotting.import_pcap_as_dataframe(
    wireshark_trace, 
    http2_ports = "32445,5002,5000,32665,80,32077,5006,8080,3000,8081",
    wireshark_version = '4.2.3',
    logging_level=logging.INFO,
    remove_pdml=True)

print(packets_df)

procedure_df, procedure_frames_df = trace_plotting.calculate_procedure_length(packets_df)
pd.set_option('display.max_rows', 10)
# display(procedure_df)

print('Average procedure length (ms)')
mean_values = procedure_df.groupby('name')['length_ms'].mean()
min_values = procedure_df.groupby('name')['length_ms'].min()
max_values = procedure_df.groupby('name')['length_ms'].max()
count_values = procedure_df.groupby('name')['length_ms'].count()
summary_values = mean_values.reset_index()
summary_values = summary_values.rename(columns={'length_ms':'mean_procedure_time_ms'})
summary_values['min_procedure_time_ms'] = min_values.reset_index()['length_ms']
summary_values['max_procedure_time_ms'] = max_values.reset_index()['length_ms']
summary_values['count'] = count_values.reset_index()['length_ms']
summary_values = summary_values.set_index('name')
print(summary_values)
with open(output_name_files + '_summary.txt', 'w') as f:
    f.write(summary_values.to_string())
# display(procedure_df)
# display(procedure_frames_df)

import plotly.graph_objects as go

bin_size = 3

procedure_names = list(procedure_df['name'].unique())
procedure_names.sort()
histogram_traces = []

for procedure_name in procedure_names:
    proc_data = procedure_df[procedure_df['name']==procedure_name]
    hist_array, hist_bins, hist_labels = trace_plotting.get_histogram_data(
        proc_data.loc[:,'length_ms'], 
        bin_size, 
        density=False, 
        remove_trailing_zeros=False, 
        output_labels=True,
        label_unit='ms')
    histogram_line = go.Bar(
        x=hist_bins,
        y=hist_array,
        name=procedure_name,
        text=hist_labels,
        opacity=0.65,
        showlegend=True,
        #marker={'line':{'width':0}},
        hovertemplate="<br>".join([
            "duration: %{text}",
            "occurrences: %{y}"])
    )
    histogram_traces.append(histogram_line)

fig = go.Figure(data=histogram_traces, layout = { 'bargap': 0 })

fig.update_layout(barmode='overlay')
fig.update_xaxes(title_text='Procedure length (ms)')
fig.update_yaxes(title_text='Occurrence')
fig.show()

fig.write_html(output_name_files + '_procedure_length.html')

plot_data = trace_plotting.generate_scatterplots_for_wireshark_traces(
    procedure_df, 
    filter_column='name', 
    datetime_column='start_datetime', 
    summary_column='length_ms', 
    protocol_column='name', 
    frame_number_column='start_frame', 
    auto_color=True,
    y_unit='ms',
    hide_series=False,
    opacity=0.65)
fig = go.Figure(data=plot_data)
fig.update_yaxes(title_text='Procedure length (ms)')
fig.show()

fig.write_html(output_name_files + '_procedure_timeline.html')
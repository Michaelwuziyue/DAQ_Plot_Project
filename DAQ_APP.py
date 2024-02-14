import sqlite3
import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.express as px
import base64
from dash.exceptions import PreventUpdate
from dash.dash_table import DataTable
import io
import csv
import time
import sys
from dash import dcc, html, dash_table, dcc, Output, State
import tempfile
import os



# CSS styling for the green buttons
button_style = {
    'border': 'none',
    'backgroundColor': '#4CAF50',
    'color': 'white',
    'padding': '10px 20px',
    'textAlign': 'center',
    'text-decoration': 'none',
    'display': 'inline-block',
    'fontSize': '16px',
    'borderRadius': '4px',
    'cursor': 'pointer',
    'width': '50%'  # Set the width to 50% for both buttons
}

# Function to connect to the database and fetch data
def fetch_data(database_file):
    try:
        connection = sqlite3.connect(database_file)
        query = "SELECT Local_TimeStamp, Name, Value FROM NewTable;"
        result_df = pd.read_sql_query(query, connection)
        result_df['Local_TimeStamp'] = pd.to_datetime(result_df['Local_TimeStamp'], errors='coerce')
        connection.close()
        return result_df
    except sqlite3.Error as e:
        print(f"Error fetching data from {database_file}: {e}")
        return pd.DataFrame()

# Get the output database file name from the command-line arguments
output_db_file = None

# Create Dash app with suppress_callback_exceptions=True
app = dash.Dash(__name__, suppress_callback_exceptions=True)


# App layout
app.layout = html.Div(children=[
        html.Link(
        rel='stylesheet',
        href='https://use.fontawesome.com/releases/v5.8.1/css/all.css'
    ),
    # Left Panel (1/4 of the screen)
    html.Div([
        html.H1([
            html.Img(src='/assets/Saltworks-logomark.png', style={'height': '50px', 'verticalAlign': 'middle'}),
            " SQLite DB Viewer Rev: M.1"
        ], style={'color': '#000000', 'textAlign': 'center', 'marginBottom': '20px'}),

        


        # Start Date and Time Selection
        html.Div(style={'display': 'flex', 'marginBottom': '20px'}, children=[
            # Container for Start Date
            html.Div(style={'flex': '1'}, children=[
                html.Label("Select Start Date:", style={'display': 'block'}),
                dcc.DatePickerSingle(
                    id='start-date-picker',
                    date=None,
                    display_format='YYYY-MM-DD',
                    style={'width': '100%'}
                ),
            ]),

            # Container for Start Hour
            html.Div(style={'flex': '1'}, children=[
                html.Label("Start Hour:", style={'display': 'block'}),
                dcc.Dropdown(
                    id='start-hour-picker',
                    options=[{'label': str(h), 'value': str(h).zfill(2)} for h in range(24)],
                    value='00',
                    style={'width': '100%'}
                ),
            ]),

            # Container for Start Minute
            html.Div(style={'flex': '1'}, children=[
                html.Label("Start Minute:", style={'display': 'block'}),
                dcc.Dropdown(
                    id='start-minute-picker',
                    options=[{'label': str(m), 'value': str(m).zfill(2)} for m in range(60)],
                    value='00',
                    style={'width': '100%'}
                ),
            ]),
        ]),

        # End Date and Time Selection
        html.Div(style={'display': 'flex', 'marginBottom': '20px'}, children=[
            # Container for End Date
            html.Div(style={'flex': '1'}, children=[
                html.Label("Select End Date:", style={'display': 'block'}),
                dcc.DatePickerSingle(
                    id='end-date-picker',
                    date=None,
                    display_format='YYYY-MM-DD',
                    style={'width': '100%'}
                ),
            ]),

            # Container for End Hour
            html.Div(style={'flex': '1'}, children=[
                html.Label("End Hour:", style={'display': 'block'}),
                dcc.Dropdown(
                    id='end-hour-picker',
                    options=[{'label': str(h), 'value': str(h).zfill(2)} for h in range(24)],
                    value='23',
                    style={'width': '100%'}
                ),
            ]),

            # Container for End Minute
            html.Div(style={'flex': '1'}, children=[
                html.Label("End Minute:", style={'display': 'block'}),
                dcc.Dropdown(
                    id='end-minute-picker',
                    options=[{'label': str(m), 'value': str(m).zfill(2)} for m in range(60)],
                    value='59',
                    style={'width': '100%'}
                ),
            ]),
        ]),




        # Adjusted part for the Dropdown
        dcc.Loading(
            id="name-dropdown-loading",
            type="default",
            children=[
                html.Div([  # Wrapper Div for the Dropdown
                    dcc.Dropdown(
                        id='name-dropdown',
                        options=[],
                        value=None,
                        multi=True,
                        placeholder="Click and Scroll Down to Select instrument(s)",
                        searchable=True,
                        style={'width': '100%','maxHeight': '450px','minHeight': '450px','overflow': 'auto'},  # Keep width but remove height constraints
                        optionHeight=50,
                    )
                ], style={'overflow': 'auto', 'maxHeight': '450px','minHeight': '450px'})
                ]
        ),
        dcc.Dropdown(
            id='output-db-dropdown',
            options=[],
            value=None,
            disabled=True,
            placeholder="Selected Output Database File",
        ),
    ], style={'width': '25%', 'float': 'left', 'marginLeft': '20px'}),

    # Right Panel (75% of the screen)
    html.Div([
        # Top Section (Table)
        html.Div([
            dcc.Loading(
                id="table-loading",
                type="default",
                children=[
                    DataTable(
                        id='table',
                        columns=[{'name': 'Local_TimeStamp', 'id': 'Local_TimeStamp'},
                                {'name': 'Name', 'id': 'Name'},
                                {'name': 'Value', 'id': 'Value'}],

                        data=[{'Local_TimeStamp': '', 'Name': '', 'Value': ''}],  # Default empty row
                        style_table={'height': '30vh', 'marginRight': '20px', 'background-color': 'white'},  # Set white background
                        style_header={'text-align': 'center'},  # Center-align column headers
                        fixed_rows={'headers': True, 'data': 0}  # Fix the top row containing column names
                    )
                ]
            )

        ], style={'width': '100%', 'float': 'left', 'border': '0.5px solid #A9A9A9', 'marginTop': '10px'}),



        # Bottom Section (Plot)
        html.Div([
            dcc.Loading(
                id="plot-loading",
                type="default",
                children=[
                    dcc.Graph(
                        id='instrument-plot',
                        style={'height': '60vh'},
                        figure={
                            'data': [],  # Your data goes here
                            'layout': {
                                'bgcolor': '#F0F8FF',  # Set the background color of the plot
                                'title': 'Instrument Logging Data',
                                'xaxis': {'title': 'Local TimeStamp'},
                                'yaxis': {'title': 'Instrument Value'},
                                'template': 'plotly_white'
                            }
                        }
                    )
                ]
            )
        ], style={'width': '100%', 'float': 'left', 'border': '0.5px solid #A9A9A9', 'marginTop': '15px'}),
    ], style={'width': '72%', 'float': 'right', 'marginRight': '20px'}),

    # Database file upload
    html.Div([
        dcc.Upload(
            id='upload-data',
            children=[
                html.Div([
                    dcc.Loading(
                        id="upload-button-loading",
                        type="default",
                        children=[
                            html.Button('Upload Database File', id='upload-button', n_clicks=0, style=button_style),
                        ]
                    ),
                    html.Div("", id="upload-status", style={'display': 'inline', 'marginLeft': '10px'}),  # Empty div for upload status
                ])
            ],
            multiple=False
        ),
    html.Div([
        # Export Table Button
        html.Button("Export Table to CSV", id="export-button", n_clicks=0, style=button_style),
        # Help Button with Font Awesome icon
        html.Button([
            html.I(className="fas fa-question-circle")  # Font Awesome Help Icon
        ], id="help-button", title="Use Upload Button to Upload the Resulting .db3 File From DB Joiner Program. Then Click and Scroll Down to Select Instruments and Pick Time As Needed. Use Export Button to Export Current Data to .csv File. Note Some Large Database May Take Up to Minutes to Load.", style={
            'border': 'none',
            'backgroundColor': 'transparent',  # Transparent background
            'color': '#007bff',  # Color to match your design
            'cursor': 'pointer',
            'verticalAlign': 'middle',
            'horizontalAlign': 'middle',
            'fontSize': '24px',  # Adjust icon size as needed
            'margin': '10px',  # Add some margin if needed
            'transition': 'color 0.2s',
        }),
        ], style={'marginTop': '20px'}), 
        # Download button
        html.Div(dcc.Download(id="export-data")),

    ], style={'width': '25%', 'float': 'left', 'marginLeft': '20px', 'marginTop': '20px'}),
    dcc.Store(id='temp-file-store'), 


], style={'backgroundColor': 'rgba(211,211,211, 0.5)', 'height': 'calc(100vh - 17px)'})
from datetime import datetime

# Callback to update the table and plot based on user inputs
@app.callback(
    [Output('table', 'data'),
     Output('instrument-plot', 'figure')],
    [Input('name-dropdown', 'value'),
     Input('start-date-picker', 'date'),
     Input('start-hour-picker', 'value'),
     Input('start-minute-picker', 'value'),
     Input('end-date-picker', 'date'),
     Input('end-hour-picker', 'value'),
     Input('end-minute-picker', 'value'),
     Input('output-db-dropdown', 'value')]
)

def update_table_and_plot(selected_names, start_date, start_hour, start_minute, end_date, end_hour, end_minute, selected_db):
    if not selected_db or not selected_names:
        raise PreventUpdate  # No database selected or no instruments chosen, so do nothing

    # Convert start and end datetime strings to datetime objects
    # Adjusted to include seconds in the datetime objects for filtering
    start_datetime = datetime.strptime(f"{start_date} {start_hour}:{start_minute}:00", "%Y-%m-%d %H:%M:%S") if start_date and start_hour and start_minute else None
    end_datetime = datetime.strptime(f"{end_date} {end_hour}:{end_minute}:59", "%Y-%m-%d %H:%M:%S") if end_date and end_hour and end_minute else None

    filtered_df = fetch_data(selected_db)

    if not filtered_df.empty:
        filtered_df = filtered_df[filtered_df['Name'].isin(selected_names)]
        if start_datetime and end_datetime:
            # Ensure comparison is between datetime objects
            filtered_df['Local_TimeStamp'] = pd.to_datetime(filtered_df['Local_TimeStamp'])
            filtered_df = filtered_df[
                (filtered_df['Local_TimeStamp'] >= start_datetime) &
                (filtered_df['Local_TimeStamp'] <= end_datetime)
            ]

    if filtered_df.empty:
        return [], px.scatter(title="No data available for the selected range or instruments").update_layout(template='plotly_white')

    table_data = filtered_df.to_dict('records')

    fig = px.line(
        filtered_df,
        x='Local_TimeStamp',
        y='Value',
        color='Name',
        title='Instrument Logging Data',
        labels={'Value': 'Instrument Value'},
        template='plotly_white'
    )

    return table_data, fig



# Callback to update the name dropdown options dynamically
@app.callback(
    Output('name-dropdown', 'options'),
    [Input('output-db-dropdown', 'value')]
)
def update_name_dropdown(selected_db):
    if selected_db:
        filtered_df = fetch_data(selected_db)
        return [{'label': name, 'value': name} for name in filtered_df['Name'].unique()]
    else:
        # Return an empty list if 'name-dropdown' is not found
        return []

# Updated callback to handle file upload and initialize date/time selections
# Updated callback
@app.callback(
    [Output('output-db-dropdown', 'options'),
     Output('output-db-dropdown', 'value'),
     Output('output-db-dropdown', 'disabled'),
     Output('upload-button', 'disabled'),
     Output('upload-status', 'children'),
     Output('start-date-picker', 'date'),
     Output('start-hour-picker', 'value'),
     Output('start-minute-picker', 'value'),
     Output('end-date-picker', 'date'),
     Output('end-hour-picker', 'value'),
     Output('end-minute-picker', 'value'),
     Output('temp-file-store', 'data')],  # Update the Output list to include the temp-file-store
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename'),
     State('temp-file-store', 'data')]  # Add temp-file-store data to the State
)
def update_database_options(contents, filename, temp_file_data):
    if contents is None:
        raise PreventUpdate

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    # Check if there's an existing temporary file path and delete the file if it exists
    if temp_file_data and os.path.exists(temp_file_data['path']):
        os.unlink(temp_file_data['path'])

    # Create a new temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db3')
    temp_file_path = temp_file.name

    with open(temp_file_path, 'wb') as f:
        f.write(decoded)

    # Update the dropdown options and value
    options = [{'label': filename, 'value': temp_file_path}]
    value = temp_file_path

    # Read the uploaded file to determine start and end times
    connection = sqlite3.connect(temp_file_path)
    df = pd.read_sql_query("SELECT Local_TimeStamp FROM NewTable;", connection)
    connection.close()

    # Convert Local_TimeStamp to datetime
    df['Local_TimeStamp'] = pd.to_datetime(df['Local_TimeStamp'])

    # Find min and max timestamp
    min_timestamp = df['Local_TimeStamp'].min()
    max_timestamp = df['Local_TimeStamp'].max()

    # Extract date, hour, and minute for start and end times
    start_date = min_timestamp.strftime('%Y-%m-%d')
    start_hour = min_timestamp.strftime('%H')
    start_minute = min_timestamp.strftime('%M')
    end_date = max_timestamp.strftime('%Y-%m-%d')
    end_hour = max_timestamp.strftime('%H')
    end_minute = max_timestamp.strftime('%M')

    return options, value, True, False, "FILE UPLOADED", start_date, start_hour, start_minute, end_date, end_hour, end_minute, {'path': temp_file_path}



# Callback to export table data to CSV
@app.callback(
    Output('export-data', 'data'),
    [Input('export-button', 'n_clicks')],
    [State('table', 'data')]
)
def export_data_to_csv(n_clicks, table_data):
    if n_clicks > 0:
        if not table_data:
            return dash.no_update

        # Create a DataFrame from the table data
        df = pd.DataFrame(table_data)

        # Create a CSV string from the DataFrame without the index
        csv_string = df.to_csv(index=False, encoding='utf-8')

        # Define the filename for the exported CSV file
        csv_filename = "exported_data.csv"

        # Create the data URL for downloading
        csv_data_uri = f'{csv_string}'

        return dict(content=csv_data_uri, filename=csv_filename)

    raise PreventUpdate

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

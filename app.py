import subprocess
import sys

def check_and_install_packages(packages):
    """Check if packages are installed and install them if they are not."""
    for package in packages:
        try:
            # Try to import the package
            __import__(package)
            print(f"'{package}' is already installed.")
        except ImportError:
            # If the package is not installed, install it
            print(f"'{package}' is not installed. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

required_packages = [
    'pandas',
    'dash',
    'dash_bootstrap_components',
    'plotly',
    'dash_bootstrap_templates',
    'python-dateutil',
    'python-dotenv'
]

check_and_install_packages(packages=required_packages)

import pandas as pd
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from dash_bootstrap_templates import load_figure_template
import plotly.express as px
import io
import base64
import webbrowser
from threading import Timer
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
from dotenv import load_dotenv

def get_env_var():
    load_dotenv()
    NOM_RATE = os.getenv("NOM_RATE")
    BANK = os.getenv("BANK")
    MAX_INVESTMENT_VALUE = os.getenv("MAX_INVESTMENT_VALUE")
    MAX_YEARLY_CONTRIBUTION = os.getenv("MAX_YEARLY_CONTRIBUTION")
    return NOM_RATE, BANK, MAX_INVESTMENT_VALUE, MAX_YEARLY_CONTRIBUTION

env_vars = get_env_var()
nominal_rate = float(env_vars[0])
BANK = env_vars[1]
MAX_INVESTMENT_VALUE = float(env_vars[2])
MAX_YEARLY_CONTRIBUTION = float(env_vars[3])

compounding_period = 12
period = {
    "anually": 1,
    "semi-anually": 2,
    "quaterly": 4,
    "monthly": 12
}

btn_style = {
"display": "inline-block",
    "height": "38px",
    "padding": "0 30px",
    "color": "rgba(98, 0, 238, 1.0)",
    "text-align": "center",
    "font-size": "11px",
    "font-weight": "600",
    "line-height": "38px",
    "letter-spacing": ".1rem",
    "text-transform": "uppercase",
    "text-decoration": "none",
    "white-space": "nowrap",
    "background-color": "transparent",
    "border-radius": "9px",
    "border": "2px solid rgba(98, 0, 238, 1.0)",
    "cursor": "pointer",
    "box-sizing": "border-box",
   }

btn_center_styling = {
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center'
    }

def get_effective_rate(nominal_rate):
    effective_rate = ((1 + (nominal_rate / compounding_period)) ** compounding_period) - 1
    return effective_rate

effective_rate = get_effective_rate(nominal_rate=nominal_rate)

chart_template = "plotly_dark"
text_styling = {'color': '#D3D3D3', 'font-size': '21px'}

def get_period(period):
    period_str = next((key for key, value in period.items() if value == compounding_period), None)
    return period_str

period_str = get_period(period)

def get_opendate(df):
    Date_opened = df['Date'][0]
    return Date_opened

def get_investment_value(df):
    investment_value = df['Balance'][len(df)-1]
    return investment_value

def get_invested_amount(contributions, withdrawls):
    money_invested = sum(contributions) - sum(withdrawls)
    return money_invested

def get_interest_earned(investment_value, money_invested):
    interest = investment_value - money_invested
    return interest

def get_interest_paydate(df):
    # Filter the DataFrame with the correct logical operator and parentheses
    filtered_df = df[(df["Contribution_Value"] == 0) & (df["Withdrawl_Value"] == 0)]
    # Get the last date and add one month
    last_date = pd.to_datetime(filtered_df['Date'].iloc[-1])
    next_interest_paydate = last_date + pd.DateOffset(months=1)
    
    # Return the date in the desired format
    return next_interest_paydate.strftime('%Y-%m-%d')

def Calculate_Next_Interestpayment(nominal_rate, df):
    projected_interest = (nominal_rate/ 12) * df['Balance'][len(df)-1]
    return projected_interest

def full_months_between(start_date, end_date):
    # Ensure the dates are datetime objects (in case they are not)
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate the difference in years and months
    year_diff = end_date.year - start_date.year
    month_diff = end_date.month - start_date.month
    
    # Calculate total full months difference
    total_month_diff = year_diff * 12 + month_diff
    
    # Adjust if the day of the start date is greater than the end date
    if start_date.day > end_date.day:
        total_month_diff -= 1
    
    return total_month_diff

def Connect_Localhost():
    webbrowser.open_new("http://127.0.0.1:8050")

def Value_Chart(df, withdrawls, withdrawl_date, value_at_withdrawl, contributions, contribution_date, Value_at_contribution, interest_payments, interest_payment_date, value_at_interest_payment):
    fig = px.area(x=df["Date"], y=df["Balance"], template=chart_template)
    fig.update_traces(
        fill='tozeroy', # Fill area to zero on the y-axis
        fillcolor='rgba(98, 0, 238, 0.3)',  # Area color with transparency
        line=dict(color='#6200ee')  # Border line color
    )
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Balance'],mode='markers',marker=dict(size=1, color='#6200ee'), showlegend=False,
    hovertemplate='<b>Date:</b> %{x}<br>' +
    '<b>Balance:</b> %{y:.2f}<br>' + '<extra></extra>'))
    fig.add_trace(go.Scatter(x=withdrawl_date, y=value_at_withdrawl, name='Withdrawl',mode='markers',marker=dict(size=8, color='rgba(220, 20, 60,0.8)'),
    hovertemplate='<b>Date:</b> %{x}<br>' +
    '<b>Balance:</b> %{y:.2f}<br>' +
    '<b>Withdrawl:</b> %{customdata[0]}<br>' + '<extra></extra>',
    customdata=list(zip([round(withdrawl, 2) for withdrawl in withdrawls]))))
    fig.add_trace(go.Scatter(x=contribution_date, y=Value_at_contribution, name='Contribution', mode='markers',marker=dict(size=8, color='rgba(42, 170, 138,0.8)'),
    hovertemplate='<b>Date:</b> %{x}<br>' +
    '<b>Balance:</b> %{y}<br>' +
    '<b>Contribution:</b> %{customdata[0]:.2f}<br>' + '<extra></extra>',
    customdata=list(zip([round(contribution, 2) for contribution in contributions]))))
    fig.add_trace(go.Scatter(x=interest_payment_date, y=value_at_interest_payment, name='Interest Payment', mode='markers',marker=dict(size=8, color='rgba(240, 185, 11, 1.0)'), 
    hovertemplate='<b>Date:</b> %{x}<br>' +
    '<b>Balance:</b> %{y:.2f}<br>' +
    '<b>Interest:</b> %{customdata[0]}<br>' + '<extra></extra>',
    customdata=list(zip([round(payment, 2) for payment in interest_payments]))))
    fig.update_layout(
            yaxis_title="Balance",
            xaxis_title=f"Date",
            legend_title="Details",
            xaxis_rangeslider_visible=False
            )
    fig.update_layout(margin=dict(l=20, r=10, t=20, b=10))
    df['Date'] = pd.to_datetime(df['Date'])

    # Calculate the difference between the first and last date
    date_diff = df['Date'].iloc[-1] - df['Date'].iloc[0]
    buttons_list = [
                    dict(count=1,
                        label="1m",
                        step="month",
                        stepmode="backward"),
                    dict(count=6,
                        label="6m",
                        step="month",
                        stepmode="backward"),
                    dict(count=1,
                        label="YTD",
                        step="year",
                        stepmode="todate"),]
    
    if date_diff.days > 365:
        buttons_list.append(dict(count=1,
                        label="1y",
                        step="year",
                        stepmode="backward"),)
    if date_diff.days > 365 * 2:
        buttons_list.append(dict(count=2,
                        label="2y",
                        step="year",
                        stepmode="backward"),)
    if date_diff.days > 365 * 3:
        buttons_list.append(dict(count=3,
                        label="3y",
                        step="year",
                        stepmode="backward"),)
    if date_diff.days > 365 * 5:
        buttons_list.append(dict(count=5,
                        label="5y",
                        step="year",
                        stepmode="backward"),)
    if date_diff.days > 365 * 10:
        buttons_list.append(dict(count=10,
                        label="10y",
                        step="year",
                        stepmode="backward"),)
    buttons_list.append(dict(step="all"))

    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list(buttons_list),
                    bgcolor='black',
                    activecolor='gray', # Color of the active button
                    borderwidth=0.5,
                    bordercolor='white',
                    font=dict(size=14, color='white'),
                    x=0, 
                    y=1.13,
                    xanchor='left',
                    yanchor='top'
                    ), fixedrange=True, type="date"))
    

    return fig

def Pie_Chart(interest, money_invested):
    fig = go.Figure(data=[go.Pie(labels=['Interest Earned', 'Contributions'], values=[interest,money_invested],marker=dict(colors=['rgba(240, 185, 11, 0.8)','rgba(98, 0, 238, 0.9)'],line=dict(color='#000000', width=0.5)), textposition='inside', hole=.3,
    hovertemplate='<b>%{label}</b><br>Value: %{value:.2f}<br>Percentage: %{percent}<extra></extra>')])
    fig.update_layout(
        margin=dict(l=150, r=10, t=50, b=10),
        annotations=[dict(text='TFSA', x=0.5, y=0.5, font_size=25, showarrow=False)]
    )
    fig.update_layout(legend_title="Details", template=chart_template)
    return fig

def Interest_Chart(df):
    months = full_months_between(start_date=df['Date'].iloc[0], end_date=df['Date'].iloc[-1])
    remaining_months = months % 12
    Interest_paid = round(((nominal_rate * (remaining_months/12)) * 100),2)
    Remaining = round(((nominal_rate * 100) - Interest_paid),2)

    fig = go.Figure(data=[
        go.Bar(name='Interest Paid for current year', x=[0], y=[Interest_paid], marker_color='rgba(42, 170, 138,0.8)',width=0.4, marker_line=dict(width=0.5, color="#000000"),    
               hovertemplate='Interest Paid: %{y}%<br>' + '<extra></extra>'),
        go.Bar(name='Interest to be paid', x=[0], y=[Remaining], marker_color='rgba(98, 0, 238, 0.9)', width=0.4, marker_line=dict(width=0.5, color="#000000"),
        hovertemplate='Outstanding Interest to be paid: </b> %{y}%<br>' + '<extra></extra>')
    ])

    fig.update_layout(barmode='stack', template=chart_template)
    fig.update_yaxes(title_text='Percentage Interest')
    fig.update_layout(legend_title="Details")
    fig.update_layout(margin=dict(l=40, r=40, t=10, b=10))
    fig.add_annotation(
        x=0, y=nominal_rate * 100,
        text=f"Interest Rate: {nominal_rate*100}%",
        font={"size":14, "color":"white", "family":"Arial"},
        showarrow=True,
        arrowhead=3,
        ax=0,
        ay=-40
    )
    fig.update_layout(
        xaxis=dict(
            showticklabels=False,  # Hide tick labels
            showgrid=False,        # Hide grid lines
            zeroline=False         # Hide the zero line
        )
    )
    return fig

def Bar_Chart(df):
    outstanding_contributions = []
    annual_contributions = []
    df['Date'] = pd.to_datetime(df['Date'])
    years = df['Date'].dt.year.astype(str).unique().tolist()
    df['Date'] = df['Date'].astype(str)
    for year in years:
        filtered_df = df[df['Date'].str.contains(str(year))]
        annual_contribution = filtered_df['Contribution_Value'].sum()
        outstanding_contribution = MAX_YEARLY_CONTRIBUTION - annual_contribution
        annual_contributions.append(annual_contribution)
        outstanding_contributions.append(outstanding_contribution)

    fig = go.Figure(data=[
        go.Bar(name='YTD Contribution Amount', x=years, y=annual_contributions, marker_color='rgba(42, 170, 138,0.8)',width=0.6, marker_line=dict(width=0.5, color="#000000"),    
               hovertemplate='<b>Year:</b> %{x}<br>' +
                '<b>Annual Contributions: </b> %{y:.2f}<br>' + '<extra></extra>'),
        go.Bar(name='Outstanding Conntribution Amount', x=years, y=outstanding_contributions, marker_color='rgba(220, 20, 60,0.8)', width=0.6, marker_line=dict(width=0.5, color="#000000"),
        hovertemplate='<b>Year: </b> %{x}<br>' +
        '<b>Outstanding Contributions: </b> %{y:.2f}<br>' + '<extra></extra>')
    ])
    fig.add_hline(
        y=MAX_YEARLY_CONTRIBUTION,
        line_dash="dot",
        row=3,
        col="all",
        line=dict(
            color="white",  # Set the line color
            width=0.7  # Set the line width
        )
    )

    fig.update_layout(barmode='stack', template=chart_template)
    fig.update_yaxes(title_text='Amount')
    fig.update_xaxes(title_text='Year')
    fig.update_layout(legend_title="Details")
    fig.update_layout(margin=dict(l=100, r=10, t=20, b=10))
    position = (len(annual_contributions)/2)-0.5
    fig.add_annotation(
        x=position, y=MAX_YEARLY_CONTRIBUTION,
        text=f"Annual Contribution Limit:  {int(MAX_YEARLY_CONTRIBUTION)}",
        font={"size":14, "color":"white", "family":"Arial"},
        showarrow=True,
        arrowhead=3,
        ax=0,
        ay=-40
    )
    return fig

def FileUploader():
    file_uploader = dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select File')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    )
    return file_uploader

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, dbc.icons.FONT_AWESOME])
load_figure_template('BOOTSTRAP')
app.title = f"Savings Account Tracking Dashboard"

app.layout = html.Div([
    html.H2(app.title, style={'text-align': 'center'}),
    html.Hr(style={'margin-top': '1%', 'margin-bottom': '2%'}),
    FileUploader(),
    html.Hr(style={'margin-top': '2%', 'margin-bottom': '1%'}),
    html.Div(id='file-upload-status', style={'display': 'none'}),
    html.Div(id="file_output"),
    html.Hr(style={'margin-top': '1%', 'margin-bottom': '2%'}),
], style={'margin-left': '3%', 'margin-right': '3%', 'margin-top': '1%', 'margin-bottom': '1%'})

@app.callback(
    [Output('file_output', 'children'),Output('file-upload-status', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def process_file(contents, filename):
    global df
    if contents is None:
        return "Upload a file to generate your Dashboard.", "false"
    content_type, content_string = contents.split(',')

    try:
        decoded = base64.b64decode(content_string)
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        else: 
            return "Invalid file type. Upload a csv or xlsx.", "false"

        Date_opened = get_opendate(df=df)
        investment_value = get_investment_value(df=df)

        Output = Output = html.Div([
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.H3('General Information'),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        dbc.Row([
            dbc.Col(html.H6("Nominal Interest Rate:", style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{nominal_rate * 100:.1f}%', style=text_styling)),
            dbc.Col(html.H6('Effective Interest Rate:', style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{effective_rate * 100:.2f}%', style=text_styling)),
        ]),
        dbc.Row([
            dbc.Col(html.H6("Period Compounded:", style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{period_str}', style=text_styling)),
            dbc.Col(html.H6('Date Opened:', style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{str(Date_opened)}', style=text_styling)),
        ], justify='center'),
        dbc.Row([
            dbc.Col(html.H6("Maximum Savings Balance:", style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{MAX_INVESTMENT_VALUE:.2f}', style=text_styling)),
            dbc.Col(html.H6('Yearly Contribution Limit:', style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{MAX_YEARLY_CONTRIBUTION:.2f}', style=text_styling)),
        ], justify='center'),
        dbc.Row([
            dbc.Col(html.H6("Current Investment Value:", style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{investment_value:.2f}', id="current-value", style=text_styling)),
            dbc.Col(html.H6("Total Interest Earned:", style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{investment_value:.2f}', id="interest-earned", style=text_styling)),
        ], justify="center"),
        dbc.Row([
            dbc.Col(html.H6("Bank:", style={'font-size': '21px'})),
            dbc.Col(html.H6(BANK, id="bank", style=text_styling)),
        ], justify="center", style={"margin-right" : "50%"}),

        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.H3("Record a Contribution or Withdrawal"),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        dbc.Row([
            dbc.Col(html.H5("Date:")),
            dbc.Col(html.H5("Investment Value:")),
            dbc.Col(html.H5("Contribution Value:")),
            dbc.Col(html.H5("Withdrawal Value:")),
        ], justify='center'),
        dbc.Row([
            dbc.Col(dcc.Input(id='Date', type='text', value='', placeholder='YYYY-MM-DD', 
                               style={'width': '150px', 'height': '30px', 
                                      'border': '1px solid white', 
                                      'padding': '0.25rem 0.5rem', 
                                      'border-radius': '5px',
                                      'background-color':'#000000',
                                      'color':'white'}), width=3),
            dbc.Col(dcc.Input(id='Investment-Value', type='number', value='', placeholder='Enter Value', 
                               style={'width': '150px', 'height': '30px', 
                                      'border': '1px solid white',  
                                      'padding': '0.25rem 0.5rem', 
                                      'border-radius': '5px',
                                      'background-color':'#000000',
                                      'color':'white'}, min=0, max=MAX_INVESTMENT_VALUE), width=3),
            dbc.Col(dcc.Input(id='Contribution-Value', type='number', value='', placeholder='Enter Value', 
                               style={'width': '150px', 'height': '30px', 
                                      'border': '1px solid white',  
                                      'padding': '0.25rem 0.5rem', 
                                      'border-radius': '5px',
                                      'background-color':'#000000',
                                      'color':'white'}, min=0, max=MAX_YEARLY_CONTRIBUTION), width=3),
            dbc.Col(dcc.Input(id='Withdrawal-Value', type='number', value='', placeholder='Enter Value', 
                               style={'width': '150px', 'height': '30px', 
                                      'border': '1px solid white',  
                                      'padding': '0.25rem 0.5rem', 
                                      'border-radius': '5px', 
                                      'background-color':'#000000',
                                      'color':'white'}, min=0), width=3),
        ], justify='center'),
        dbc.Row(dbc.Col(html.Div(html.Button('Save Data', id='save-button', n_clicks=0, style=btn_style), style={'textAlign': 'center', "margin-top":'5%'}), width=3), justify='center'),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.Div(id='output'),
    ])

        return html.Div([
            html.P("File successfully uploaded."), Output
        ]), "true"
    except Exception as e:
        print(f"Error processing file: {e}")
        return html.Div("There was an error processing the file."), "false"

@app.callback(
    [Output('current-value', 'children'), Output('Date', 'value'), Output('Investment-Value','value'), Output('Contribution-Value','value'), Output('Withdrawal-Value','value'), Output("interest-earned","children"), Output('output', 'children')],
    [Input('save-button', 'n_clicks')],
    [State('Date', 'value'), State('Investment-Value', 'value'),
        State('Contribution-Value', 'value'), State('Withdrawal-Value', 'value'), 
        State('file-upload-status', 'children')]
)
def get_data(n_clicks, date, investment_value, contribution_value, withdrawal_value, file_status):
    global df
    if n_clicks > 0 and file_status == "true":
        # Save input values to a dictionary
        data = {
            'Date': date,
            'Balance': investment_value,
            'Contribution_Value': contribution_value,
            'Withdrawl_Value': withdrawal_value
        }

        new_row_df = pd.DataFrame([data])
        
        # Concatenate the DataFrames
        df = pd.concat([df, new_row_df], ignore_index=True)
        print(df)

    investment_value = get_investment_value(df=df)
    contributions, contribution_date, Value_at_contribution = [], [], []
    withdrawls, withdrawl_date, value_at_withdrawl = [], [], []
    interest_payments, interest_payment_date, value_at_interest_payment = [], [], []
    for i in range(0,len(df)):
        if (df['Contribution_Value'][i] != 0) and (df['Withdrawl_Value'][i] == 0):
            contributions.append(df['Contribution_Value'][i])
            Value_at_contribution.append(df['Balance'][i])
            contribution_date.append(df['Date'][i])
        if (df['Withdrawl_Value'][i] != 0) and (df['Contribution_Value'][i] == 0):
            withdrawls.append(df['Withdrawl_Value'][i])
            withdrawl_date.append(df['Date'][i])
            value_at_withdrawl.append(df['Balance'][i])
        if (df['Withdrawl_Value'][i] == 0) and (df['Contribution_Value'][i] == 0):
            if i != 0 and ((df['Balance'][i] - df['Balance'][i-1]) != 0):
                interest_payment_date.append(df['Date'][i])
                value_at_interest_payment.append(df['Balance'][i])
                interest_payments.append(df['Balance'][i] - df['Balance'][i-1])
            
    money_invested = get_invested_amount(contributions=contributions, withdrawls=withdrawls)
    interest = get_interest_earned(investment_value=investment_value, money_invested=money_invested)

    interest_paydate = get_interest_paydate(df=df)
    Next_InterestPayment = Calculate_Next_Interestpayment(nominal_rate=nominal_rate, df=df)

    output = [
        html.H3("Savings Tracking Chart"),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.Div(dcc.Graph(figure=Value_Chart(df=df, withdrawls=withdrawls, withdrawl_date=withdrawl_date, value_at_withdrawl=value_at_withdrawl,contributions=contributions, contribution_date=contribution_date, Value_at_contribution=Value_at_contribution, interest_payments=interest_payments, interest_payment_date=interest_payment_date, value_at_interest_payment=value_at_interest_payment), config={'displayModeBar': False}, style={'height': '60vh', 'width': '100%'})),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.Div(
            [
                html.Div(html.H3("Money invested vs Interest earned"), style={"flex": "1","padding": "10px"}),
                html.Div(html.H3("Next Interest Payment"), style={"flex": "1", "padding": "10px"})
            ],
            style={"display": "flex", "width": "100%"}
        ),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.Div(
            [
                html.Div(dcc.Graph(figure=Pie_Chart(interest=interest,money_invested=money_invested), config={'displayModeBar': False}, style={'height': '55vh', 'width': '100%'}), style={"flex": "1","padding": "10px"}),
                html.Div([dcc.Graph(figure=Interest_Chart(df=df), config={'displayModeBar': False}, style={'height': '50vh', 'width': '100%','margin-left':'2%'}),
                html.Hr(style={'margin-top': '1%', 'margin-bottom': '2%'}),
        dbc.Row([
            dbc.Col(html.H6("Expected Interest Amount:", style={'font-size': '21px', 'margin-left':'2%'})),
            dbc.Col(html.H6(f'{Next_InterestPayment:.2f}', style=text_styling)),
        ], style={'margin-top':'2%'}),dbc.Row([
            dbc.Col(html.H6("Next Interest Payment Date:", style={'font-size': '21px', 'margin-left': '2%'})),
            dbc.Col(html.H6(f'{interest_paydate}', style=text_styling)),
        ])], style={"flex": "1", "padding": "20px"})
            ],
            style={"display": "flex", "width": "100%"}
        ),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.H3("Yearly Savings Contribution Status: Paid vs. Outstanding"),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.Div(dcc.Graph(figure=Bar_Chart(df=df), config={'displayModeBar': False}, style={'height': '60vh', 'width': '100%'})),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.H3("Export data as csv or Excel"),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        dbc.Row([
            dbc.Col(html.Div([
        html.Button("Download CSV", id="btn_csv",style=btn_style),
        dcc.Download(id="download-dataframe-csv"),
        ],style=btn_center_styling), ),
            dbc.Col(html.Div([html.Button("Download Excel", id="btn_xlsx", style=btn_style),dcc.Download(id="download-dataframe-xlsx"),], style=btn_center_styling),),
        ], justify='center'),
    ]

    if n_clicks > 0:
        print(f"Data saved: {data}")
    return f'R{investment_value:.2f}', '', '', '', '', f'R{interest:.2f}',output

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    prevent_initial_call=True,
)
def to_csv(n_clicks):
    if n_clicks > 0:
        return dcc.send_data_frame(df.to_csv, "data.csv")
    
@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("btn_xlsx", "n_clicks"),
    prevent_initial_call=True,
)
def to_excel(n_clicks):
    if n_clicks > 0:
        return dcc.send_data_frame(df.to_excel, "data.xlsx", sheet_name="Sheet_name_1")

if __name__ == '__main__':
    Timer(0.1, Connect_Localhost).start()
    # starts the server
    app.run_server()
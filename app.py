import subprocess
import sys

def checkAndInstallPackages(packages):
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

requiredPackages = [
    'pandas',
    'dash',
    'dash_bootstrap_components',
    'plotly',
    'dash_bootstrap_templates',
    'python-dateutil',
    'python-dotenv'
]

checkAndInstallPackages(packages=requiredPackages)

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

def getEnvVar():
    load_dotenv()
    USER_NAME = os.getenv("USER_NAME")
    NOM_RATE = os.getenv("NOM_RATE")
    MAX_INVESTMENT_VALUE = os.getenv("MAX_INVESTMENT_VALUE")
    MAX_YEARLY_CONTRIBUTION = os.getenv("MAX_YEARLY_CONTRIBUTION")
    ACCOUNT_HOLDER = os.getenv("ACCOUNT_HOLDER")
    CURRENCY = os.getenv("CURRENCY")
    return USER_NAME, NOM_RATE, MAX_INVESTMENT_VALUE, MAX_YEARLY_CONTRIBUTION, ACCOUNT_HOLDER, CURRENCY

env_vars = getEnvVar()
USER_NAME: str = env_vars[0]
nominalRate: float = float(env_vars[1])
MAX_INVESTMENT_VALUE: float = float(env_vars[2])
MAX_YEARLY_CONTRIBUTION: float = float(env_vars[3])
ACCOUNT_HOLDER: str = env_vars[4]
CURRENCY: str = env_vars[5]

compoundingPeriod = 12
period = {
    "anually": 1,
    "semi-anually": 2,
    "quaterly": 4,
    "monthly": 12
}

btnStyle = {
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

btnCenterStyling = {
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center'
    }

def getEffectiveRate(nominalRate):
    effectiveRate = ((1 + (nominalRate / compoundingPeriod)) ** compoundingPeriod) - 1
    return effectiveRate

effectiveRate = getEffectiveRate(nominalRate=nominalRate)

chartTemplate = "plotly_dark"
textStyling = {'color': '#D3D3D3', 'font-size': '21px'}

def getPeriod(period):
    periodStr = next((key for key, value in period.items() if value == compoundingPeriod), None)
    return periodStr

periodStr = getPeriod(period)

def getOpenDate(df):
    dateOpened = df['Date'][0]
    return dateOpened

def getInvestmentValue(df):
    investmentValue = df['Balance'][len(df)-1]
    return investmentValue

def getInvestedAmount(contributions, withdrawls):
    moneyInvested = sum(contributions) - sum(withdrawls)
    return moneyInvested

def getInterestEarned(investmentValue, moneyInvested):
    interest = investmentValue - moneyInvested
    return interest

def getInterestPayDate(df):
    # Filter the DataFrame with the correct logical operator and parentheses
    filteredDF = df[(df["Contribution_Value"] == 0) & (df["Withdrawl_Value"] == 0)]
    # Get the last date and add one month
    lastDate = pd.to_datetime(filteredDF['Date'].iloc[-1])
    nextInterestPayDate = lastDate + pd.DateOffset(months=1)

    # Return the date in the desired format
    return nextInterestPayDate.strftime('%Y-%m-%d')

def calculateNextInterestPayment(nominalRate, df):
    projectedInterest = (nominalRate/ 12) * df['Balance'][len(df)-1]
    return projectedInterest

def fullMonthsBetween(startDate, endDate):
    # Ensure the dates are datetime objects (in case they are not)
    if isinstance(startDate, str):
        startDate = datetime.strptime(startDate, '%Y-%m-%d')
    if isinstance(endDate, str):
        endDate = datetime.strptime(endDate, '%Y-%m-%d')

    # Calculate the difference in years and months
    yearDiff = endDate.year - startDate.year
    monthDiff = endDate.month - startDate.month

    # Calculate total full months difference
    totalMonthDiff = yearDiff * 12 + monthDiff

    # Adjust if the day of the start date is greater than the end date
    if startDate.day > endDate.day:
        totalMonthDiff -= 1

    return totalMonthDiff

def connectLocalhost():
    webbrowser.open_new("http://127.0.0.1:8050")

def valueChart(df, withdrawls, withdrawlDate, valueAtWithdrawl, contributions, contributionDate, valueAtContribution, interestPayments, interestPaymentDate, valueAtInteresrPayment):
    fig = px.area(x=df["Date"], y=df["Balance"], template=chartTemplate)

    sortedPairs = sorted(zip(pd.to_datetime(interestPaymentDate), interestPayments, valueAtInteresrPayment))
    interestPaymentDate, interestPayments, valueAtInteresrPayment = zip(*sortedPairs)

    interestPaymentDate = [date.strftime("%Y-%m-%d") for date in interestPaymentDate]
    interestPayments = list(interestPayments)
    valueAtInteresrPayment = list(valueAtInteresrPayment)

    fig.update_traces(
        fill='tozeroy', # Fill area to zero on the y-axis
        fillcolor='rgba(98, 0, 238, 0.3)',  # Area color with transparency
        line=dict(color='#6200ee')  # Border line color
    )
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Balance'],mode='markers',marker=dict(size=1, color='#6200ee'), showlegend=False,
    hovertemplate='<b>Date:</b> %{x}<br>' +
    '<b>Balance:</b> ' + CURRENCY + '%{y:.2f}<br>' + '<extra></extra>'))
    fig.add_trace(go.Scatter(x=withdrawlDate, y=valueAtWithdrawl, name='Withdrawal',mode='markers',marker=dict(size=8, color='rgba(220, 20, 60,0.8)'),
    hovertemplate='<b>Date:</b> %{x}<br>' +
    '<b>Balance:</b> ' + CURRENCY + '%{y:.2f}<br>' +
    '<b>Withdrawal:</b> ' + CURRENCY + '%{customdata[0]}<br>' + '<extra></extra>',
    customdata=list(zip([round(withdrawl, 2) for withdrawl in withdrawls]))))
    fig.add_trace(go.Scatter(x=contributionDate, y=valueAtContribution, name='Contribution', mode='markers',marker=dict(size=8, color='rgba(42, 170, 138,0.8)'),
    hovertemplate='<b>Date:</b> %{x}<br>' +
    '<b>Balance:</b> '+ CURRENCY + '%{y:.2f}<br>' +
    '<b>Contribution:</b> ' + CURRENCY + '%{customdata[0]:.2f}<br>' + '<extra></extra>',
    customdata=list(zip([round(contribution, 2) for contribution in contributions]))))
    fig.add_trace(go.Scatter(x=interestPaymentDate, y=valueAtInteresrPayment, name='Interest Payment', mode='markers',marker=dict(size=8, color='rgba(240, 185, 11, 1.0)'),
    hovertemplate='<b>Date:</b> %{x}<br>' +
    '<b>Balance:</b> ' + CURRENCY + '%{y:.2f}<br>' +
    '<b>Interest:</b> ' + CURRENCY + '%{customdata[0]}<br>' + '<extra></extra>',
    customdata=list(zip([round(payment, 2) for payment in interestPayments]))))
    fig.update_layout(
            yaxis_title="Balance (ZAR)",
            xaxis_title=f"Date",
            legend_title="Details",
            xaxis_rangeslider_visible=False
            )
    fig.update_layout(margin=dict(l=20, r=10, t=20, b=10))
    df['Date'] = pd.to_datetime(df['Date'])

    # Calculate the difference between the first and last date
    dateDiff = df['Date'].iloc[-1] - df['Date'].iloc[0]
    buttonsList = [
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

    if dateDiff.days > 365:
        buttonsList.append(dict(count=1,
                        label="1y",
                        step="year",
                        stepmode="backward"),)
    if dateDiff.days > 365 * 2:
        buttonsList.append(dict(count=2,
                        label="2y",
                        step="year",
                        stepmode="backward"),)
    if dateDiff.days > 365 * 3:
        buttonsList.append(dict(count=3,
                        label="3y",
                        step="year",
                        stepmode="backward"),)
    if dateDiff.days > 365 * 5:
        buttonsList.append(dict(count=5,
                        label="5y",
                        step="year",
                        stepmode="backward"),)
    if dateDiff.days > 365 * 10:
        buttonsList.append(dict(count=10,
                        label="10y",
                        step="year",
                        stepmode="backward"),)
    buttonsList.append(dict(step="all"))

    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list(buttonsList),
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

def pieChart(interest, moneyInvested):
    fig = go.Figure(data=[go.Pie(labels=['Interest Earned', 'Contributions'], values=[interest,moneyInvested],marker=dict(colors=['rgba(240, 185, 11, 0.8)','rgba(98, 0, 238, 0.9)'],line=dict(color='#000000', width=0.5)), textposition='inside', hole=.3,
    hovertemplate='<b>%{label}</b><br>Value: ' + CURRENCY + '%{value:.2f}<br>Percentage: %{percent}<extra></extra>')])
    fig.update_layout(
        margin=dict(l=150, r=10, t=10, b=10),
        annotations=[dict(text=Account_Type, x=0.5, y=0.5, font_size=25, showarrow=False)]
    )
    fig.update_layout(legend_title="Details", template=chartTemplate)
    return fig

def interestChart(df):
    months = fullMonthsBetween(startDate=df['Date'].iloc[0], endDate=df['Date'].iloc[-1])
    remainingMonths = months % 12
    interestPaid = round(((nominalRate * (remainingMonths/12)) * 100),2)
    Remaining = round(((nominalRate * 100) - interestPaid),2)

    fig = go.Figure(data=[
        go.Bar(name='Interest Paid for current year', x=[0], y=[interestPaid], marker_color='rgba(42, 170, 138,0.8)',width=0.4, marker_line=dict(width=0.5, color="#000000"),
               hovertemplate='Interest Paid: %{y}%<br>' + '<extra></extra>'),
        go.Bar(name='Interest to be paid', x=[0], y=[Remaining], marker_color='rgba(98, 0, 238, 0.9)', width=0.4, marker_line=dict(width=0.5, color="#000000"),
        hovertemplate='Outstanding Interest to be paid: </b> %{y}%<br>' + '<extra></extra>')
    ])

    fig.update_layout(barmode='stack', template=chartTemplate)
    fig.update_yaxes(title_text='Percentage Interest')
    fig.update_layout(legend_title="Details")
    fig.update_layout(margin=dict(l=40, r=40, t=10, b=10))
    fig.add_annotation(
        x=0, y=nominalRate * 100,
        text=f"Interest Rate: {round(nominalRate*100,1)}%",
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

def barChart(df):
    outstandingContributions = []
    annualContributions = []
    df['Date'] = pd.to_datetime(df['Date'])
    years = df['Date'].dt.year.astype(str).unique().tolist()
    df['Date'] = df['Date'].astype(str)
    for year in years:
        filteredDF = df[df['Date'].str.contains(str(year))]
        annualContribution = filteredDF['Contribution_Value'].sum()
        outstandingContribution = MAX_YEARLY_CONTRIBUTION - annualContribution
        annualContributions.append(annualContribution)
        outstandingContributions.append(outstandingContribution)

    fig = go.Figure(data=[
        go.Bar(name='YTD Contribution Amount', x=years, y=annualContributions, marker_color='rgba(42, 170, 138,0.8)',width=0.6, marker_line=dict(width=0.5, color="#000000"),
               hovertemplate='<b>Year:</b> %{x}<br>' +
                '<b>Annual Contributions: </b> '+ CURRENCY + '%{y:.2f}<br>' + '<extra></extra>'),
        go.Bar(name='Outstanding Conntribution Amount', x=years, y=outstandingContributions, marker_color='rgba(220, 20, 60,0.8)', width=0.6, marker_line=dict(width=0.5, color="#000000"),
        hovertemplate='<b>Year: </b> %{x}<br>' +
        '<b>Outstanding Contributions: </b> ' + CURRENCY +'%{y:.2f}<br>' + '<extra></extra>')
    ])
    if len(years) > 1:
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

    fig.update_layout(barmode='stack', template=chartTemplate)
    fig.update_yaxes(title_text='Amount (ZAR)')
    fig.update_xaxes(title_text='Year')
    fig.update_layout(legend_title="Details")
    fig.update_layout(margin=dict(l=100, r=10, t=20, b=10))
    position = (len(annualContributions)/2)-0.5
    fig.add_annotation(
        x=position, y=MAX_YEARLY_CONTRIBUTION,
        text=f"Annual Contribution Limit:  {CURRENCY}{int(MAX_YEARLY_CONTRIBUTION)}",
        font={"size":14, "color":"white", "family":"Arial"},
        showarrow=True,
        arrowhead=3,
        ax=0,
        ay=-40
    )
    return fig

def fileUploader():
    fileuploader = dcc.Upload(
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
    return fileuploader

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, dbc.icons.FONT_AWESOME])
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" href="/favicon.ico" type="image/x-icon">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

load_figure_template('BOOTSTRAP')
app.title = f"{USER_NAME}'s Savings Account Tracker"

app.layout = html.Div([
    html.H2(app.title, style={'text-align': 'center'}),
    html.Hr(style={'margin-top': '1%', 'margin-bottom': '2%'}),
    fileUploader(),
    html.Hr(style={'margin-top': '2%', 'margin-bottom': '1%'}),
    html.Div(id='file-upload-status', style={'display': 'none'}),
    html.Div(id="file_output"),
    html.Hr(style={'margin-top': '1%', 'margin-bottom': '2%'}),
], style={'margin-left': '3%', 'margin-right': '3%', 'margin-top': '3%', 'margin-bottom': '3%'})

@app.callback(
    [Output('file_output', 'children'),Output('file-upload-status', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def processFile(contents, filename):
    global df
    if contents is None:
        return "Upload a file to generate your Dashboard.", "false"
    contentType, content_string = contents.split(',')

    try:
        decoded = base64.b64decode(content_string)
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an Excel file
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return "Invalid file type. Upload a csv or xlsx.", "false"

        global BANK
        BANK = (filename.split("_")[0]).upper()
        global Account_Type
        Account_Type = (filename.split("_")[1].split(".")[0]).upper()
        dateOpened = getOpenDate(df=df)
        investmentValue = getInvestmentValue(df=df)

        Output =  html.Div([
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.H3('General Information'),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        dbc.Row([
            dbc.Col(html.H6("Nominal Interest Rate:", style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{nominalRate * 100:.1f}%', style=textStyling)),
            dbc.Col(html.H6('Effective Interest Rate:', style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{effectiveRate * 100:.2f}%', style=textStyling)),
        ]),
        dbc.Row([
            dbc.Col(html.H6("Period Compounded:", style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{periodStr}', style=textStyling)),
            dbc.Col(html.H6('Date Opened:', style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{str(dateOpened)}', style=textStyling)),
        ], justify='center'),
        dbc.Row([
            dbc.Col(html.H6("Maximum Savings Balance:", style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{CURRENCY}{MAX_INVESTMENT_VALUE:.2f}', style=textStyling)),
            dbc.Col(html.H6('Yearly Contribution Limit:', style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{CURRENCY}{MAX_YEARLY_CONTRIBUTION:.2f}', style=textStyling)),
        ], justify='center'),
        dbc.Row([
            dbc.Col(html.H6("Current Investment Value:", style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{CURRENCY}{investmentValue:.2f}', id="current-value", style=textStyling)),
            dbc.Col(html.H6("Total Interest Earned:", style={'font-size': '21px'})),
            dbc.Col(html.H6(f'{CURRENCY}{investmentValue:.2f}', id="interest-earned", style=textStyling)),
        ], justify="center"),
        dbc.Row([
            dbc.Col(html.H6("Bank:", style={'font-size': '21px'})),
            dbc.Col(html.H6(BANK, id="bank", style=textStyling)),
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
        dbc.Row(dbc.Col(html.Div(html.Button('Save Data', id='save-button', n_clicks=0, style=btnStyle), style={'textAlign': 'center', "margin-top":'5%'}), width=3), justify='center'),
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
def get_data(n_clicks, date, investmentValue, contribution_value, withdrawal_value, fileStatus):
    global df
    if n_clicks > 0 and fileStatus == "true":
        # Save input values to a dictionary
        data = {
            'Date': date,
            'Balance': investmentValue,
            'Contribution_Value': contribution_value,
            'Withdrawl_Value': withdrawal_value
        }

        newRowdf = pd.DataFrame([data])

        # Concatenate the DataFrames
        df = pd.concat([df, newRowdf], ignore_index=True)
        df = df.sort_values(by='Date', ascending=True)
        # print(df)

    investmentValue = getInvestmentValue(df=df)
    contributions, contributionDate, valueAtContribution = [], [], []
    withdrawls, withdrawlDate, valueAtWithdrawl = [], [], []
    interestPayments, interestPaymentDate, valueAtInteresrPayment = [], [], []
    for i in range(0,len(df)):
        if (df['Contribution_Value'][i] != 0) and (df['Withdrawl_Value'][i] == 0):
            contributions.append(df['Contribution_Value'][i])
            valueAtContribution.append(df['Balance'][i])
            contributionDate.append(df['Date'][i])
        if (df['Withdrawl_Value'][i] != 0) and (df['Contribution_Value'][i] == 0):
            withdrawls.append(df['Withdrawl_Value'][i])
            withdrawlDate.append(df['Date'][i])
            valueAtWithdrawl.append(df['Balance'][i])
        if (df['Withdrawl_Value'][i] == 0) and (df['Contribution_Value'][i] == 0):
            if i != 0 and ((df['Balance'][i] - df['Balance'][i-1]) != 0):
                interestPaymentDate.append(df['Date'][i])
                valueAtInteresrPayment.append(df['Balance'][i])
                interestPayments.append(df['Balance'][i] - df['Balance'][i-1])

    moneyInvested = getInvestedAmount(contributions=contributions, withdrawls=withdrawls)
    interest = getInterestEarned(investmentValue=investmentValue, moneyInvested=moneyInvested)

    interestPayDate = getInterestPayDate(df=df)
    nextInterestPayment = calculateNextInterestPayment(nominalRate=nominalRate, df=df)

    output = [
        html.H3("Savings Tracking Chart"),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.Div(dcc.Graph(figure=valueChart(df=df, withdrawls=withdrawls, withdrawlDate=withdrawlDate, valueAtWithdrawl=valueAtWithdrawl,contributions=contributions, contributionDate=contributionDate, valueAtContribution=valueAtContribution, interestPayments=interestPayments, interestPaymentDate=interestPaymentDate, valueAtInteresrPayment=valueAtInteresrPayment), config={'displayModeBar': False}, style={'height': '60vh', 'width': '100%'})),
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
                html.Div(dcc.Graph(figure=pieChart(interest=interest,moneyInvested=moneyInvested), config={'displayModeBar': False}, style={'height': '55vh', 'width': '100%'}), style={"flex": "1","padding": "10px"}),
                html.Div([dcc.Graph(figure=interestChart(df=df), config={'displayModeBar': False}, style={'height': '50vh', 'width': '100%','margin-left':'2%'}),
                html.Hr(style={'margin-top': '1%', 'margin-bottom': '2%'}),
        dbc.Row([
            dbc.Col(html.H6("Expected Interest Amount:", style={'font-size': '21px', 'margin-left':'2%'})),
            dbc.Col(html.H6(f'{CURRENCY}{nextInterestPayment:.2f}', style=textStyling)),
        ], style={'margin-top':'2%'}),dbc.Row([
            dbc.Col(html.H6("Next Interest Payment Date:", style={'font-size': '21px', 'margin-left': '2%'})),
            dbc.Col(html.H6(f'{interestPayDate}', style=textStyling)),
        ])], style={"flex": "1", "padding": "20px"})
            ],
            style={"display": "flex", "width": "100%"}
        ),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.H3("Yearly Savings Contribution Status: Paid vs. Outstanding"),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.Div(dcc.Graph(figure=barChart(df=df), config={'displayModeBar': False}, style={'height': '60vh', 'width': '100%'})),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        html.H3("Export data as csv or Excel"),
        html.Hr(style={'margin-top': '1%', 'margin-bottom': '1%'}),
        dbc.Row([
            dbc.Col(html.Div([
        html.Button("Download CSV", id="btn_csv",style=btnStyle),
        dcc.Download(id="download-dataframe-csv"),
        ],style=btnCenterStyling), ),
            dbc.Col(html.Div([html.Button("Download Excel", id="btn_xlsx", style=btnStyle),dcc.Download(id="download-dataframe-xlsx"),], style=btnCenterStyling),),
        ], justify='center'),
    ]

    if n_clicks > 0:
        print(f"Data saved: {data}")
    return f'{CURRENCY}{investmentValue:.2f}', '', '', '', '', f'{CURRENCY}{interest:.2f}',output

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    prevent_initial_call=True,
)
def to_csv(n_clicks):
    if n_clicks > 0:
        return dcc.send_data_frame(df.to_csv, "data.csv",index=False)

@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("btn_xlsx", "n_clicks"),
    prevent_initial_call=True,
)
def to_excel(n_clicks):
    if n_clicks > 0:
        return dcc.send_data_frame(df.to_excel, "data.xlsx", sheet_name="Sheet_name_1", index=False)

if __name__ == '__main__':
    Timer(0.1, connectLocalhost).start()
    # starts the server
    app.run_server()

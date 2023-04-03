from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import dash_player as dp
import json 
import pandas as pd 

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],suppress_callback_exceptions=True)
template = 'plotly_dark'
color = {'color': 'white'}
test_csv = pd.read_csv("data/testData.csv").to_dict(orient='records')
totalVideos = len(test_csv)
video = test_csv[0]['CLIPNAME']
userEmail = ''
scores = {
    'TestID' : [],
    'AScore': [],
    'BScore': []
}

modalGetInfo = html.Div(dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Enter your info below"), close_button=False),
                dbc.ModalBody("Enter your Email below:"),
                dbc.Input(id='modal-Email', placeholder="Email goes here...", type='text'),
                dbc.ModalFooter(
                    dbc.Button(
                        "Start Test", id="modal-submit", className="ms-auto", n_clicks=0
                    )
                ),
            ],
            id="modal",
            is_open=True,
            keyboard=False,
            backdrop="static"
        ))

modalEnd = html.Div(dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("END OF SURVEY"), close_button=False),
                dbc.ModalBody("Thank you for participating!"),
                dbc.ModalFooter("Goodbye!"),
            ],
            id="modalEnd",
            is_open=False,
            keyboard=False,
            backdrop="static"
        ))

videoPlayer = html.Center(dp.DashPlayer(
            id="videoPlayer",
            url=video,
            controls=True,
            width="65%",
            height="65%",
            loop=True,
            playing=True,
            ))

leftColumn = dbc.Col(html.Center(html.Div([html.Hr(),"A (Quality)", 
                      dcc.Slider(0, 100, value=50, id='slider-A', tooltip={"placement": "bottom", "always_visible": True}),
                      html.Div(id='slider-A-output')
                      ]),style=color))

rightColumn = dbc.Col(html.Center(html.Div([html.Hr(),"B (Quality)", 
                      dcc.Slider(0, 100, value=50, id='slider-B', tooltip={"placement": "bottom", "always_visible": True}),
                      html.Div(id='slider-B-output')
                      ]),style=color))

mainApp = html.Div(
    [
        modalGetInfo, modalEnd,
        html.Div([
        html.Div(dbc.Row(dbc.Col(html.Div(videoPlayer))), id='htmlVideoPlayer', style={'display':'none'}),
        html.Div(
       [
        dbc.Row(
            [
            leftColumn, rightColumn
            ]
        ),
        html.P(id='placeholder'),
        dbc.Row(html.Center(html.Div([dbc.Button('Submit', color="secondary", id='submit-button')]))),
        dbc.Row(html.Center(html.Div(f"Completed 0/{totalVideos}", id='status-count'), style=color))], id='controls', style={'display':'none'})
        ], id='mainApp')
    ]
)

app.layout = html.Div(children=[
    mainApp
])

@app.callback(
    [Output("modal", "is_open"),
     Output("htmlVideoPlayer", "style")],
    [Input("modal-submit", "n_clicks")],
    [State("modal-Email", "value")],
    prevent_initial_call=True)
def toggle_modal(modal_click, modal_email):
    if not modal_email:
        modal_email = ''
    if len(modal_email) < 3:
        return True, {'display': 'none'}
    modal_email = modal_email.replace("@","_at_").replace(".", "_dot_")
    global userEmail
    userEmail = modal_email
    return False, {'display': 'block'}




@app.callback(
    Output('slider-A-output', 'children'),
    Input('slider-A', 'value'))
def update_output_A(value):
    return '{}'.format(value)

@app.callback(
    Output('slider-B-output', 'children'),
    Input('slider-B', 'value'))
def update_output_B(value):
    return '{}'.format(value)

@app.callback(
        Output('status-count', 'children'),
        Output('modalEnd', 'is_open'),
        Output('videoPlayer', 'url'),
        Input('submit-button', 'n_clicks'),
        State('slider-A', 'value'),
        State('slider-B', 'value'),
        prevent_initial_call=True
)
def submitButton(_click, aValue, bValue):
    global scores 
    global test_csv
    _nextTest = test_csv.pop(0)
    scores['TestID'].append(_nextTest['TESTID'])
    scores['AScore'].append(aValue)
    scores['BScore'].append(bValue)
    if not test_csv:
        _scoresDF = pd.DataFrame(scores)
        _scoresDF.to_csv(f'data/results/{userEmail}.csv', index=False)
        test_csv = pd.read_csv("data/testData.csv").to_dict(orient='records')
        return f'Completed {totalVideos-len(test_csv)}/{totalVideos}', True, _nextTest['CLIPNAME']
    nextVideo = test_csv[0]['CLIPNAME']
    return f'Completed {totalVideos-len(test_csv)}/{totalVideos}', False, nextVideo

if __name__ == '__main__':
    app.run_server(debug=True)

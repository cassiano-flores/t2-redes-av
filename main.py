# SNMP Manager
#
# Integrantes:
# - Cassiano Luis Flores Michel
# - José Eduardo Serpa Rodrigues
# - Pedro Menuzzi Mascaró

import dash
from dash.dependencies import Output, Input
from dash import dcc
from dash import html
import plotly
import plotly.graph_objs as go
from collections import deque
import time
from datetime import datetime
from pysnmp.hlapi import *

# SNMP parameters
community = 'public'
host = 'localhost'
port = 161

oids = {
    'ifNumber': '1.3.6.1.2.1.2.1.0',
    'ifInErrors': '1.3.6.1.2.1.2.2.1.14',  # Número de pacotes recebidos com erro.
    'ifSpeed': '1.3.6.1.2.1.2.2.1.5',  # Velocidade do link.
    'ipInDiscards': '1.3.6.1.2.1.4.3.0',  # Porcentagem de datagramas IP recebidos com erro.
    'ipForwDatagrams': '1.3.6.1.2.1.4.6.0',  # Taxa de forwarding de datagramas IP por segundo
    'tcpInSegs': '1.3.6.1.2.1.6.10.0',  # Número de segmentos TCP recebidos
    'tcpOutSegs': '1.3.6.1.2.1.6.11.0',  # Número de segmentos TCP transmitidos
    'udpInDatagrams': '1.3.6.1.2.1.7.1.0',  # Número de datagramas UDP recebidos
    'udpOutDatagrams': '1.3.6.1.2.1.7.4.0',  # Número de datagramas UDP transmitidos
    'sysUpTime': '1.3.6.1.2.1.1.3.0',  # Tempo desde a última reinicialização do agente.
    'sysLocation': '1.3.6.1.2.1.1.6.0',  # Localização física do agente.
    'sysContact': '1.3.6.1.2.1.1.4.0',  # Informações de contato do administrador do sistema.
    'sysName': '1.3.6.1.2.1.1.5.0',  # Nome do sistema.
    'sysDescr': '1.3.6.1.2.1.1.1.0',  # Descrição do sistema.
    'ifTable': '1.3.6.1.2.1.2.2',  # Tabela de interfaces de rede.
    'ipAddrTable': '1.3.6.1.2.1.4.20',  # Tabela de endereços IP
    'ipRouteTable': '1.3.6.1.2.1.4.21',  # Tabela de rotas IP
    'tcpConnTable': '1.3.6.1.2.1.6.13',  # Tabela de conexões TCP
    'icmpInEchoReps': '1.3.6.1.2.1.5.21.0',  # Número de respostas de eco ICMP recebidas.
    'icmpOutEchoReps': '1.3.6.1.2.1.5.22.0',  # Número de respostas de eco ICMP transmitidas.
    'snmpInPkts': '1.3.6.1.2.1.11.1.0',  # Número de pacotes SNMP recebidos.
    'snmpOutPkts': '1.3.6.1.2.1.11.2.0',  # Número de pacotes SNMP transmitidos.
    'ifInUcastPkts': '1.3.6.1.2.1.2.2.1.11',
    'ifInNUcastPkts': '1.3.6.1.2.1.2.2.1.12',
    'ifInOctets': '1.3.6.1.2.1.2.2.1.10',
    'ifOutOctets': '1.3.6.1.2.1.2.2.1.16',
}

# Configurações de Gráficos
X = []
Y = {key: [] for key in oids}


def get_snmp_data(oid):
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((host, port)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    error_indication, error_status, error_index, var_binds = next(iterator)

    if error_indication:
        print(error_indication)
        return None
    elif error_status:
        print('%s at %s' % (
            error_status.prettyPrint(),
            error_index and var_binds[int(error_index) - 1][0] or '?'
        ))
        return None
    else:
        for var_bind in var_binds:
            return var_bind[1]



# Função para realizar a consulta SNMP usando bulkCmd
def get_snmp_bulk(oid):
    # Criar a lista de OIDs para todas as interfaces
    oids_to_query = [f'{oid}.{i}' for i in range(1, ifNumberObject + 1)]

    # Consulta SNMP usando bulkCmd
    iterator = bulkCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((host, port)),
        ContextData(),
        0, 25,  # Non-repeaters and max-repetitions
        *[
            ObjectType(ObjectIdentity(oid)) for oid in oids_to_query
        ]
    )

    error_indication, error_status, error_index, var_binds_table = next(iterator)

    if error_indication:
        print(f'Error indication: {error_indication}')
        return None
    elif error_status:
        print(f'Error status: {error_status.prettyPrint()} at {error_index}')
        return None
    else:
        # Extrair os valores para todas as interfaces
        values_for_interfaces = [int(var_bind[1]) for var_bind in var_binds_table]

        return values_for_interfaces





app = dash.Dash(__name__)
final_html = html.Div(
    [
        dcc.Interval(
            id='my-input',
            interval=5 * 1000,
            n_intervals=0
        ),

        html.H1('Simple Network Management Protocol - Monitores de Recurso e Desempenho'),

        html.Div([

            html.Div([
                html.H3('Info'),
                html.Div(id='my-output')
            ], style={'display': 'flex', 'flex-direction': 'column', 'width': '100%'}),

            html.H3('Desempenho'),
            html.Div([
                dcc.Graph(style={'width': '50%', 'height': '50%'}, id='graph1', animate=True),
                dcc.Graph(style={'width': '50%', 'height': '50%'}, id='graph2', animate=True)
            ], style={'display': 'flex',
                      'flex-direction': 'row',
                      'width': '100%',
                      }),

            html.Div([
                dcc.Graph(style={'width': '50%', 'height': '50%'}, id='graph3', animate=True),
                dcc.Graph(style={'width': '50%', 'height': '50%'}, id='graph4', animate=True)
            ], style={'display': 'flex',
                      'flex-direction': 'row',
                      'width': '100%',
                      }),

            html.Div([
                dcc.Graph(style={'width': '50%', 'height': '50%'}, id='graph5', animate=True),
                dcc.Graph(style={'width': '50%', 'height': '50%'}, id='graph6', animate=True)
            ], style={'display': 'flex',
                      'flex-direction': 'row',
                      'width': '100%',
                      })

        ], style={'display': 'flex', 'flex-direction': 'column'}),

    ], style={'display': 'flex', 'flex-direction': 'column', 'font-family': 'Roboto thin'}

)
app.layout = final_html


def decode(string):
    string_final = ''
    for c in string:
        string_final += chr(c)
    return string_final


x1 = deque(maxlen=20)
y1 = deque(maxlen=20)
x2 = deque(maxlen=20)
y2 = deque(maxlen=20)
x3 = deque(maxlen=20)
y3 = deque(maxlen=20)


@app.callback(
    Output('graph1', 'figure'),
    [Input('my-input', 'n_intervals')]
)
def update_graph1(n):
    tempo_atual_em_segundos = time.time()
    data_hora_atual = datetime.fromtimestamp(tempo_atual_em_segundos)
    # hora_formatada = data_hora_atual.strftime("%H:%M:%S")
    x1.append(data_hora_atual)
    y1.append(int(get_snmp_data('1.3.6.1.2.1.5.21.0')))

    data = plotly.graph_objs.Scatter(
        x=list(x1),
        y=list(y1),
        name='Scatter',
        mode='lines+markers'
    )

    layout = go.Layout(
        title='Requisições ICMP ECHO Recebidas',
        xaxis=dict(title='Tempo (hh:mm:ss)', range=[min(x1), max(x1)]),
        yaxis=dict(title='Requisições', range=[min(y1), max(y1)]),
    )

    return {'data': [data], 'layout': layout}

@app.callback(
    Output('graph2', 'figure'),
    [Input('my-input', 'n_intervals')]
)
def update_graph2(n):
    tempo_atual_em_segundos = time.time()
    data_hora_atual = datetime.fromtimestamp(tempo_atual_em_segundos)
    # hora_formatada = data_hora_atual.strftime("%H:%M:%S")
    x2.append(data_hora_atual)
    y2.append(porcentagem_pacotes_recebidos_erro())


    data = plotly.graph_objs.Scatter(
        x=list(x2),
        y=list(y2),
        name='Scatter',
        mode='lines+markers'
    )

    layout = go.Layout(
        title='Porcentagem de pacotes recebidos com erro',
        xaxis=dict(title='Tempo (hh:mm:ss)', range=[min(x2), max(x2)]),
        yaxis=dict(title='%', range=[min(y2), max(y2)]),
    )

    return {'data': [data], 'layout': layout}


@app.callback(
    Output('graph3', 'figure'),
    [Input('my-input', 'n_intervals')]
)
def update_graph3(n):
    tempo_atual_em_segundos = time.time()
    data_hora_atual = datetime.fromtimestamp(tempo_atual_em_segundos)
    # hora_formatada = data_hora_atual.strftime("%H:%M:%S")
    x3.append(data_hora_atual)
    y3.append(int(taxa_bytes_segundo()/1000000))


    data = plotly.graph_objs.Scatter(
        x=list(x3),
        y=list(y3),
        name='Scatter',
        mode='lines+markers'
    )

    layout = go.Layout(
        title='Taxa de Bytes/Segundo',
        xaxis=dict(title='Tempo (s)', range=[min(x3), max(x3)]),
        yaxis=dict(title='MegaBytes', range=[min(y3), max(y3)]),
    )

    return {'data': [data], 'layout': layout}


@app.callback(
    Output(component_id='my-output', component_property='children'),
    Input(component_id='my-input', component_property='n_intervals')
)
def update_data(n):
    sysDescrObject = decode(get_snmp_data('1.3.6.1.2.1.1.1.0'))
    software = sysDescrObject.split("Software: ")
    hardware = sysDescrObject.split("Software: ")
    hardware = hardware[0]

    total_milissegundos = get_snmp_data('1.3.6.1.2.1.1.3.0')
    total_segundos = total_milissegundos // 100
    dias = total_segundos // (24 * 3600)
    horas = (total_segundos % (24 * 3600)) // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60

    nome = get_snmp_data('1.3.6.1.2.1.1.5.0')

    n_interfaces = get_snmp_data('1.3.6.1.2.1.2.1.0')

    dump = html.Div([
        html.Label(["Nome do dispositivo: "], style={'font-weight': 'bold'}),
        html.Label(f"{decode(nome)}"),
        html.Br(),
        html.Label(["Número de interfaces presentes no sistema: "], style={'font-weight': 'bold'}),
        html.Label(f"{n_interfaces}"),
        html.Br(),
        html.Label(["Hardware: "], style={'font-weight': 'bold'}), html.Label(f"{hardware[10:len(hardware) - 2]}"),
        html.Br(),
        html.Label(["Software: "], style={'font-weight': 'bold'}), html.Label(f"{software[1]}"),
        html.Br(),
        html.Label(["Tempo Ativo do Sistema: "], style={'font-weight': 'bold'}),
        html.Label(f"{dias} dias, {horas} horas, {minutos} minutos e {segundos} segundos"),
        html.Br(),

    ], )

    return dump



# ******************************* Métricas *******************************
ifNumberObject = int(get_snmp_data(oids['ifNumber']))
interval_time = 5

def porcentagem_pacotes_recebidos_erro():
    if_in_errors = sum(get_snmp_bulk(oids['ifInErrors']))
    if_in_ucast_pkts = sum(get_snmp_bulk(oids['ifInUcastPkts']))
    if_in_n_ucast_pkts = sum(get_snmp_bulk(oids['ifInNUcastPkts']))

    if (if_in_ucast_pkts + if_in_n_ucast_pkts) > 0:
        return if_in_errors / (if_in_ucast_pkts + if_in_n_ucast_pkts)

    return if_in_errors

def taxa_bytes_segundo():
    if_in_octets = sum(get_snmp_bulk(oids['ifInOctets']))
    if_out_octets = sum(get_snmp_bulk(oids['ifOutOctets']))
    second_time = time.time()
    first_time = int(time.time() - interval_time)

    return ((((if_in_octets + if_out_octets) * second_time) - ((if_in_octets + if_out_octets) * first_time)) /
            (second_time - first_time))


if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port=8080, debug=True)

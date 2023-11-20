# SNMP Manager

# Integrantes:
# - Cassiano Luis Flores Michel
# - José Eduardo Serpa Rodrigues
# - Pedro Menuzzi Mascaró

import dash
from dash import dcc, html, Input, Output
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

# Objetos utilizados no gerente
oids = {
    'sysInformations': '1.3.6.1.2.1.1',
    'sysDescr': '1.3.6.1.2.1.1.1.0',
    'sysObjectID': '1.3.6.1.2.1.1.2.0',
    'sysUpTime': '1.3.6.1.2.1.1.3.0',
    'sysContact': '1.3.6.1.2.1.1.4.0',
    'sysName': '1.3.6.1.2.1.1.5.0',
    'sysLocation': '1.3.6.1.2.1.1.6.0',
    'sysServices': '1.3.6.1.2.1.1.7.0',
    'ifNumber': '1.3.6.1.2.1.2.1.0',
    'ifInErrors': '1.3.6.1.2.1.2.2.1.14',
    'ifSpeed': '1.3.6.1.2.1.2.2.1.5',
    'ifInUcastPkts': '1.3.6.1.2.1.2.2.1.11',
    'ifInNUcastPkts': '1.3.6.1.2.1.2.2.1.12',
    'ifInOctets': '1.3.6.1.2.1.2.2.1.10',
    'ifOutOctets': '1.3.6.1.2.1.2.2.1.16',
    'ifName': '1.3.6.1.2.1.31.1.1.1.1',
    'ipInHdrErrors': '1.3.6.1.2.1.4.4.0',
    'ipInAddrErrors': '1.3.6.1.2.1.4.5.0',
    'ipInUnknownProtos': '1.3.6.1.2.1.4.7.0',
    'ipInReceives': '1.3.6.1.2.1.4.3.0',
    'ipForwDatagrams': '1.3.6.1.2.1.4.6.0',
    'icmpInEchoReps': '1.3.6.1.2.1.5.21.0',
}

# Configurações de Gráficos
X = []
Y = {key: [] for key in oids}

countTime = 0
agentStatus = {
    'index': -1,
    'background': 'transparent',
    'color': 'transparent'
}


# Funções snmpget (recupera um em específico), snmpbulkget e snmpwalk
def snmpget(oid):
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


def snmpbulkget(oid, isint=True):
    # Criar a lista de OIDs para todas as interfaces
    oids_to_query = [f'{oid}.{i}' for i in range(1, if_number_object + 1)]

    # Consulta SNMP usando bulkCmd
    iterator = bulkCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((host, port)),
        ContextData(),
        0, 25,
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
        if isint:
            values_for_interfaces = [int(var_bind[1]) if var_bind[1] else 0 for var_bind in var_binds_table]
        else:
            values_for_interfaces = [var_bind[1] if var_bind[1] else 0 for var_bind in var_binds_table]

        return values_for_interfaces


def snmpwalk(oid):
    iterator = nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((host, port)),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lexicographicMode=False  # Desativa o modo lexicográfico para um walk
    )

    results = []

    for error_indication, error_status, error_index, var_binds_table in iterator:
        if error_indication:
            print(error_indication)
            return None
        elif error_status:
            print('%s at %s' % (
                error_status.prettyPrint(),
                error_index and var_binds_table[int(error_index) - 1][0] or '?'
            ))
            return None
        else:
            for var_bind in var_binds_table:
                results.append(var_bind[1])

    return results


# Estrutura básica
app = dash.Dash(__name__)
final_html = html.Div(
    [
        dcc.Interval(
            id='my-input',
            interval=5 * 1000,
            n_intervals=0
        ),

        html.H1('Agente inativo! Tentando reconexão...',
                style={'color': f"{agentStatus['color']}", 'width': '100%', 'justify-content': 'center',
                       'text-align': 'center', 'position': 'absolute', 'background': f"{agentStatus['background']}",
                       'z-index': f"{agentStatus['index']}"}),

        html.H1('Simple Network Management Protocol - Monitores de Recurso e Desempenho',
                style={'width': '100%', 'justify-content': 'center', 'text-align': 'center'}),

        html.Div([

            html.Div([
                html.H2('Informações', style={'width': '100%', 'justify-content': 'center', 'text-align': 'center',
                                              'border': 'solid 2px black'}),
                html.Div(id='my-output')
            ], style={'display': 'flex', 'flex-direction': 'column', 'width': '100%'}),

            html.H2('Desempenho', style={'width': '100%', 'justify-content': 'center', 'text-align': 'center',
                                         'border': 'solid 2px black'}),
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
x4 = deque(maxlen=20)
y4 = deque(maxlen=20)
x5 = deque(maxlen=20)
y5 = deque(maxlen=20)
x6 = deque(maxlen=20)
y6 = deque(maxlen=20)

# Informações do sistema recuperadas com apenas 1 snmpwalk
sysInformations = snmpwalk(oids['sysInformations'])
sysDescr = sysInformations[0]
sysObjectID = sysInformations[1]
sysUpTime = sysInformations[2]
sysContact = sysInformations[3]
sysName = sysInformations[4]
sysLocation = sysInformations[5]
sysServices = sysInformations[6]


# Os gráficos abaixo são para Desempenho
@app.callback(
    Output('graph1', 'figure'),
    [Input('my-input', 'n_intervals')]
)
def update_graph1(n):
    tempo_atual_em_segundos = time.time()
    data_hora_atual = datetime.fromtimestamp(tempo_atual_em_segundos)
    x1.append(data_hora_atual)
    y1.append(int(snmpget(oids['icmpInEchoReps'])))

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
    x3.append(data_hora_atual)
    y3.append(int(taxa_bytes_segundo() / 1000000))

    data = plotly.graph_objs.Scatter(
        x=list(x3),
        y=list(y3),
        name='Scatter',
        mode='lines+markers'
    )

    layout = go.Layout(
        title='Taxa de Bytes/Segundo',
        xaxis=dict(title='Tempo (hh:mm:ss)', range=[min(x3), max(x3)]),
        yaxis=dict(title='MegaBytes', range=[min(y3), max(y3)]),
    )

    return {'data': [data], 'layout': layout}


@app.callback(
    Output('graph4', 'figure'),
    [Input('my-input', 'n_intervals')]
)
def update_graph4(n):
    tempo_atual_em_segundos = time.time()
    data_hora_atual = datetime.fromtimestamp(tempo_atual_em_segundos)
    x4.append(data_hora_atual)
    y4.append(int(utilizacao_link() * 100))

    data = plotly.graph_objs.Scatter(
        x=list(x4),
        y=list(y4),
        name='Scatter',
        mode='lines+markers'
    )

    layout = go.Layout(
        title='Porcentagem de utilização da largura de banda da rede',
        xaxis=dict(title='Tempo (hh:mm:ss)', range=[min(x4), max(x4)]),
        yaxis=dict(title='%', range=[min(y4), max(y4)]),
    )

    return {'data': [data], 'layout': layout}


@app.callback(
    Output('graph5', 'figure'),
    [Input('my-input', 'n_intervals')]
)
def update_graph5(n):
    tempo_atual_em_segundos = time.time()
    data_hora_atual = datetime.fromtimestamp(tempo_atual_em_segundos)
    x5.append(data_hora_atual)
    y5.append(int(porcentagem_datagramas_ip_recebidos_erro()))

    data = plotly.graph_objs.Scatter(
        x=list(x5),
        y=list(y5),
        name='Scatter',
        mode='lines+markers'
    )

    layout = go.Layout(
        title='Porcentagem de datagramas IP recebidos com erro',
        xaxis=dict(title='Tempo (hh:mm:ss)', range=[min(x5), max(x5)]),
        yaxis=dict(title='%', range=[min(y5), max(y5)]),
    )

    return {'data': [data], 'layout': layout}


@app.callback(
    Output('graph6', 'figure'),
    [Input('my-input', 'n_intervals')]
)
def update_graph6(n):
    tempo_atual_em_segundos = time.time()
    data_hora_atual = datetime.fromtimestamp(tempo_atual_em_segundos)
    x6.append(data_hora_atual)
    y6.append(int(porcentagem_datagramas_ip_recebidos_erro()))

    data = plotly.graph_objs.Scatter(
        x=list(x6),
        y=list(y6),
        name='Scatter',
        mode='lines+markers'
    )

    layout = go.Layout(
        title='Taxa de forwarding de datagramas IP por Segundo',
        xaxis=dict(title='Tempo (hh:mm:ss)', range=[min(x6), max(x6)]),
        yaxis=dict(title='Taxa de forwarding', range=[min(y6), max(y6)]),
    )

    return {'data': [data], 'layout': layout}


@app.callback(
    Output(component_id='my-output', component_property='children'),
    Input(component_id='my-input', component_property='n_intervals')
)
def update_data(n):
    sys_descr_object = decode(sysDescr)
    software = sys_descr_object.split("Software: ")
    hardware = sys_descr_object.split("Software: ")
    hardware = hardware[0]

    total_milissegundos = sysUpTime
    total_segundos = total_milissegundos // 100
    dias = total_segundos // (24 * 3600)
    horas = (total_segundos % (24 * 3600)) // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60

    nome = sysName

    local = 'Unknown' if decode(sysLocation) == '' else decode(sysLocation)

    n_interfaces = snmpget(oids['ifNumber'])

    servicos = sysServices

    admin_contato = 'None' if decode(sysContact) == '' else decode(sysContact)

    id_sistema = sysObjectID

    table = snmpbulkget(oids['ifName'], False)

    title_table = html.Table([html.Tr(html.Th('Interfaces de Rede:'))], style={'width': '100%'})

    content_trs = [html.Tr(html.Td(f'{decode(table[i])}, ', style={'width': '33%'})) for i in range(n_interfaces - 1)]
    content_table = html.Table(content_trs, style={'display': 'flex', 'flex-wrap': 'wrap', 'width': '100%'})

    table_html = html.Div([title_table, content_table])

    # Informações
    dump = html.Div([
        html.Label(["Nome do dispositivo: "], style={'font-weight': 'bold'}),
        html.Label(f"{decode(nome)}"),
        html.Br(),
        html.Label(["Localização: "], style={'font-weight': 'bold'}), html.Label(f"{local}"),
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
        html.Label(["Total de serviços que o sistema suporta: "], style={'font-weight': 'bold'}),
        html.Label(f"{servicos}"),
        html.Br(),
        html.Label(["Informações de contato do administrador do sistema: "], style={'font-weight': 'bold'}),
        html.Label(f"{admin_contato}"),
        html.Br(),
        html.Label(["Identificador de objeto do sistema: "], style={'font-weight': 'bold'}),
        html.Label(f"{id_sistema}"),
        html.Br(),
        table_html
    ], style={'display': 'flex', 'flex-direction': 'column', 'height': '80%', 'justify-content': 'center',
              'text-align': 'center'})

    global countTime
    global agentStatus

    # Quando der 6 ciclos, ou seja, 30 segundos, verifica sysUpTime do agente
    if countTime > 5:
        countTime = 0
        sys_up_time = snmpget(oids['sysUpTime'])

        # Se o sysUpTime for menor que 1 minuto, significa que caiu, mostrar mensagem
        if sys_up_time < 60:
            agentStatus['color'] = 'red'
            agentStatus['background'] = 'black'
            agentStatus['index'] = 1
        else:
            agentStatus['color'] = 'transparent'
            agentStatus['background'] = 'transparent'
            agentStatus['index'] = -1
    else:
        countTime += 1

    return dump


# ******************************* Métricas *******************************
if_number_object = int(snmpget(oids['ifNumber']))
interval_time = 5
second_time = time.time()
first_time = int(time.time() - interval_time)


def porcentagem_pacotes_recebidos_erro():
    if_in_errors = sum(snmpbulkget(oids['ifInErrors']))
    if_in_ucast_pkts = sum(snmpbulkget(oids['ifInUcastPkts']))
    if_in_n_ucast_pkts = sum(snmpbulkget(oids['ifInNUcastPkts']))

    if (if_in_ucast_pkts + if_in_n_ucast_pkts) > 0:
        return if_in_errors / (if_in_ucast_pkts + if_in_n_ucast_pkts)

    return if_in_errors


def taxa_bytes_segundo():
    if_in_octets = sum(snmpbulkget(oids['ifInOctets']))
    if_out_octets = sum(snmpbulkget(oids['ifOutOctets']))

    return ((((if_in_octets + if_out_octets) * second_time) - ((if_in_octets + if_out_octets) * first_time)) /
            (second_time - first_time))


def utilizacao_link():
    if_speed = sum(snmpbulkget(oids['ifSpeed']))

    return (taxa_bytes_segundo() * 8) / if_speed


def porcentagem_datagramas_ip_recebidos_erro():
    ip_in_hdr_errors = snmpget(oids['ipInHdrErrors'])
    ip_in_addr_errors = snmpget(oids['ipInAddrErrors'])
    ip_in_unknown_protos = snmpget(oids['ipInUnknownProtos'])
    ip_in_receives = snmpget(oids['ipInReceives'])

    return ((ip_in_hdr_errors + ip_in_addr_errors + ip_in_unknown_protos) / ip_in_receives) * 100


def taxa_forwarding_segundo():
    ip_forw_datagrams = snmpget(oids['ipForwDatagrams'])

    return ((ip_forw_datagrams * second_time) - (ip_forw_datagrams * first_time)) / (second_time - first_time)


if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port=8080, debug=True)

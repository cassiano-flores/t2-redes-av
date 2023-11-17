import dash 
from dash.dependencies import Output, Input
from dash import dcc
from dash import html
import plotly 
import plotly.graph_objs as go 
from collections import deque 
import time
from pysnmp.hlapi import *

# SNMP Manager
#
# Integrantes:
# - Cassiano Luis Flores Michel
# - José Eduardo Serpa Rodrigues
# - Pedro Menuzzi Mascaró

# SNMP parameters
community = 'public'
host = 'localhost'
port = 161

oids = {
#	'sysDescr': '1.3.6.1.2.1.1.1',
    'ifInErrors': '1.3.6.1.2.1.2.2.1.14.1',    # Número de pacotes recebidos com erro.
    'ifOutOctets': '1.3.6.1.2.1.2.2.1.16.1',   # Número de bytes transmitidos por segundo.
    'ifSpeed': '1.3.6.1.2.1.2.2.1.5.1',        # Velocidade do link.
    'ipInDiscards': '1.3.6.1.2.1.4.3.0',       # Porcentagem de datagramas IP recebidos com erro.
    'ipForwDatagrams': '1.3.6.1.2.1.4.6.0',    # Taxa de forwarding de datagramas IP por segundo
    'tcpInSegs': '1.3.6.1.2.1.6.10.0',         # Número de segmentos TCP recebidos
    'tcpOutSegs': '1.3.6.1.2.1.6.11.0',        # Número de segmentos TCP transmitidos
    'udpInDatagrams': '1.3.6.1.2.1.7.1.0',     # Número de datagramas UDP recebidos
    'udpOutDatagrams': '1.3.6.1.2.1.7.4.0',    # Número de datagramas UDP transmitidos
    'sysUpTime': '1.3.6.1.2.1.1.3.0',          # Tempo desde a última reinicialização do agente.
    'sysLocation': '1.3.6.1.2.1.1.6.0',        # Localização física do agente.
    'sysContact': '1.3.6.1.2.1.1.4.0',         # Informações de contato do administrador do sistema.
    'sysName': '1.3.6.1.2.1.1.5.0',            # Nome do sistema.
    'sysDescr': '1.3.6.1.2.1.1.1.0',           # Descrição do sistema.
    'ifTable': '1.3.6.1.2.1.2.2',              # Tabela de interfaces de rede.
    'ipAddrTable': '1.3.6.1.2.1.4.20',         # Tabela de endereços IP
    'ipRouteTable': '1.3.6.1.2.1.4.21',        # Tabela de rotas IP
    'tcpConnTable': '1.3.6.1.2.1.6.13',        # Tabela de conexões TCP
    'icmpInEchoReps': '1.3.6.1.2.1.5.21.0',    # Número de respostas de eco ICMP recebidas.
    'icmpOutEchoReps': '1.3.6.1.2.1.5.22.0',   # Número de respostas de eco ICMP transmitidas.
    'snmpInPkts': '1.3.6.1.2.1.11.1.0',        # Número de pacotes SNMP recebidos.
    'snmpOutPkts': '1.3.6.1.2.1.11.2.0',       # Número de pacotes SNMP transmitidos.
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

app = dash.Dash(__name__)
final_html = html.Div(
	[
		dcc.Interval(
			id='my-input',
			interval=3 * 1000,
			n_intervals=0
		),

		html.H1('Simple Network Management Protocol - Monitores de Recurso e Desempenho'),

		html.Div([

			html.Div([
				html.H3('Info'),
				html.Div(id='my-output')
			], style={'display':'flex', 'flex-direction': 'column', 'width': '100%'}),


			html.Div([
				html.H3('Desempenho'),
				html.Label('grafico1'),
				dcc.Graph(id='live-graph', animate=True),


				html.Label('grafico2'),
				dcc.Graph(id = 'live-graph2', animate = True),


			], style={'display':'flex',
					  'flex-direction': 'column',
					  'width': '100%',
					})


		], style={'display':'flex', 'flex-direction': 'column'}),



	], style={'display' : 'flex', 'flex-direction': 'column'}


)
app.layout = final_html

def decode(string):
	string_final = ''
	for c in string:
		string_final += chr(c)
	return string_final

@app.callback(
	Output(component_id='my-output', component_property='children'),
	Input(component_id='my-input', component_property='n_intervals')
)
def update_data(n):
	sysDescrObject = decode(get_snmp_data('1.3.6.1.2.1.1.1.0'))
	sysDescrObject = sysDescrObject.split("Software: ")

	sysUpTime = get_snmp_data('1.3.6.1.2.1.1.3.0')
	print(TimeTicks.getNamedValues(sysUpTime))


	#cada objeto recuperado pelo metodo	'get_snmp_data(<oid_adress>)', retorna
	#um buffer, referente ao conteudo do packote na rede, onde devemos
	#capturar as informações para exibir na string final

	# porcentagem_pacotes_recebidos_erro = ifInErrors / (ifInUCastPkts + ifInNUCastPkts)
	#
	# taxa_bytes_segundo = (((ifInOctets + ifOutOctets) * tempo_dois) - ((ifInOctets + ifOutOctets) * tempo_um)) / (tempo_dois - tempo_um)
	#
	# utilizacao_link = (taxa_bytes_segundo * 8) / ifSpeed
	#
	# porcentagem_datagramas_IP_recebidos_erro = (ipInHdrErrors + ipInAddrErrors + ipInUnknownProtos) / ipInReceives
	#
	# taxa_forwarding_segundo = ((ipForwDatagrams * tempo_dois) - (ipForwDatagrams * tempo_um)) / (tempo_dois - tempo_um)

	final_dump = ''
	final_dump += "sysDescr:"
	final_dump += sysDescrObject[1]
	final_dump += '<br>'
	final_dump += 'sysUpTime:'
	#final_dump += sysUpTime

	return final_dump


# data = plotly.graph_objs.Scatter(
# 		x=list(X),
# 		y=list(Y),
# 		name='Scatter',
# 		mode= 'lines+markers'
# )
#
# return {'data': [data],
# 		'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),yaxis = dict(range = [min(Y),max(Y)]),)}


if __name__ == '__main__': 
	app.run_server(host='127.0.0.1', port=8080 ,debug=True)
# SNMP Manager
#
# Integrantes:
# - Cassiano Luis Flores Michel
# - José Eduardo Serpa Rodrigues
# - Pedro Menuzzi Mascaró

import tkinter as tk
from tkinter import ttk
from pysnmp.hlapi import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time

# Lista de objetos MIB II para a gerência de desempenho
mib_oids = [
    ('1.3.6.1.2.1.2.2.1.14.1', 'Porcentagem de pacotes recebidos com erro'),
    ('1.3.6.1.2.1.2.2.1.10.1', 'Taxa de bytes/segundo'),
    ('1.3.6.1.2.1.2.2.1.5.1', 'Utilização do link'),
    ('1.3.6.1.2.1.4.3.0', 'Porcentagem de datagramas IP recebidos com erro'),
    ('1.3.6.1.2.1.2.2.1.9.1', 'Taxa de forwarding/segundo'),
]

historical_data = [[] for _ in mib_oids]

# Função para consultar um objeto na MIB
def get_snmp_data(target, oid):
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData(community.get(), mpModel=0),
               UdpTransportTarget((target, 161)),
               ContextData(),
               ObjectType(ObjectIdentity(oid)))
    )

    if errorIndication:
        return None
    elif errorStatus:
        return None
    else:
        return varBinds[0][1]

# Função para atualizar os dados
def update_data():
    while monitoring:
        for i, (oid, label) in enumerate(mib_oids):
            value = get_snmp_data(agent_ips[agent_combobox.current()], oid)
            if value is not None:
                data_labels[i].config(text=f'{label}: {value.prettyPrint()}')
                historical_data[i].append((time.time(), float(value)))
            else:
                data_labels[i].config(text=f'{label}: Erro ao obter dados')

        # Verifique a queda do agente consultando sysUpTime
        sysuptime_oid = '1.3.6.1.2.1.1.3.0'
        sysuptime_value = get_snmp_data(agent_ips[agent_combobox.current()], sysuptime_oid)
        if sysuptime_value is None:
            alarm_label.config(text="Agente SNMP inativo: Alarme gerado!")

        time.sleep(periodicity.get())

# Função para iniciar o monitoramento
def start_monitor():
    global monitoring
    monitoring = True
    monitoring_thread = threading.Thread(target=update_data)
    monitoring_thread.daemon = True
    monitoring_thread.start()

# Função para parar o monitoramento
def stop_monitor():
    global monitoring
    monitoring = False

# Função para criar e exibir gráficos
def show_graph():
    fig, ax = plt.subplots()
    for i, (oid, label) in enumerate(mib_oids):
        values = []
        timestamps = []
        for data_point in historical_data[i]:
            timestamps.append(data_point[0])
            values.append(data_point[1])
        ax.plot(timestamps, values, label=label)
    ax.set_xlabel('Tempo')
    ax.set_ylabel('Valores')
    ax.legend()
    graph_window = tk.Toplevel(root)
    graph_window.title("Gráficos")
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack()
    canvas.draw()

# Configuração da interface gráfica
root = tk.Tk()
root.title("Gerente SNMP")

# Variáveis para controle
monitoring = False

# Defina as máquinas e comunidades aqui
agent_ips = ['127.0.0.1', '192.168.1.1']  # Exemplo com duas máquinas
agent_combobox_label = tk.Label(root, text="Selecione a máquina:")
agent_combobox_label.pack()
agent_combobox = ttk.Combobox(root, values=agent_ips)
agent_combobox.pack()
community_label = tk.Label(root, text="Comunidade SNMP:")
community_label.pack()
community = tk.StringVar()
community_entry = tk.Entry(root, textvariable=community)
community_entry.pack()

# Configuração do tempo de periodicidade
periodicity_label = tk.Label(root, text="Tempo de periodicidade (segundos):")
periodicity_label.pack()
periodicity = tk.DoubleVar()
periodicity_entry = tk.Entry(root, textvariable=periodicity)
periodicity_entry.pack()

# Botões de controle
start_button = tk.Button(root, text="Iniciar Monitoramento", command=start_monitor)
start_button.pack()
stop_button = tk.Button(root, text="Parar Monitoramento", command=stop_monitor)
stop_button.pack()
graph_button = tk.Button(root, text="Exibir Gráficos", command=show_graph)
graph_button.pack()

# Rótulo de alarme
alarm_label = tk.Label(root, text="", fg="red")
alarm_label.pack()

# Lista de objetos MIB II para exibir os resultados
data_labels = []

# Crie rótulos para exibir os resultados
for oid, label in mib_oids:
    data_label = tk.Label(root, text=f'{label}: Aguardando atualização...')
    data_label.pack()
    data_labels.append(data_label)

root.mainloop()

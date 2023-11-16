# SNMP Manager
#
# Integrantes:
# - Cassiano Luis Flores Michel
# - José Eduardo Serpa Rodrigues
# - Pedro Menuzzi Mascaró

from pysnmp.hlapi import *
import matplotlib.pyplot as plt
import time

# Configurações SNMP
community_string = "public"
target_ip = "localhost"

# Dicionário de OIDs
oids = {
    'ifInErrors': '1.3.6.1.2.1.2.2.1.14.1',
    'ifOutOctets': '1.3.6.1.2.1.2.2.1.16.1',
    'ifSpeed': '1.3.6.1.2.1.2.2.1.5.1',
    'ipInDiscards': '1.3.6.1.2.1.4.3.0',
    'ipForwDatagrams': '1.3.6.1.2.1.4.6.0',
    'tcpInSegs': '1.3.6.1.2.1.6.10.0',
    'tcpOutSegs': '1.3.6.1.2.1.6.11.0',
    'udpInDatagrams': '1.3.6.1.2.1.7.1.0',
    'udpOutDatagrams': '1.3.6.1.2.1.7.4.0',
    'sysUpTime': '1.3.6.1.2.1.1.3.0',
    'sysLocation': '1.3.6.1.2.1.1.6.0',
    'sysContact': '1.3.6.1.2.1.1.4.0',
    'sysName': '1.3.6.1.2.1.1.5.0',
    'sysDescr': '1.3.6.1.2.1.1.1.0',
    'ifTable': '1.3.6.1.2.1.2.2',
    'ipAddrTable': '1.3.6.1.2.1.4.20',
    'ipRouteTable': '1.3.6.1.2.1.4.21',
    'tcpConnTable': '1.3.6.1.2.1.6.13',
    'icmpInEchoReps': '1.3.6.1.2.1.5.21.0',
    'icmpOutEchoReps': '1.3.6.1.2.1.5.22.0',
    'snmpInPkts': '1.3.6.1.2.1.11.1.0',
    'snmpOutPkts': '1.3.6.1.2.1.11.2.0',
}

# Configurações de Gráficos
x_data = []
y_data = {key: [] for key in oids}

def snmp_get(oid):
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData(community_string),
               UdpTransportTarget((target_ip, 161)),
               ContextData(),
               ObjectType(ObjectIdentity(oid)))
    )

    if errorIndication:
        print(errorIndication)
        return None
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(), varBinds[int(errorIndex)-1] if errorIndex else '?'))
        return None
    else:
        return varBinds[0][1]

def update_data():
    # Atualiza os dados a serem exibidos nos gráficos
    x_data.append(time.time())  # Use timestamps como valores x

    # Itera sobre o dicionário de oids
    for key, oid in oids.items():
        y_data[key].append(snmp_get(oid))

def plot_graphs():
    # Gera gráficos
    for key, values in y_data.items():
        plt.plot(x_data, values, label=key)

def main():
    # Configurações iniciais e loop principal
    update_interval = 3  # Atualiza os dados a cada 60 segundos

    while True:
        update_data()
        plot_graphs()
        time.sleep(update_interval)

if __name__ == "__main__":
    main()

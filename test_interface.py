from scapy.all import get_if_list, get_if_hwaddr

interfaces = get_if_list()
print("Available interfaces:")
for iface in interfaces:
    try:
        print(f"{iface} - {get_if_hwaddr(iface)}")
    except Exception as e:
        print(f"{iface} - Unable to retrieve hardware address")

"""
Guide:

Kør scriptet og find mac adresser på interfaces.

Match dette med ifconfig eller ipconfig mac adresse under det valgte ethernet interface.

Indsæt det matchende interface under iface i scapy - ved passive_monitoring.py
"""
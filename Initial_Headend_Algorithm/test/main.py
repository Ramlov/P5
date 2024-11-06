# main.py

from PM import PassiveMonitoring

def main():
    # Initialize PassiveMonitoring on loopback interface "lo" for local testing
    passive_monitor = PassiveMonitoring(interface="lo")
    passive_monitor.start_monitoring()

if __name__ == "__main__":
    main()

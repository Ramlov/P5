import csv
from datetime import datetime

class CSVLogger:
    def __init__(self, csv_file='network_metrics.csv'):
        self.csv_file = csv_file
        self.csv_columns = ['Timestamp', 'FD_ID', 'IP_Address', 'Latency', 'Packet_Loss', 'Throughput', 'Status']
        self._ensure_file_initialized()

    def _ensure_file_initialized(self):
        # Ensure the file has the correct header if it's empty or doesn't exist
        try:
            with open(self.csv_file, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.csv_columns)
                if file.tell() == 0:  # File is empty, write the header
                    writer.writeheader()
        except IOError as e:
            print(f"Failed to initialize CSV file: {e}")

    def log(self, fd_id, ip_address, latency, packet_loss, throughput, status):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_row = {
            'Timestamp': timestamp,
            'FD_ID': fd_id,
            'IP_Address': ip_address,
            'Latency': latency if latency is not None else 'N/A',
            'Packet_Loss': packet_loss,
            'Throughput': throughput if throughput is not None else 'N/A',
            'Status': status
        }

        try:
            with open(self.csv_file, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.csv_columns)
                writer.writerow(data_row)
        except IOError as e:
            print(f"Failed to write to CSV file: {e}")

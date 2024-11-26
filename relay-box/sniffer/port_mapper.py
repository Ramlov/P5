import time

class PortMatcher:
    def __init__(self, port_range):
        """
        Initializes the PortMatcher with a specified range of allowed source ports.
        """
        self.port_map = {}  # Stores dst_port as key, (src_port, timestamp) as value
        self.port_range = port_range

    def _cleanup(self):
        """
        Removes mappings that are older than 5 seconds.
        """
        current_time = time.time()
        self.port_map = {
            dst_port: (src_port, timestamp)
            for dst_port, (src_port, timestamp) in self.port_map.items()
            if current_time - timestamp <= 5
        }
        print(f"Cleaned up mappings: {self.port_map}")

    def port_mapping(self, dst_port, src_port):
        """
        Adds or updates a mapping from src_port to dst_port if src_port is within the allowed range.
        Removes outdated mappings before proceeding.
        """
        self._cleanup()

        if src_port in self.port_range:
            print(f"Mapping {src_port} to {dst_port}")
            self.port_map[dst_port] = (src_port, time.time())
            return src_port
        else:
            return self.get_mapping(dst_port)

    def get_mapping(self, dst_port):
        """
        Retrieves the src_port for a given dst_port.
        Removes outdated mappings before proceeding.
        Returns None if no valid mapping exists.
        """
        self._cleanup()
        mapping = self.port_map.get(dst_port)
        print(f"Retrieved mapping for {dst_port}: {mapping}")
        return mapping[0] if mapping else None

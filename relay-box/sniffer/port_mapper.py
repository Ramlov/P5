import time

class PortMatcher:
    def __init__(self, port_range):
        """
        Initializes the PortMatcher with a specified range of allowed destination ports.
        """
        self.port_map = {}  # Stores src_port as key, (dst_port, timestamp) as value
        self.port_range = port_range

    def _cleanup(self):
        """
        Removes mappings that are older than 5 seconds.
        """
        current_time = time.time()
        self.port_map = {
            src_port: (dst_port, timestamp)
            for src_port, (dst_port, timestamp) in self.port_map.items()
            if current_time - timestamp <= 5
        }
        # print(f"Cleaned up mappings: {self.port_map}")

    def port_mapping(self, src_port, dst_port):
        """
        Adds or updates a mapping from src_port to dst_port if src_port is within the allowed range.
        Removes outdated mappings before proceeding.
        """
        self._cleanup()
        if src_port in self.port_range:
            # If src_port is valid, create or update the mapping.
            self.port_map[src_port] = (dst_port, time.time())
            return dst_port
        else:
            # If src_port is not in the allowed range, check for an existing mapping.
            existing_mapping = self.get_mapping(src_port)
            if existing_mapping is not None:
                return existing_mapping
            # If no existing mapping, create a new one to the provided dst_port.
            self.port_map[src_port] = (dst_port, time.time())
            return dst_port

        
    def get_mapping(self, src_port):
        """
        Retrieves the dst_port for a given src_port.
        Removes outdated mappings before proceeding.
        Returns None if no valid mapping exists.
        """
        self._cleanup()
        mapping = self.port_map.get(src_port)
        if mapping:
            # print(f"Retrieved mapping for {src_port}: {mapping[0]}")
            return mapping[0]
        return None

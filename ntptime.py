import os
import ntplib
from time import time
from datetime import datetime


def check_and_update_time(ntp_server="pool.ntp.org", max_difference_seconds=3600):
    """
    Check the system time against an NTP server and update if the difference exceeds a threshold.

    :param ntp_server: The NTP server to query.
    :param max_difference_seconds: Maximum allowed time difference in seconds.
    :return: A message indicating whether the time was updated or not.
    """
    try:
        # Create an NTP client
        client = ntplib.NTPClient()
        
        # Request time from the NTP server
        response = client.request(ntp_server, version=3)
        
        # Get the current system time
        current_time = time()
        
        # Calculate the time difference
        time_difference = abs(current_time - response.tx_time)
        
        # Check if the time difference exceeds the allowed threshold
        if time_difference < max_difference_seconds:
            return "System time is within the acceptable range. No update needed."
        
        # Format the NTP server time for setting
        new_time = datetime.utcfromtimestamp(response.tx_time).strftime("%Y-%m-%d %H:%M:%S")
        
        # Set the system time (requires sudo)
        os.system(f"sudo date -u -s '{new_time}'")
        
        return "System time was updated successfully."
    
    except Exception as e:
        return f"An error occurred: {e}"
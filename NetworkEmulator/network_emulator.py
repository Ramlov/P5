NETWORK_PROFILES = {
    "SLOW": {
        "latency": 1100
    },
    "NORMAL": {
        "latency": 250
    },
    "GOOD": {
        "latency": 50
    }
}

FIELD_DEVICE_PROFILES = [ # we only define the field devices that will have SLOW network profile.
    {
        "id": 0,
        "profile": "SLOW"
    },
    {
        "id": 1,
        "profile": "SLOW"
    }
]

PACKET_LOSS_SEQUENCES = {
    0: {
        "index": 0,
        "p": [0,0,0,0,0,1,0,1,0]
    },
    1: {
        "index": 0,
        "p": [0, 1, 0, 1, 0, 1, 0, 0, 0]
    }
}

class NetworkEmulator:
    def __init__(self) -> None:
        pass

    def _get_network_profile(self, fd_id):
        try:
            fd_profile = FIELD_DEVICE_PROFILES[fd_id]

            profile = NETWORK_PROFILES[fd_profile["profile"]]
            return profile["latency"]
        except KeyError: # field device doesnt have SLOW network profile. Use either NORMAL or GOOD profile?
            #
            return NETWORK_PROFILES["NORMAL"]

    def emulate(self, fd_id: int) -> int: #fd_id = field device ID
        try:
            fd = PACKET_LOSS_SEQUENCES[fd_id]

            index = fd["index"]
            p = fd["p"]

            # get the sequence p_i based on index
            p_i = p[index]

            # increment index
            PACKET_LOSS_SEQUENCES[fd_id]["index"]+=1

            if p_i == 1: # drop package
                return 1105
            
            # get network profile for field device
            # apply conditions
            latency = self._get_network_profile(fd_id)
            print(f"Latency: {latency}")


        except KeyError:
            print(f"Field Device ({fd_id}) has no packet loss sequence associated.")
        pass

if __name__ == '__main__':
    ne = NetworkEmulator()
    ne.emulate(0)
    
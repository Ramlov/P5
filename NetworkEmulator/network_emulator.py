import time, json

NETWORK_PROFILES = {
    "SLOW": {
        "latency": 1100
    },
    "NORMAL": {
        "latency": 300
    },
    "GOOD": {
        "latency": 50
    }
}

PACKET_LOSS_SEQUENCES = {
    0: {
        "index": 0,
        "p": [0,0,0,0,0,1,0,1,0]
    },
    1: {
        "index": 0,
        "p": [0,1,0,1,0,1,0,0,0]
    }
}

class NetworkEmulator:
    def __init__(self) -> None:
        pass

    def _get_network_profile(self, fd_id):
        try:
            # get profiles
            with open('./NetworkEmulator/fd_profiles.json') as json_file:
                data = json.load(json_file)
                profile = next((item['profile']
                               for item in data if item['id'] == fd_id), None)
                
                if profile is None: # no profile found
                    return NETWORK_PROFILES["NORMAL"]["latency"]

                return NETWORK_PROFILES[profile]["latency"]
        except KeyError: # field device doesnt have SLOW network profile. Use either NORMAL or GOOD profile? or pick random profile?
            #
            return NETWORK_PROFILES["NORMAL"]

    def emulate(self, fd_id: int) -> int: #fd_id = field device ID
        try:
            fd = PACKET_LOSS_SEQUENCES[fd_id]

            index = fd["index"]
            p = fd["p"]

            # check if index is at the end
            if index >= len(p): #reset counter
                PACKET_LOSS_SEQUENCES[fd_id]["index"] = 0
                index = 0

            # get the sequence p_i based on index
            p_i = p[index]

            # increment index
            PACKET_LOSS_SEQUENCES[fd_id]["index"]+=1

            if p_i == 1: # drop package
                print("Packet Loss!")
                return 1105 # just some random return code
        
        except KeyError:
            print(f"Field Device ({fd_id}) has no packet loss sequence associated.")
        
        # get network profile for field device
        latency = self._get_network_profile(fd_id)
        print(f"Latency: {latency}")
        # apply conditions
        time.sleep(latency / 1000)
        return 0

if __name__ == '__main__':
    ne = NetworkEmulator()
    while True:
        ne.emulate(0)
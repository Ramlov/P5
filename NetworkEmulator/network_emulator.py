import time, json, random

NETWORK_PROFILES = {
    "SLOW": {
        "min": 1001,
        "max": 2000
    },
    "NORMAL": {
        "min": 300,
        "max": 500
    },
    "GOOD": {
        "min": 50,
        "max": 300
    }
}

PACKET_LOSS_SEQUENCES = { # TODO: Define sequences for fd's with SLOW profile
    0: {
        "index": 0,
        "p": [0,0,1,0,0,1,0,1,0]
    },
    1: {
        "index": 0,
        "p": [0,1,0,1,0,1,0,0,0]
    },
    2: {
        "index": 0,
        "p": [0, 1]
    }
}

class NetworkEmulator:
    def __init__(self) -> None:
        pass

    def _get_network_profile(self, fd_id):
        min = 0
        max = 0
        try:
            # get profiles
            with open('./NetworkEmulator/fd_profiles.json') as json_file:
                data = json.load(json_file)
                profile = next((item['profile']
                               for item in data if item['id'] == fd_id), None)
                if profile is None: # no profile found
                    min = NETWORK_PROFILES["NORMAL"]["min"]
                    max = NETWORK_PROFILES["NORMAL"]["max"]
                    return random.randrange(min, max)
                
                print(f"Found Profile for Field Device ID {fd_id}: {profile}")
                min = NETWORK_PROFILES[profile]["min"]
                max = NETWORK_PROFILES[profile]["max"]
                return random.randrange(min, max)
        except KeyError:
            min = NETWORK_PROFILES["NORMAL"]["min"]
            max = NETWORK_PROFILES["NORMAL"]["max"]
            return random.randrange(min, max)

    def emulate(self, fd_id: int) -> int: #fd_id = field device ID
        try:
            fd = PACKET_LOSS_SEQUENCES[fd_id]

            index = fd["index"]
            p = fd["p"]

            # check if index is at the end
            if index >= len(p): #reset counter
                PACKET_LOSS_SEQUENCES[fd_id]["index"] = 0
                index = 0

            # get the sequence p_i
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
        rc = ne.emulate(2)
        if rc == 1105:
            # dont retransmit packet
            continue
        
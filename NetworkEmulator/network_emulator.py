from throttling_profile import PROFILE_CONSTANTS, PROFILE_CONDITIONS, ThrottlingProfile

PACKET_LOSS_SEQUENCES = {
    0: {
        "index": "0",
        "pl": {0,0,0,0,0,1,0,1,0}
    },
    1: {
        "index": "0",
        "pl": {0, 1, 0, 1, 0, 1, 0, 0, 0}
    }
}

class NetworkEmulator:
    throttling_profile = ThrottlingProfile()
    network_profile = None

    def __init__(self) -> None:
        pass

    def _set_network_profile(self, profile: PROFILE_CONSTANTS):
        self.network_profile = profile

    def emulate(self, fd_id: int) -> None:
        #fd_id = field device ID
        try:
            fd = PACKET_LOSS_SEQUENCES[fd_id]

            index = fd["index"]
            pl = fd["pl"]

        except KeyError:
            print(f"Field Device ({fd_id}) has no packet loss sequence associated.")
        pass

if __name__ == '__main__':
    ne = NetworkEmulator()
    ne.emulate(4)
    
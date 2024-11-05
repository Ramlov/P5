# https://gist.github.com/theodorosploumis/fd4086ee58369b68aea6b0782dc96a2e

import enum

class PROFILE_CONSTANTS(enum.Enum):
    SLOW_3G = 1
    NORMAL_3G = 2
    GOOD_3G = 3

class PROFILE_CONDITIONS(enum.Enum):
    DOWNLOAD_KBS: 0
    UPLOAD_KBS: 1
    LATENCY_MS: 2


class ThrottlingProfile:
    ...
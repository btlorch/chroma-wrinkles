from data.encoders.encoder import Encoder
from utils.constants import LIBJPEG_TURBO_CJPEG_EXECUTABLE_KEY, LIBJPEG_TURBO_DJPEG_EXECUTABLE_KEY, LIBJPEG_TURBO, constants


class LibjpegTurboEncoder(Encoder):
    @classmethod
    def name(cls):
        return LIBJPEG_TURBO

    @property
    def cjpeg_executable(self):
        return constants[LIBJPEG_TURBO_CJPEG_EXECUTABLE_KEY]

    @property
    def djpeg_executable(self):
        return constants[LIBJPEG_TURBO_DJPEG_EXECUTABLE_KEY]

from data.encoders.encoder import Encoder
from utils.constants import LIBJPEG_CJPEG_EXECUTABLE_KEY, LIBJPEG_DJPEG_EXECUTABLE_KEY, constants, LIBJPEG_DCT_SCALING


class LibjpegDctScalingEncoder(Encoder):
    @classmethod
    def name(cls):
        return LIBJPEG_DCT_SCALING

    @property
    def cjpeg_executable(self):
        return constants[LIBJPEG_CJPEG_EXECUTABLE_KEY]

    @property
    def djpeg_executable(self):
        return constants[LIBJPEG_DJPEG_EXECUTABLE_KEY]

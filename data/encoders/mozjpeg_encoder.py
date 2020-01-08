from data.encoders.encoder import Encoder
from utils.constants import constants, MOZJPEG, MOZJPEG_CJPEG_EXECUTABLE_KEY, MOZJPEG_DJPEG_EXECUTABLE_KEY


class MozjpegEncoder(Encoder):
    @classmethod
    def name(cls):
        return MOZJPEG

    @property
    def cjpeg_executable(self):
        return constants[MOZJPEG_CJPEG_EXECUTABLE_KEY]

    @property
    def djpeg_executable(self):
        return constants[MOZJPEG_DJPEG_EXECUTABLE_KEY]

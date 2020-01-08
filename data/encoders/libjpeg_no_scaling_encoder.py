from data.encoders.encoder import Encoder
from utils.constants import LIBJPEG_CJPEG_EXECUTABLE_KEY, LIBJPEG_DJPEG_EXECUTABLE_KEY, constants, LIBJPEG_NO_SCALING


class LibjpegNoScalingEncoder(Encoder):
    @classmethod
    def name(cls):
        return LIBJPEG_NO_SCALING

    @property
    def cjpeg_executable(self):
        return constants[LIBJPEG_CJPEG_EXECUTABLE_KEY]

    @property
    def djpeg_executable(self):
        return constants[LIBJPEG_DJPEG_EXECUTABLE_KEY]

    def cjpeg(self, input_filename, output_filename, quality, cjpeg_args=()):
        cjpeg_args = ["-sample", "1x1"] + list(cjpeg_args)
        return super().cjpeg(input_filename, output_filename, quality, cjpeg_args)

    def dcraw_cjpeg(self, input_filename, output_filename, quality, dcraw_args=(), cjpeg_args=()):
        cjpeg_args = ["-sample", "1x1"] + list(cjpeg_args)
        return super().dcraw_cjpeg(input_filename, output_filename, quality, dcraw_args, cjpeg_args)

    def djpeg_cjpeg(self, input_filename, output_filename, quality, djpeg_args=(), cjpeg_args=()):
        cjpeg_args= ["sample", "1x1"] + list(cjpeg_args)
        return super().djpeg_cjpeg(input_filename, output_filename, quality, djpeg_args, cjpeg_args)

    def dcraw_convert_cjpeg(self, input_filename, output_filename, quality, dcraw_args=(), cjpeg_args=()):
        cjpeg_args = ["-sample", "1x1"] + list(cjpeg_args)
        return super().dcraw_convert_cjpeg(input_filename, output_filename, quality, dcraw_args, cjpeg_args)
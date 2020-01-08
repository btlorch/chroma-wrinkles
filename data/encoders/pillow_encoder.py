from data.encoders.encoder import Encoder
from utils.constants import PILLOW
from PIL import Image
import tempfile


class PillowEncoder(Encoder):
    def __init__(self):
        super().__init__()

    @classmethod
    def name(cls):
        return PILLOW

    def cjpeg_executable(self):
        raise ValueError("Not applicable")

    def djpeg_executable(self):
        raise ValueError("Not applicable")

    def dcraw_cjpeg(self, input_filename, output_filename, quality, dcraw_args=(), cjpeg_args=()):
        with tempfile.NamedTemporaryFile(suffix=".ppm") as ppm_file:
            self.dcraw(input_filename, ppm_file.name)

            img = Image.open(ppm_file.name)

            img.save(output_filename, quality=quality)

            return output_filename

from utils.constants import constants, DCRAW_EXECUTABLE_KEY
from utils.logger import setup_custom_logger
import numpy as np
import subprocess
import collections
import tempfile
import imageio
import abc
import os


log = setup_custom_logger(os.path.basename(__file__))


class Encoder(abc.ABC):
    def __init__(self):
        super().__init__()

    @property
    @abc.abstractmethod
    def cjpeg_executable(self):
        pass

    @property
    @abc.abstractmethod
    def djpeg_executable(self):
        pass

    @classmethod
    @abc.abstractmethod
    def name(cls):
        pass

    @staticmethod
    def _is_tuple_or_list(args):
        if isinstance(args, str):
            return False

        return isinstance(args, collections.abc.Sequence)

    def dcraw_cjpeg(self, input_filename, output_filename, quality, dcraw_args=(), cjpeg_args=()):
        """
        Converts a raw image to JPEG by piping the output of dcraw into cjpeg.
        :param input_filename: path to raw file
        :param output_filename: path to output JPEG file
        :param quality: JPEG quality for compression
        :param dcraw_args: list of additional command line arguments to dcraw
        :param cjpeg_args: list of additional command line arguments to cjpeg
        :return: output filename
        """
        # Ensure dcraw_args and cjpeg_args to be collections
        if not self._is_tuple_or_list(dcraw_args) or not self._is_tuple_or_list(cjpeg_args):
            raise ValueError("Additional arguments to dcraw and cjpeg must be a list or a tuple")

        # Convert to ppm first
        dcraw_command_line = [constants[DCRAW_EXECUTABLE_KEY], "-w", "-c", input_filename]
        if len(dcraw_args) > 0:
            # Insert at position 1
            dcraw_command_line[1:1] = list(dcraw_args)

        # Then save as jpeg file
        # Skip quality if qtables is set
        if "-qtables" not in cjpeg_args:
            cjpeg_command_line = [self.cjpeg_executable, "-quality", str(quality)]
        else:
            cjpeg_command_line = [self.cjpeg_executable]

        cjpeg_command_line = cjpeg_command_line + ["-outfile", output_filename]
        if len(cjpeg_args) > 0:
            # Insert at position 1
            cjpeg_command_line[1:1] = list(cjpeg_args)

        # Pipe output from dcraw directly into cjpeg. This relieves us from keeping track of temporary files.
        dcraw_process = subprocess.Popen(dcraw_command_line, stdout=subprocess.PIPE)
        cjpeg_process = subprocess.run(cjpeg_command_line, stdin=dcraw_process.stdout, stdout=subprocess.PIPE, check=True)

        # TODO report errors
        # djpeg_process.stdout.close()

        return output_filename

    def dcraw_convert_cjpeg(self, input_filename, output_filename, quality, dcraw_args=(), cjpeg_args=()):
        """
        Converts a raw image to JPEG by piping the output of dcraw into cjpeg, but swaps the R and B channels before JPEG compression.
        :param input_filename: path to raw file
        :param output_filename: path to output JPEG file
        :param quality: JPEG quality for compression
        :param dcraw_args: list of additional command line arguments to dcraw
        :param cjpeg_args: list of additional command line arguments to cjpeg
        :return: output filename
        """
        # Ensure dcraw_args and cjpeg_args to be collections
        if not self._is_tuple_or_list(dcraw_args) or not self._is_tuple_or_list(cjpeg_args):
            raise ValueError("Additional arguments to dcraw and cjpeg must be a list or a tuple")

        # Convert to ppm first
        dcraw_command_line = [constants[DCRAW_EXECUTABLE_KEY], "-w", "-c", input_filename]
        if len(dcraw_args) > 0:
            # Insert at position 1
            dcraw_command_line[1:1] = list(dcraw_args)

        # Swap color channels
        convert_command_line = ["convert", "ppm:-", "-separate", "+channel", "-swap", "0,2", "-combine", "-colorspace", "RGB", "ppm:-"]

        # Then save as jpeg file
        # Skip quality if qtables is set
        if "-qtables" not in cjpeg_args:
            cjpeg_command_line = [self.cjpeg_executable, "-quality", str(quality)]
        else:
            cjpeg_command_line = [self.cjpeg_executable]

        cjpeg_command_line = cjpeg_command_line + ["-outfile", output_filename]
        if len(cjpeg_args) > 0:
            # Insert at position 1
            cjpeg_command_line[1:1] = list(cjpeg_args)

        # Pipe output from dcraw directly into cjpeg. This relieves us from keeping track of temporary files.
        dcraw_process = subprocess.Popen(dcraw_command_line, stdout=subprocess.PIPE)
        convert_process = subprocess.Popen(convert_command_line, stdin=dcraw_process.stdout, stdout=subprocess.PIPE)
        dcraw_process.stdout.close()
        cjpeg_process = subprocess.run(cjpeg_command_line, stdin=convert_process.stdout, stdout=subprocess.PIPE, check=True)
        convert_process.stdout.close()

        # TODO report errors
        # djpeg_process.stdout.close()

        return output_filename

    def auto_cjpeg(self, input, output_filename, quality, cjpeg_args=()):
        """
        Chooses cjpeg method to use based on type of input
        :param input: ndarray or filename of raw or png file
        """
        if isinstance(input, np.ndarray):
            # Numpy array
            return self.img_cjpeg(input, output_filename, quality, cjpeg_args)

        if isinstance(input, str):
            ext = os.path.splitext(input)[1].lower()
            if ext in [".nef", ".dng"]:
                # Raw image
                return self.dcraw_cjpeg(input, output_filename, quality, cjpeg_args=cjpeg_args)
            elif ext == ".png":
                # Png image
                return self.png_cjpeg(input, output_filename, quality, cjpeg_args=cjpeg_args)

        raise ValueError("Unknown input format")

    def png_cjpeg(self, input_filename, output_filename, quality, cjpeg_args=()):
        """
        Converts an image to ppm format before compressing it to a jpeg image
        """
        with tempfile.NamedTemporaryFile(suffix=".ppm") as f:
            convert_command_line = ["convert", input_filename, f.name]
            convert_process = subprocess.run(convert_command_line, stdout=subprocess.PIPE, check=True)
            self.cjpeg(f.name, output_filename, quality, cjpeg_args)

    def img_cjpeg(self, img, output_filename, quality, cjpeg_args=()):
        """
        Saves a given ndarray as JPEG image
        :param img: ndarray
        :param output_filename: path to output JPEG file
        :param quality: JPEG quality factor
        :param cjpeg_args: additional command line arguments to pass on to cjpeg
        """
        with tempfile.NamedTemporaryFile(suffix=".ppm") as f:
            imageio.imwrite(f.name, img)

            self.cjpeg(f.name, output_filename, quality, cjpeg_args)

    def cjpeg(self, input_filename, output_filename, quality, cjpeg_args=()):
        # Ensure cjpeg_args to be collections
        if not self._is_tuple_or_list(cjpeg_args):
            raise ValueError("Additional arguments to cjpeg must be a list or a tuple")

        # Concatenate cjpeg command line
        # Skip quality if qtables is set
        if "-qtables" not in cjpeg_args:
            cjpeg_command_line = [self.cjpeg_executable, "-quality", str(quality)]
        else:
            cjpeg_command_line = [self.cjpeg_executable]

        cjpeg_command_line = cjpeg_command_line + ["-outfile", output_filename, input_filename]

        if len(cjpeg_args) > 0:
            # Insert at position 1
            cjpeg_command_line[1:1] = list(cjpeg_args)

        # Raise error if exit code is non-zero
        cjpeg_process = subprocess.run(cjpeg_command_line, stdout=subprocess.PIPE, check=True)

        return output_filename

    def djpeg(self, input_filename, output_filename, djpeg_args=()):
        # Ensure djpeg_args to be a collection
        if not self._is_tuple_or_list(djpeg_args):
            raise ValueError("Additional arguments to djpeg must be a list or tuple")

        # Concatenate djpeg command line
        djpeg_command_line = [self.djpeg_executable, "-outfile", output_filename, input_filename]

        if len(djpeg_args) > 0:
            # Insert at position 1
            djpeg_command_line[1:1] = list(djpeg_args)

        # Raise error if exit code is non-zero
        djpeg_process = subprocess.run(djpeg_command_line, stdout=subprocess.PIPE, check=True)

        return output_filename

    def djpeg_cjpeg(self, input_filename, output_filename, quality, djpeg_args=(), cjpeg_args=()):
        """
        Recompresses a given jpeg image
        :param input_filename: file path to image to be recompressed
        :param output_filename: file path where to store recompressed image
        :param quality: quality factor for cjpeg
        :param djpeg_args: tuple/list of additional arguments for djpeg command
        :param cjpeg_args: tuple/list of additional arguments for cjpeg
        :return: output raw_filename
        """
        # Ensure djpeg_args and cjpeg_args to be collections
        if not self._is_tuple_or_list(djpeg_args) or not self._is_tuple_or_list(cjpeg_args):
            raise ValueError("Additional arguments to djpeg and cjpeg must be a list or a tuple")

        # Djpeg command line
        djpeg_command_line = [self.djpeg_executable, input_filename]
        if len(djpeg_args) > 0:
            # Insert at position 1
            djpeg_command_line[1:1] = list(djpeg_args)

        # Skip quality if qtables is set
        if "-qtables" not in cjpeg_args:
            cjpeg_command_line = [self.cjpeg_executable, "-quality", str(quality)]
        else:
            cjpeg_command_line = [self.cjpeg_executable]

        cjpeg_command_line = cjpeg_command_line + ["-outfile", output_filename]

        if len(cjpeg_args) > 0:
            # Insert at position 1
            cjpeg_command_line[1:1] = list(cjpeg_args)

        # Pipe output from djpeg directly into cjpeg
        djpeg_process = subprocess.Popen(djpeg_command_line, stdout=subprocess.PIPE)
        cjpeg_process = subprocess.run(cjpeg_command_line, stdin=djpeg_process.stdout, stdout=subprocess.PIPE, check=True)

        return output_filename

    def dcraw(self, input_filename, output_filename, dcraw_args=()):
        """
        Converts a given raw image to an uncompressed ppm file
        :param input_filename: path to raw image
        :param output_filename: where to store output as ppm file
        :param dcraw_args: additional arguments passed to dcraw
        :return: output filename
        """
        assert os.path.splitext(output_filename)[1] == ".ppm", "Only ppm output supported"
        # Convert to ppm
        dcraw_command_line = [constants[DCRAW_EXECUTABLE_KEY], "-w", "-c", input_filename]
        if len(dcraw_args) > 0:
            # Insert at position 1
            dcraw_command_line[1:1] = list(dcraw_args)

        with open(output_filename, "wb") as f:
            dcraw_process = subprocess.run(dcraw_command_line, stdout=f, check=True)

        # TODO Check for errors

        return output_filename

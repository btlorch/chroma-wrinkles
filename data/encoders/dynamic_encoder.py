from data.encoders.encoder import Encoder


class DynamicEncoder(Encoder):
    def __init__(self, cjpeg_executable, djpeg_executable, name):
        """
        Allows to define the binding to the respective libjpeg derivate at object construction time.
        Uses cjpeg and djpeg default parameters.
        :param cjpeg_executable: Path to cjpeg executable
        :param djpeg_executable: Path to djpeg executable
        """
        super().__init__()
        self._cjpeg_executable = cjpeg_executable
        self._djpeg_executable = djpeg_executable
        self._name = name

    def name(self):
        return self._name

    @property
    def cjpeg_executable(self):
        return self._cjpeg_executable

    @property
    def djpeg_executable(self):
        return self._djpeg_executable

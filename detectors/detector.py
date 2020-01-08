import abc


class Detector(abc.ABC):
    @abc.abstractmethod
    def detect_map(self, channel):
        """
        Computes a probability for each pixel that it matches the model that the specific detector expects.
        :param channel: input image. The exact format depends on the specific detector.
        :return: Probability for each pixel in the given input that it matches the model.
        """
        pass

    @abc.abstractmethod
    def detect_score(self, channel):
        """
        Computes a scalar score for how strong the specific detector's model matches to the given input data.
        :param channel: input image. The exact format depends on the specific detector.
        :return: Scalar score
        """
        pass

import numpy

import chainer
from chainer.backends import cuda
from chainer.functions.loss import negative_sampling
from chainer import link
from chainer.utils import walker_alias
from chainer import variable


class NegativeSampling(link.Link):

    """Negative sampling loss layer.

    This link wraps the :func:`~chainer.functions.negative_sampling` function.
    It holds the weight matrix as a parameter. It also builds a sampler
    internally given a list of word counts.

    Args:
        in_size (int): Dimension of input vectors.
        counts (int list): Number of each identifiers.
        sample_size (int): Number of negative samples.
        power (float): Power factor :math:`\\alpha`.
        dtype (numpy.dtype): Type to use in computing.

    .. seealso:: :func:`~chainer.functions.negative_sampling` for more detail.

    Attributes:
        W (~chainer.Variable): Weight parameter matrix.

    """

    def __init__(self, in_size, counts, sample_size, power=0.75, dtype=None):
        super(NegativeSampling, self).__init__()
        dtype = chainer.get_dtype(dtype)
        vocab_size = len(counts)
        self.sample_size = sample_size
        power = dtype.type(power)
        p = numpy.array(counts, dtype)
        numpy.power(p, power, p)
        self.sampler = walker_alias.WalkerAlias(p)

        with self.init_scope():
            self.W = variable.Parameter(0, (vocab_size, in_size))

    def to_cpu(self):
        super(NegativeSampling, self).to_cpu()
        self.sampler.to_cpu()
        return self

    def to_gpu(self, device=None):
        with cuda._get_device(device):
            super(NegativeSampling, self).to_gpu()
            self.sampler.to_gpu()
        return self

    def forward(self, x, t, reduce='sum'):
        """Computes the loss value for given input and ground truth labels.

        Args:
            x (~chainer.Variable): Input of the weight matrix multiplication.
            t (~chainer.Variable): Batch of ground truth labels.
            reduce (str): Reduction option. Its value must be either
                ``'sum'`` or ``'no'``. Otherwise, :class:`ValueError` is
                raised.

        Returns:
            ~chainer.Variable: Loss value.

        """
        return negative_sampling.negative_sampling(
            x, t, self.W, self.sampler.sample, self.sample_size,
            reduce=reduce)

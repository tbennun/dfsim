"""
Computes ``y = a*x + y`` with global memory.
"""

import numpy as np

from dfsim import ProcessingElement, Processor


# Define the processing elements
class Multiplier(ProcessingElement):
    multiplied: bool  #: Has this processing element finished the multiplication?

    def __init__(self):
        self.multiplied = False


# Define a 100x1 spatial processor with one communication plane
SIZE = 100
sim = Processor(SIZE, 1, default_memory=Multiplier())

#################################################
# Define global memory

a = np.random.rand()
x = np.random.rand(SIZE)
y = np.random.rand(SIZE)

#################################################
# Define message handlers


# Make a processing element based on its index (the extra function avoids a
# Python issue, creating a unique closure where ``i`` corresponds to the PE ID)
def make_pe(i: int):
    @sim.register_handler(i, 0)
    def multiply(self: Multiplier, _):
        if self.multiplied:
            return

        y[i] += a * x[i]

        self.multiplied = True


for i in range(SIZE):
    make_pe(i)

#################################################
# (no routes necessary)

if __name__ == '__main__':
    expected = a * x + y

    sim.simulate(time_steps=1)

    assert np.allclose(expected, y)

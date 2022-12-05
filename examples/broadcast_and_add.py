"""
A simple example that broadcasts over a column, adding one to each element along the way.
"""

import numpy as np
from typing import Optional

from dfsim import Direction, ProcessingElement, Processor


# Define the processing elements
class MyPE(ProcessingElement):
    def __init__(self):
        self.val = np.zeros(1, np.int32)


# Define a 4x4 spatial processor with one communication channel
sim = Processor(4, 4, default_memory=MyPE())

#################################################
# Define message handlers


# Instigator
@sim.register_handler(proc_i=0, proc_j=0, channel=0)
def instigate(self: MyPE, _):
    if self.val == 0:  # Only send once
        self.val[:] = 42
        return 42  # Send 42 along route


# Receiver
for i in range(1, 3):

    @sim.register_handler(i, 0, 0)
    def get_and_send(self: MyPE, message: Optional[int]):
        if message is not None:
            self.val[:] = message + 1
            return self.val[0]


# Store handler
@sim.register_handler(proc_i=3, proc_j=0, channel=0)
def store(self: MyPE, message: Optional[int]):
    if message is not None:
        self.val[:] = message + 1


#################################################
# Define routes

# 0->1->2->3
sim.route(0, 0, 0, Direction.PROCESSOR, Direction.SOUTH)
for i in range(1, 3):
    sim.route(i, 0, 0, Direction.NORTH, Direction.PROCESSOR)
    sim.route(i, 0, 0, Direction.PROCESSOR, Direction.SOUTH)
sim.route(3, 0, 0, Direction.NORTH, Direction.PROCESSOR)

if __name__ == '__main__':
    sim.simulate(time_steps=10)

    print(f'Final memory:')
    for i in range(sim.rows):
        for j in range(sim.cols):
            print(sim[i, j].memory.val[0], end=' ')
        print()

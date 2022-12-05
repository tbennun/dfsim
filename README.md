# DFSim

DFSim is a simplified 2D grid dataflow processor simulator.
The processors it simulates contain processing elements that contain their own memory and can perform immediate neighborhood communication.

It is an event-driven simulator written in Python and allows you to register message handlers that will run perpetually on the processor.
If no message was received, the handler will still be called but with a `None` argument for the message.

For communication, you can specify routes via the `route` method on multiple concurrent communication channels in order
to reduce congestion (similarly to Virtual Channels in NoCs or Communicators in MPI).

## Example use

You can use DFSim to prototype spatial programs easily. For example, a simple column broadcast:

```python
import numpy as np
from typing import Optional

from dfsim import Direction, ProcessingElement, Processor

# Define the processing elements
class MyPE(ProcessingElement):
    def __init__(self):
        self.val = np.zeros(1, np.int32)

# Define a 4x4 spatial processor with one communication channel
sim = Processor(4, 4, 1, default_memory=MyPE())

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
            self.val[:] = message
            return message  # Forward

# Store handler
@sim.register_handler(proc_i=3, proc_j=0, channel=0)
def store(self: MyPE, message: Optional[int]):
    if message is not None:
        self.val[:] = message

#################################################
# Define routes
sim.route(0, 0, 0, Direction.PROCESSOR, Direction.SOUTH)
for i in range(1, 3):
    sim.route(i, 0, 0, Direction.NORTH, Direction.PROCESSOR)
    sim.route(i, 0, 0, Direction.PROCESSOR, Direction.SOUTH)
sim.route(3, 0, 0, Direction.NORTH, Direction.PROCESSOR)
```

Then, the simulator can be invoked as:
```python
sim.simulate(time_steps=10)
```

You can access the individual PEs to print the result:
```python
print(f'Final memory:')
for i in range(sim.rows):
    for j in range(sim.cols):
        print(sim[i, j].memory.val[0], end=' ')
    print()
```

## License and contributing

The project is published under the New BSD license. This is a community project - feel free to make any contributions in pull requests!

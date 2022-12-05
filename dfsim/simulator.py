"""
2D grid spatial architecture simulator with neighbor communication and multiple
communication channels.
"""
import copy
from enum import Enum, auto
from typing import Any, Dict, List, Callable, Optional, Tuple

######################################

# The type of a message in the simulator
MessageType = Any


class ProcessingElement:
    """
    A processing element in the grid. Extend this class to implement your own
    processing element memory and methods.
    """
    pass


# A handler for a processor receives the processing element and the message,
# and may return a response message.
HandlerType = Callable[[ProcessingElement, Optional[MessageType]],
                       Optional[MessageType]]


class Direction(Enum):
    """
    Directionality of a message route.
    """
    NORTH = auto()
    SOUTH = auto()
    EAST = auto()
    WEST = auto()
    PROCESSOR = auto()  #: Message going into or out of the processor
    NOTHING = auto()  #: No message


class PE:
    """
    Internal class that manages a processor's processing element, including
    its location, routes, and communication. Access memory via the
    ``ProcessingElement`` class.
    """
    memory: ProcessingElement
    inbound_routes: List[Direction]
    outbound_routes: List[Direction]
    skip_routes: List[Tuple[Direction, Direction]]
    queues: List[List[Any]]
    handlers: List[List[HandlerType]]
    i: int
    j: int
    parent: 'Processor'

    def __init__(self, i: int, j: int, parent: 'Processor'):
        self.memory = None
        self.inbound_routes = [
            Direction.NOTHING for _ in range(parent.channels)
        ]
        self.outbound_routes = [
            Direction.NOTHING for _ in range(parent.channels)
        ]
        self.skip_routes = [(Direction.NOTHING, Direction.NOTHING)
                            for _ in range(parent.channels)]
        self.handlers = [[] for _ in range(parent.channels)]
        self.queues = [[] for _ in range(parent.channels)]
        self.i = i
        self.j = j
        self.parent = parent

    def set_memory(self, memory: ProcessingElement):
        """
        Sets the memory of this processing element to the given object.
        """
        self.memory = memory

    def register_handler(self, channel: int, handler: HandlerType):
        """
        Registers a message handler to this processing element on the given channel.
        """
        self.handlers[channel].append(handler)

    def run_channels(self):
        """
        Simulates all channels w.r.t. communication and execution.
        """
        for p in range(self.parent.channels):
            tosend = None
            element = None
            if self.queues[p]:
                element = self.queues[p].pop(0)

                # Take care of skip routes
                if self.skip_routes[p][0] != Direction.NOTHING:
                    self.send(element, self.skip_routes[p][1], p)

            # Take care of handlers
            for handler in self.handlers[p]:
                # Only one send per channel, so result may be overridden
                tosend = handler(self.memory, element)

            # Take care of outbound routes
            if (tosend is not None
                    and self.outbound_routes[p] != Direction.NOTHING):
                self.send(tosend, self.outbound_routes[p], p)

    def send(self, element: Any, direction: Direction, channel: int):
        """
        Internal function that sends a message according to the route directionality.
        """
        if direction == Direction.NORTH:
            self.parent[self.i - 1, self.j].queues[channel].append(element)
        elif direction == Direction.SOUTH:
            self.parent[self.i + 1, self.j].queues[channel].append(element)
        elif direction == Direction.EAST:
            self.parent[self.i, self.j + 1].queues[channel].append(element)
        elif direction == Direction.WEST:
            self.parent[self.i, self.j - 1].queues[channel].append(element)
        elif direction == Direction.PROCESSOR:
            self.queues[channel].append(element)


class Processor:
    """
    A simulated dataflow architecture processor.
    It is a 2D-grid spatial architecture with neighbor communication and
    multiple concurrent communication routes (channels).
    """
    rows: int
    cols: int
    channels: int
    pes: List[PE]

    def __init__(self,
                 rows: int,
                 cols: int,
                 channels: int = 1,
                 default_memory: Optional[ProcessingElement] = None):
        """
        Initializes a simulated processor.

        :param rows: The number of rows in the processing element grid.
        :param cols: The number of columns in the processing element grid.
        :param channels: The number of concurrent communication routes that can
                       be set.
        :param default_memory: The default processing element class (if not
                               None, the given object will be replicated
                               for the entire grid).
        """
        self.rows = rows
        self.cols = cols
        self.channels = channels
        self.pes = [
            PE(ind // cols, ind % cols, self) for ind in range(rows * cols)
        ]
        if default_memory is not None:
            for pe in self.pes:
                pe.set_memory(copy.deepcopy(default_memory))

    def __getitem__(self, tup) -> PE:
        """
        Returns the processing element at the given index.
        """
        i, j = tup
        if i < 0 or i >= self.rows or j < 0 or j >= self.cols:
            raise IndexError
        return self.pes[i * self.cols + j]

    def register_handler(self, proc_i: int, proc_j: int, channel: int = 0):
        """
        A decorator that can be used to register perpetually-executed handlers
        for each processor.
        
        The handler receives two parameters: processing element and optional
        message. If no message is received in this time-step, the message
        parameter will be set to ``None``. The handler can also send a message
        in this time-step by returning a value. Note that only one message
        can be sent per channel, so the last handler will override previous
        return values.

        Example use::

            @proc.register_handler(0, 0)
            def print_received_message(self, message):
              if message is not None:
                print('Received message:', message)

        :param proc_i: Processing element row.
        :param proc_j: Processing element column.
        :param channel: Communication channel.
        """
        def decorator(func: HandlerType):
            self[proc_i, proc_j].register_handler(channel, func)
            return func

        return decorator

    def route(self, proc_i: int, proc_j: int, channel: int, rcv: Direction,
              snd: Direction):
        """
        Creates a new route in the spatial processor.

        :note: This function will override an existing route if called with
               the same processing element index and channel.
        :param proc_i: Processing element row.
        :param proc_j: Processing element column.
        :param channel: Communication channel.
        :param rcv: Receiving direction.
        :param snd: Sending direction.
        """
        if snd == Direction.PROCESSOR:
            self[proc_i, proc_j].inbound_routes[channel] = rcv
        elif rcv == Direction.PROCESSOR:
            self[proc_i, proc_j].outbound_routes[channel] = snd
        else:
            self[proc_i, proc_j].skip_routes[channel] = (rcv, snd)

    def simulate(self, time_steps: int):
        """
        Simulate the dataflow architecture for the given number of time steps.
        In each step, messages are received across all channels, handlers are
        executed, and new messages are sent.

        :param time_steps: The number of time steps to simulate.
        :note: This function can be called multiple times in order to inspect
               the processor between steps.
        """
        for _ in range(time_steps):
            # This can probably run in parallel
            for i in range(self.rows):
                for j in range(self.cols):
                    self[i, j].run_channels()

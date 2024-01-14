import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.queue import QueueEmpty, Queue
from cocotb.clock import Clock
import logging
import enum
import pyuvm


# Logger setup
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# AES mode enum
@enum.unique
class Mode(enum.IntEnum):
    Encrypt = 0
    Decrypt = 1


# VAI BFM with queues for
class VaiBfm(metaclass=pyuvm.Singleton):
    """Valid-Accept Bfm"""

    def __init__(self):
        self.log = logging.getLogger()
        self.log.info("Valid-accept BFM")
        self.log.info("  Copyright (c) 2024 Torsten Meissner")
        self.dut = cocotb.top
        self.driver_queue = Queue(maxsize=1)
        self.in_monitor_queue = Queue(maxsize=0)
        self.out_monitor_queue = Queue(maxsize=0)
        self.clock = Clock(
            self.dut.clk_i, 10, units="ns"
        )  # Create a 10 ns period clock
        cocotb.start_soon(self.clock.start())

    # Reset coroutine
    async def reset(self):
        self.dut.reset_i.value = 0
        self.dut.valid_i.value = 0
        self.dut.mode_i.value = 0
        self.dut.key_i.value = 0
        self.dut.data_i.value = 0
        self.dut.accept_i.value = 0
        await Timer(100, units="ns")
        self.dut.reset_i.value = 1

    # VAI input driver
    async def __driver(self):
        self.dut.valid_i.value = 0
        self.dut.key_i.value = 0
        self.dut.data_i.value = 0
        while True:
            await RisingEdge(self.dut.clk_i)
            if not self.dut.valid_i.value:
                try:
                    (mode, key, data) = self.driver_queue.get_nowait()
                    self.dut.mode_i.value = mode
                    self.dut.key_i.value = key
                    self.dut.data_i.value = data
                    self.dut.valid_i.value = 1
                except QueueEmpty:
                    continue
            else:
                if self.dut.accept_o.value:
                    self.dut.valid_i.value = 0

    # VAI output receiver
    # We ignore data out, we use the output monitor instead
    async def __receiver(self):
        self.dut.accept_i.value = 0
        while True:
            await RisingEdge(self.dut.clk_i)
            if self.dut.valid_o.value and not self.dut.accept_i.value:
                self.dut.accept_i.value = 1
            else:
                self.dut.accept_i.value = 0

    # VAI input monitor
    async def __in_monitor(self):
        while True:
            await RisingEdge(self.dut.clk_i)
            if self.dut.valid_i.value and self.dut.accept_o.value:
                in_tuple = (
                    self.dut.mode_i.value,
                    self.dut.key_i.value,
                    self.dut.data_i.value,
                )
                self.in_monitor_queue.put_nowait(in_tuple)

    # VAI output monitor
    async def __out_monitor(self):
        while True:
            await RisingEdge(self.dut.clk_i)
            if self.dut.valid_o.value and self.dut.accept_i.value:
                out_data = self.dut.data_o.value
                self.out_monitor_queue.put_nowait(out_data)

    # Launching the coroutines using start_soon
    def start_tasks(self):
        cocotb.start_soon(self.__driver())
        cocotb.start_soon(self.__receiver())
        cocotb.start_soon(self.__in_monitor())
        cocotb.start_soon(self.__out_monitor())

    # The get_input() coroutine returns the next VAI input
    async def get_input(self):
        data = await self.in_monitor_queue.get()
        return data

    # The get_output() coroutine returns the next VAI output
    async def get_output(self):
        data = await self.out_monitor_queue.get()
        return data

    # send_op puts the VAI input operation into the driver queue
    async def send_op(self, mode, key, data):
        await self.driver_queue.put((mode, key, data))

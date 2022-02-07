import logging
from cocotb.triggers import FallingEdge, RisingEdge, Timer, ReadOnly


class Uart:
    """UART base class"""

    def __init__(self, txrx, clock, div, bits, parity, *args, **kwargs):
        self._version = "0.0.1"

        self.log = logging.getLogger(f"cocotb.{txrx._path}")

        self._txrx = txrx
        self._clock = clock
        self._div = div
        self._bits = bits
        self._par = parity

        self._clkedge = RisingEdge(self._clock)

    async def _wait_cycle(self):
        for x in range(self._div):
            await self._clkedge

    @staticmethod
    def odd_parity(data):
        parity = True
        while data:
            parity = not parity
            data = data & (data - 1)
        return int(parity)


class UartReceiver(Uart):

    def __init__(self, txrx, clock, div, bits, parity, *args, **kwargs):
        super().__init__(txrx, clock, div, bits, parity, *args, **kwargs)

        self.log.info("UART receiver")
        self.log.info("  cocotbext-uart version %s", self._version)
        self.log.info("  Copyright (c) 2022 Torsten Meissner")

    async def receive(self):
        """Receive and return one UART frame"""

        # Wait for frame start
        await FallingEdge(self._txrx)

        # Consume start bit
        await self._get_start_bit()

        # Receive data bits
        self._rec = 0
        for x in range(self._bits):
            await self._wait_cycle()
            await ReadOnly()
            self._rec |= bool(self._txrx.value.integer) << x

        if self._par:
            # Consume parity bit
            await self._get_parity_bit()

        # Consume stop bit
        await self._get_stop_bit()

        self.log.info("Received data: %s", hex(self._rec))
        return self._rec

    async def _get_start_bit(self):
        """Consume and check start bit"""
        for x in range(int(self._div/2)):
            await self._clkedge
        await ReadOnly()
        if self._txrx.value == 1:
            self.log.warning("Start bit set")

    async def _get_stop_bit(self):
        """Consume and check stop bit"""
        await self._wait_cycle()
        await ReadOnly()
        if self._txrx.value == 0:
            self.log.warning("Stop bit not set")

    async def _get_parity_bit(self):
        """Consume and check parity bit"""
        await self._wait_cycle()
        await ReadOnly()
        if self.odd_parity(self._rec) != self._txrx.value:
            self.log.warning("Parity wrong")


class UartDriver(Uart):

    def __init__(self, txrx, clock, div, bits, parity, *args, **kwargs):
        super().__init__(txrx, clock, div, bits, parity, *args, **kwargs)

        self.log.info("UART sender")
        self.log.info("  cocotbext-uart version %s", self._version)
        self.log.info("  Copyright (c) 2022 Torsten Meissner")

        # Drive input defaults (setimmediatevalue to avoid x asserts)
        self._txrx.setimmediatevalue(1)

    async def send(self, data):
        """Send one UART frame"""

        self._data = data;

        self.log.info("Sending data:  %s", hex(self._data))

        # Send start bit
        await self._send_bit(0)

        # Send data bits
        for x in range(self._bits):
            self._txrx.value = (self._data >> x) & 1
            await self._wait_cycle()


        if self._par:
            # Send parity bit
            await self._send_bit(self.odd_parity(self._data))

        # Consume stop bit
        await self._send_bit(1)

    async def _send_bit(self, data):
        self._txrx.value = data
        await self._wait_cycle()


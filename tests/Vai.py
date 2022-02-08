import logging
from cocotb.triggers import FallingEdge, RisingEdge, Timer, ReadOnly


class Vai:
    """VAI base class"""

    def __init__(self, clock, data, valid, accept, *args, **kwargs):
        self._version = "0.0.1"

        self.log = logging.getLogger(f"cocotb.{valid._path}")

        self._data = data
        self._valid = valid
        self._accept = accept
        self._clock = clock

        self._clkedge = RisingEdge(self._clock)


class VaiDriver(Vai):
    """Valid-Accept Driver"""

    def __init__(self, clock, data, valid, accept, *args, **kwargs):
        super().__init__(clock, data, valid, accept, *args, **kwargs)

        self.log.info("Valid-accept driver")
        self.log.info("  cocotbext-vai version %s", self._version)
        self.log.info("  Copyright (c) 2022 Torsten Meissner")

        # Hack to drive lists of signals
        if isinstance(self._data, list):
            for entry in self._data:
                entry.setimmediatevalue(0)
        else:
            self._data.setimmediatevalue(0)
        self._valid.setimmediatevalue(0)

    async def send(self, data, sync=True):
        if sync:
            await self._clkedge

        self._valid.value = 1
        # Hack to drive lists of signals
        if isinstance(self._data, list):
            for i in range(len(self._data)):
                self._data[i].value = data[i]
        else:
            self.log.info("Sending data:  %s", hex(data))
            self._data.value = data

        while True:
            await ReadOnly()
            if self._accept.value:
                break
            await self._clkedge
        await self._clkedge

        self._valid.value = 0



class VaiReceiver(Vai):
    """Valid-Accept Receiver"""

    def __init__(self, clock, data, valid, accept, *args, **kwargs):
        super().__init__(clock, data, valid, accept, *args, **kwargs)

        self.log.info("Valid-accept receiver")
        self.log.info("  cocotbext-vai version %s", self._version)
        self.log.info("  Copyright (c) 2022 Torsten Meissner")

        # Drive input defaults (setimmediatevalue to avoid x asserts)
        self._accept.setimmediatevalue(0)

    async def receive(self, sync=True):
        if sync:
            await self._clkedge

        while True:
            await ReadOnly()
            if self._valid.value:
                break
            await self._clkedge
        
        await self._clkedge
        self._accept.value = 1
        _rec = self._data.value
        self.log.info("Received data: %s", hex(_rec))

        await self._clkedge
        self._accept.value = 0

        return _rec

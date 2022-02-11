import logging
import cocotb
from cocotb.utils import get_sim_time
from cocotb.triggers import FallingEdge, RisingEdge, Timer


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

        if isinstance(self._data, list):
            _info = ', '.join(map(lambda x: str(hex(x)), data))
            for i in range(len(self._data)):
                self._data[i].value = data[i]

        else:
            self._data.value = data
            _info = hex(data)

        self.log.info(f"Send data:    {_info}")

        while True:
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
            if self._valid.value:
                break
            await self._clkedge
        
        await self._clkedge
        self._accept.value = 1
        _rec = self._data.value
        self.log.info(f"Receive data: {hex(_rec)}")

        await self._clkedge
        self._accept.value = 0

        return _rec


class VaiMonitor(Vai):
    """Valid-Accept Receiver"""

    def __init__(self, clock, data, valid, accept, queue=None, *args, **kwargs):
        super().__init__(clock, data, valid, accept, *args, **kwargs)

        self.log.info("Valid-accept monitor")
        self.log.info("  cocotbext-vai version %s", self._version)
        self.log.info("  Copyright (c) 2022 Torsten Meissner")

        self._active = None
        self._queue = queue
        self._transactions = {}
        self._restart()

    def _restart(self):
        self.log.debug("SramMonitor._restart()")
        if self._active is not None:
            self._active.kill()
        # Schedule VAI read to run concurrently
        self._active = cocotb.start_soon(self._read())

    async def _read(self, cb=None):
        while True:
            await self._clkedge
            if self._valid.value and self._accept.value:
                if self._queue:
                    await self._queue.put(self._data)
                #self._transactions[str(get_sim_time('ns'))] = {
                #    "data" : self._data.value}


    @property
    def transactions(self, index=None):
        if index:
            key = list(self._transactions.keys())[index]
            return {key: self._transactions[key]}
        else:
            return self._transactions

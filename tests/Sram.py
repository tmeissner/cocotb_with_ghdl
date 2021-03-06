import logging
import cocotb
from cocotb.utils import get_sim_time
from cocotb.triggers import FallingEdge, RisingEdge, Timer


class Sram:

    def __init__(self, clk, wen, ren, adr, din, dout, mem, *args, **kwargs):
        self._version = "0.0.1"

        self.log = logging.getLogger(f"cocotb.{clk._path}")

        self._clk = clk
        self._wen = wen
        self._ren = ren
        self._adr = adr
        self._din = din
        self._dout = dout
        self._mem = mem

        self._clkedge = RisingEdge(self._clk)


class SramRead(Sram):

    def __init__(self, clk, ren, adr, din, mem, *args, **kwargs):
        super().__init__(clk, None, ren, adr, din, None, mem, *args, **kwargs)
    
        self.log.info("SRAM read")
        self.log.info("  cocotbext-sram version %s", self._version)
        self.log.info("  Copyright (c) 2022 Torsten Meissner")
    
        self._active = None
        self._restart()

    def _restart(self):
        self.log.debug("SramRead._restart()")
        if self._active is not None:
            self._active.kill()
        # Schedule SRAM read to run concurrently
        self._active = cocotb.start_soon(self._read())

    async def _read(self):
        self.log.debug("SramRead._read()")
        while True:
            await self._clkedge
            if self._ren.value == 1:
                _data = self._mem[str(self._adr.value)]
                self._din.value = _data
                self.log.info(f"Read data:  {hex(_data)} from adr: {hex(self._adr.value)}")


class SramWrite(Sram):

    def __init__(self, clk, wen, adr, dout, mem, *args, **kwargs):
        super().__init__(clk, wen, None, adr, None, dout, mem, *args, **kwargs)
    
        self.log.info("SRAM write")
        self.log.info("  cocotbext-sram version %s", self._version)
        self.log.info("  Copyright (c) 2022 Torsten Meissner")
    
        self._active = None
        self._restart()

    def _restart(self):
        self.log.debug("SramWrite._restart()")
        if self._active is not None:
            self._active.kill()
        # Schedule SRAM write to run concurrently
        self._active = cocotb.start_soon(self._write())

    async def _write(self):
        self.log.debug("SramWrite._write()")
        while True:
            await self._clkedge
            if self._wen.value == 1:
                self._mem[str(self._adr.value)] = self._dout.value
                self.log.info(f"Wrote data: {hex(self._dout.value)} to adr:   {hex(self._adr.value)}")


class SramMonitor(Sram):

    def __init__(self, clk, wen, ren, adr, din, dout, *args, **kwargs):
        super().__init__(clk, wen, ren, adr, din, dout, None, *args, **kwargs)
    
        self.log.info("SRAM monitor")
        self.log.info("  cocotbext-sram version %s", self._version)
        self.log.info("  Copyright (c) 2022 Torsten Meissner")
    
        self._active = None
        self._transactions = {}
        self._restart()

    def _restart(self):
        self.log.debug("SramMonitor._restart()")
        if self._active is not None:
            self._active.kill()
        # Schedule SRAM read to run concurrently
        self._active = cocotb.start_soon(self._read())

    async def _read(self):
        self.log.debug("SramMonitor._read()")
        while True:
            await self._clkedge
            if self._wen.value:
                self._transactions[str(get_sim_time('ns'))] = {
                    "type" : "write",
                    "adr"  : self._adr.value,
                    "data" : self._dout.value}
            elif self._ren.value:
                _adr = self._adr.value
                await self._clkedge
                self._transactions[str(get_sim_time('ns'))] = {
                    "type" : "read",
                    "adr"  : _adr,
                    "data" : self._din.value}

    @property
    def transactions(self, index=None):
        if index:
            key = list(self._transactions.keys())[index]
            return {key: self._transactions[key]}
        else:
            return self._transactions

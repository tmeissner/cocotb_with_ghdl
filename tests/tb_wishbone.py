# test_uart.py

import logging
import random
import cocotb
import pprint
from collections import defaultdict
from Sram import SramRead, SramWrite, SramMonitor
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer, ReadOnly
from cocotbext.wishbone.driver import WishboneMaster, WBOp


# Reset coroutine
async def reset_dut(reset_n, duration_ns):
    reset_n.value = 1
    await Timer(duration_ns, units="ns")
    reset_n.value = 0


@cocotb.test()
async def test_wishbone(dut):
    """ First simple test """

    clkedge = RisingEdge(dut.wbclk_i)

    # Connect reset
    reset = dut.wbrst_i


    # Create empty SRAM memory
    memory = defaultdict()

    mem_read = SramRead(dut.wbclk_i, dut.localren_o,
        dut.localadress_o, dut.localdata_i, memory);
    mem_write = SramWrite(dut.wbclk_i, dut.localwen_o,
        dut.localadress_o, dut.localdata_o, memory);
    sram_monitor = SramMonitor(dut.wbclk_i, dut.localwen_o, dut.localren_o,
        dut.localadress_o, dut.localdata_i, dut.localdata_o);

    wbmaster = WishboneMaster(dut, "", dut.wbclk_i,
        width=16,   # size of data bus
        timeout=10, # in clock cycle number
        signals_dict={"cyc":  "wbcyc_i",
                      "stb":  "wbstb_i",
                      "we":   "wbwe_i",
                      "adr":  "wbadr_i",
                      "datwr":"wbdat_i",
                      "datrd":"wbdat_o",
                      "ack":  "wback_o" })

    # Drive input defaults (setimmediatevalue to avoid x asserts)
    dut.wbcyc_i.setimmediatevalue(0)
    dut.wbstb_i.setimmediatevalue(0)
    dut.wbwe_i.setimmediatevalue(0)
    dut.wbadr_i.setimmediatevalue(0)
    dut.wbdat_i.setimmediatevalue(0)

    clock = Clock(dut.wbclk_i, 10, units="ns")  # Create a 10 ns period clock
    cocotb.start_soon(clock.start())  # Start the clock

    # Execution will block until reset_dut has completed
    dut._log.info("Hold reset")
    await reset_dut(reset, 100)
    dut._log.info("Released reset")

    # Test 10 Wishbone transmissions
    for i in range(10):
        await clkedge
        adr = random.randint(0, 255)
        data = random.randint(0, 2**16-1)
        await wbmaster.send_cycle([WBOp(adr=adr, dat=data)])
        rec = await wbmaster.send_cycle([WBOp(adr=adr)])

    # Example to print transactions collected by SRAM monitor
    with open('results/sram_transactions.log', 'w', encoding='utf-8') as f:
        f.write((f"{'Time':7}{'Type':7}{'Adr':11}{'Data'}\n"))
        for k, v in sram_monitor.transactions.items():
            f.write((f"{k:7}{v['type']:7}{v['adr']:11}{v['data']} \n"))
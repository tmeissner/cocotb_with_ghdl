# test_uart.py

import logging
import random
import cocotb
import wavedrom
from Uart import UartDriver, UartReceiver
from Vai import VaiDriver, VaiReceiver
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer, ReadOnly
from cocotb.wavedrom import Wavedrom, trace



# Reset coroutine
async def reset_dut(reset_n, duration_ns):
    reset_n.value = 0
    await Timer(duration_ns, units="ns")
    reset_n.value = 1


def wave2svg(wave, file):
    svg = wavedrom.render(wave)
    svg.saveas(file)


@cocotb.test()
async def test_uarttx(dut):
    """ First simple test """

    clkedge = RisingEdge(dut.clk_i)

    # Connect reset
    reset_n = dut.reset_n_i

    # Instantiate VAI driver
    vai_driver = VaiDriver(dut.clk_i, dut.data_i, dut.valid_i, dut.accept_o)
    # Instantiate UART receiver
    uart_receiver = UartReceiver(dut.tx_o, dut.clk_i, 10, 8, True);

    # Drive input defaults (setimmediatevalue to avoid x asserts)
    dut.data_i.setimmediatevalue(0)
    dut.valid_i.setimmediatevalue(0)

    clock = Clock(dut.clk_i, 10, units="ns")  # Create a 10 ns period clock
    cocotb.start_soon(clock.start())  # Start the clock

    # Execution will block until reset_dut has completed
    dut._log.info("Hold reset")
    await reset_dut(reset_n, 100)
    dut._log.info("Released reset")

    # Test 10 UART transmissions
    for i in range(10):
        await clkedge
        val = random.randint(0, 255)
        await vai_driver.send(val)
        rec = await uart_receiver.receive();
        assert rec == val, "UART sent data was incorrect on the {}th cycle".format(i)


@cocotb.test()
async def test_uartrx(dut):
    """ First simple test """

    clkedge = RisingEdge(dut.clk_i)

    # Connect reset
    reset_n = dut.reset_n_i

    # Instantiate UART driver
    uart_driver = UartDriver(dut.rx_i, dut.clk_i, 10, 8, True);
    # Instantiate VAI receiver
    vai_receiver = VaiReceiver(dut.clk_i, dut.data_o, dut.valid_o, dut.accept_i)

    # Drive input defaults (setimmediatevalue to avoid x asserts)
    dut.rx_i.setimmediatevalue(1)
    dut.accept_i.setimmediatevalue(0)

    clock = Clock(dut.clk_i, 10, units="ns")  # Create a 1 us period clock
    cocotb.start_soon(clock.start())  # Start the clock

    # Execution will block until reset_dut has completed
    dut._log.info("Hold reset")
    await reset_dut(reset_n, 100)
    dut._log.info("Released reset")

    # Test 10 UART transmissions
    for i in range(10):
        await clkedge
        val = random.randint(0, 255)
        await uart_driver.send(val)
        rec = await vai_receiver.receive();
        assert rec == val, "UART received data was incorrect on the {}th cycle".format(i)

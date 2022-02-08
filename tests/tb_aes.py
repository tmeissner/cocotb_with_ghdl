import logging
import random
import cocotb
import pprint
from Vai import VaiDriver, VaiReceiver
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge, Timer, ReadOnly
from Crypto.Cipher import AES
from Crypto.Util.number import long_to_bytes, getRandomNBitInteger
import binascii


# Reset coroutine
async def reset_dut(reset_n, duration_ns):
    reset_n.value = 0
    await Timer(duration_ns, units="ns")
    reset_n.value = 1


@cocotb.test()
async def test_aes_enc(dut):
    """ Test AES encryption """

    clkedge = RisingEdge(dut.clk_i)

    # Connect reset
    reset = dut.reset_i

    # Instantiate VAI driver & receiver
    _input = [dut.mode_i, dut.key_i, dut.data_i]
    vai_driver = VaiDriver(dut.clk_i, _input, dut.valid_i, dut.accept_o)
    vai_receiver = VaiReceiver(dut.clk_i, dut.data_o, dut.valid_o, dut.accept_i)

    # Drive input defaults (setimmediatevalue to avoid x asserts)
    dut.mode_i.setimmediatevalue(0)
    dut.key_i.setimmediatevalue(0)
    dut.data_i.setimmediatevalue(0)
    dut.valid_i.setimmediatevalue(0)
    dut.accept_i.setimmediatevalue(0)

    clock = Clock(dut.clk_i, 10, units="ns")  # Create a 10 ns period clock
    cocotb.start_soon(clock.start())  # Start the clock

    # Execution will block until reset_dut has completed
    dut._log.info("Hold reset")
    await reset_dut(reset, 100)
    dut._log.info("Released reset")

    # Test 10 AES calculations
    for i in range(10):
        await clkedge
        _key = getRandomNBitInteger(128)
        _data = getRandomNBitInteger(128)
        # Drive AES inputs
        await vai_driver.send([0, _key, _data])
        # Calc reference data
        _aes = AES.new(long_to_bytes(_key), AES.MODE_ECB)
        _ref = _aes.encrypt(long_to_bytes(_data))
        # Get DUT output data
        _rec = await vai_receiver.receive()
        assert _rec.buff == _ref, f"Encrypt error, got {_rec.buff}, expected {_ref}"


@cocotb.test()
async def test_aes_dec(dut):
    """ Test AES decryption """

    clkedge = RisingEdge(dut.clk_i)

    # Connect reset
    reset = dut.reset_i

    # Instantiate VAI driver & receiver
    _input = [dut.mode_i, dut.key_i, dut.data_i]
    vai_driver = VaiDriver(dut.clk_i, _input, dut.valid_i, dut.accept_o)
    vai_receiver = VaiReceiver(dut.clk_i, dut.data_o, dut.valid_o, dut.accept_i)

    # Drive input defaults (setimmediatevalue to avoid x asserts)
    dut.mode_i.setimmediatevalue(0)
    dut.key_i.setimmediatevalue(0)
    dut.data_i.setimmediatevalue(0)
    dut.valid_i.setimmediatevalue(0)
    dut.accept_i.setimmediatevalue(0)

    clock = Clock(dut.clk_i, 10, units="ns")  # Create a 10 ns period clock
    cocotb.start_soon(clock.start())  # Start the clock

    # Execution will block until reset_dut has completed
    dut._log.info("Hold reset")
    await reset_dut(reset, 100)
    dut._log.info("Released reset")

    # Test 10 AES calculations
    for i in range(10):
        await clkedge
        _key = getRandomNBitInteger(128)
        _data = getRandomNBitInteger(128)
        # Drive AES inputs
        await vai_driver.send([1, _key, _data])
        # Calc reference data
        _aes = AES.new(long_to_bytes(_key), AES.MODE_ECB)
        _ref = _aes.decrypt(long_to_bytes(_data))
        # Get DUT output data
        _rec = await vai_receiver.receive()
        assert _rec.buff == _ref, f"Decrypt error, got {_rec.buff}, expected {_ref}"

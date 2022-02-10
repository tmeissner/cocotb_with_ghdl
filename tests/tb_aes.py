import logging
import random
import cocotb
import pprint
from Vai import VaiDriver, VaiReceiver, VaiMonitor
from cocotb.clock import Clock
from cocotb.queue import Queue
from cocotb.triggers import FallingEdge, RisingEdge, Timer, ReadOnly
from Crypto.Cipher import AES
from Crypto.Util.number import long_to_bytes, getRandomNBitInteger
import vsc


# Reset coroutine
async def reset_dut(reset_n, duration_ns):
    reset_n.value = 0
    await Timer(duration_ns, units="ns")
    reset_n.value = 1


# Stimuli model class
@vsc.randobj
class constraints():
    def __init__(self):
        self.key = vsc.rand_bit_t(128)
        self.data = vsc.rand_bit_t(128)

    @vsc.constraint
    def c(self):
        self.data >= 0 and self.data <= 2**128-1
        vsc.dist(self.key, [
            vsc.weight(0,  25),
            vsc.weight((1,2**128-2), 50),
            vsc.weight((2**128-1), 25)])


# Stimuli covergroup
@vsc.covergroup
class covergroup():
    def __init__(self):
        self.with_sample(
            mode = vsc.bit_t(1),
            key = vsc.bit_t(128)
        )

        self.enc = vsc.coverpoint(self.mode, bins=dict(
            enc = vsc.bin(0)))

        self.dec = vsc.coverpoint(self.mode, bins=dict(
            dec = vsc.bin(1)))

        self.key0 = vsc.coverpoint(self.key, bins=dict(
            key0 = vsc.bin(0)))

        self.keyF = vsc.coverpoint(self.key, bins=dict(
            keyF = vsc.bin(2**128-1)))

        self.encXkey0 = vsc.cross([self.enc, self.key0])
        self.encXkeyF = vsc.cross([self.enc, self.keyF])

        self.decXkey0 = vsc.cross([self.dec, self.key0])
        self.decXkeyF = vsc.cross([self.dec, self.keyF])


async def cg_sample(cg, queue):
    while True:
        _data = await queue.get()
        cg.sample(_data[0].value, _data[1].value)


@cocotb.test(skip=False)
async def test_aes_enc(dut):
    """ Test AES encryption """

    clkedge = RisingEdge(dut.clk_i)

    # Connect reset
    reset = dut.reset_i

    _input = [dut.mode_i, dut.key_i, dut.data_i]
    _output = dut.data_o
    # DUT input side
    vai_driver = VaiDriver(dut.clk_i, _input, dut.valid_i, dut.accept_o)
    vai_in_queue = cocotb.queue.Queue()
    vai_in_monitor = VaiMonitor(dut.clk_i, _input, dut.valid_i, dut.accept_o, vai_in_queue)
    # DUT output side
    vai_receiver = VaiReceiver(dut.clk_i, dut.data_o, dut.valid_o, dut.accept_i)
    vai_out_monitor = VaiMonitor(dut.clk_i, _output, dut.valid_o, dut.accept_i)

    cr = constraints()
    cg = covergroup()
    cocotb.start_soon(cg_sample(cg, vai_in_queue))

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
        # Get now random stimuli
        cr.randomize()
        _key = cr.key
        _data = cr.data
        await clkedge
        # Drive AES inputs
        await vai_driver.send([0, _key, _data])
        # Calc reference data
        _aes = AES.new(_key.to_bytes(16, 'big'), AES.MODE_ECB)
        _ref = _aes.encrypt(_data.to_bytes(16, 'big'))
        # Get DUT output data
        _rec = await vai_receiver.receive()
        # Equivalence check
        assert _rec.buff == _ref, \
            f"Encrypt error, got 0x{_rec.buff.hex()}, expected 0x{_ref.hex()}"


@cocotb.test(skip=False)
async def test_aes_dec(dut):
    """ Test AES decryption """

    clkedge = RisingEdge(dut.clk_i)

    # Connect reset
    reset = dut.reset_i

    _input = [dut.mode_i, dut.key_i, dut.data_i]
    _output = dut.data_o
    # DUT input side
    vai_driver = VaiDriver(dut.clk_i, _input, dut.valid_i, dut.accept_o)
    vai_in_queue = cocotb.queue.Queue()
    vai_in_monitor = VaiMonitor(dut.clk_i, _input, dut.valid_i, dut.accept_o, vai_in_queue)
    # DUT output side
    vai_receiver = VaiReceiver(dut.clk_i, dut.data_o, dut.valid_o, dut.accept_i)
    vai_out_monitor = VaiMonitor(dut.clk_i, _output, dut.valid_o, dut.accept_i)

    cr = constraints()
    cg = covergroup()
    cocotb.start_soon(cg_sample(cg, vai_in_queue))

    # Drive input defaults (setimmediatevalue to avoid x asserts)
    dut.mode_i.setimmediatevalue(0)
    dut.key_i.setimmediatevalue(0)
    dut.data_i.setimmediatevalue(0)
    dut.valid_i.setimmediatevalue(0)
    dut.accept_i.setimmediatevalue(0)

    clock = Clock(dut.clk_i, 10, units="ns")  # Create a 10 ns period clock
    cocotb.start_soon(clock.start())  # Start the clock

    # Execution will block until reset_dut has completed
    await reset_dut(reset, 100)
    dut._log.info("Released reset")

    # Test 10 AES calculations
    for i in range(10):
        # Get now random stimuli
        cr.randomize()
        _key = cr.key
        _data = cr.data
        await clkedge
        # Drive AES inputs
        await vai_driver.send([1, _key, _data])
        # Calc reference data
        _aes = AES.new(_key.to_bytes(16, 'big'), AES.MODE_ECB)
        _ref = _aes.decrypt(_data.to_bytes(16, 'big'))
        # Get DUT output data
        _rec = await vai_receiver.receive()
        # Equivalence check
        assert _rec.buff == _ref, \
            f"Decrypt error, got 0x{_rec.buff.hex()}, expected 0x{_ref.hex()}"

    with open('results/tb_aes_fcover.txt', 'w', encoding='utf-8') as f:
        f.write(vsc.get_coverage_report())

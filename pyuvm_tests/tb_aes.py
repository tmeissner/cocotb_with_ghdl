from cocotb.triggers import Combine
from pyuvm import (
    uvm_test,
    uvm_sequence,
    uvm_sequence_item,
    uvm_sequencer,
    uvm_driver,
    uvm_component,
    uvm_subscriber,
    uvm_env,
    uvm_factory,
    uvm_analysis_port,
    uvm_tlm_analysis_fifo,
    uvm_get_port,
    ConfigDB,
    UVMConfigItemNotFound,
)
from vsc import get_coverage_report
from VaiBfm import VaiBfm, Mode
from Coverage import constraints, covergroup
from Crypto.Cipher import AES
import cocotb
import pyuvm
import vsc


@pyuvm.test()
class AesTest(uvm_test):
    def build_phase(self):
        self.env = AesEnv("env", self)

    def end_of_elaboration_phase(self):
        self.test_all = TestAllSeq.create("test_all")

    async def run_phase(self):
        self.raise_objection()
        await self.test_all.start()
        self.drop_objection()


@pyuvm.test()
class ParallelTest(AesTest):
    def end_of_elaboration_phase(self):
        uvm_factory().set_type_override_by_type(TestAllSeq, TestAllParallelSeq)
        return super().end_of_elaboration_phase()


# Virtual sequence that starts other sequences
class TestAllSeq(uvm_sequence):

    async def body(self):
        # get the sequencer handle
        seqr = ConfigDB().get(None, "", "SEQR")
        enc_rand_seq = EncRandSeq("enc_random")
        dec_rand_seq = DecRandSeq("dec_random")
        await enc_rand_seq.start(seqr)
        await dec_rand_seq.start(seqr)


# Running encryption and decryption sequences in parallel
class TestAllParallelSeq(uvm_sequence):

    async def body(self):
        seqr = ConfigDB().get(None, "", "SEQR")
        enc_rand_seq = EncRandSeq("enc_random")
        dec_rand_seq = DecRandSeq("dec_random")
        enc_rand_task = cocotb.start_soon(enc_rand_seq.start(seqr))
        dec_rand_task = cocotb.start_soon(dec_rand_seq.start(seqr))
        await Combine(enc_rand_task, dec_rand_task)


# Sequence item which holds the stimuli for one operation
class AesSeqItem(uvm_sequence_item):

    def __init__(self, name, mode, key, data):
        super().__init__(name)
        self.mode = mode
        self.key = key
        self.data = data

    def __eq__(self, other):
        same = self.mode == other.mode and self.key == other.key and self.data == other.data
        return same

    def __str__(self):
        return f"{self.get_name()} : Mode: 0b{self.mode:01x} \
        Key: 0x{self.key:016x} Data: 0x{self.data:016x}"


# Abstract basis sequence class
# set_operands() has to be implemented by class that inherits from this class
class BaseSeq(uvm_sequence):

    async def body(self):
        self.cr = constraints()
        for _ in range(20):
            aes_tr = AesSeqItem("aes_tr", 0, 0, 0)
            await self.start_item(aes_tr)
            self.set_operands(aes_tr)
            await self.finish_item(aes_tr)

    def set_operands(self, tr):
        pass


# Sequence for encryption tests with random stimuli
class EncRandSeq(BaseSeq):
    def set_operands(self, tr):
        self.cr.randomize()
        tr.mode = 0
        tr.key = self.cr.key
        tr.data = self.cr.data


# Sequence for decryption tests with random stimuli
class DecRandSeq(BaseSeq):
    def set_operands(self, tr):
        self.cr.randomize()
        tr.mode = 1
        tr.key = self.cr.key
        tr.data = self.cr.data


class Driver(uvm_driver):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def start_of_simulation_phase(self):
        self.bfm = VaiBfm()

    async def launch_tb(self):
        await self.bfm.reset()
        self.bfm.start_tasks()

    async def run_phase(self):
        await self.launch_tb()
        while True:
            op = await self.seq_item_port.get_next_item()
            await self.bfm.send_op(op.mode, op.key, op.data)
            result = await self.bfm.get_output()
            self.ap.write(result)
            self.seq_item_port.item_done()


class Scoreboard(uvm_component):

    def build_phase(self):
        self.input_fifo = uvm_tlm_analysis_fifo("input_fifo", self)
        self.output_fifo = uvm_tlm_analysis_fifo("output_fifo", self)
        self.input_get_port = uvm_get_port("input_get_port", self)
        self.output_get_port = uvm_get_port("output_get_port", self)
        self.input_export = self.input_fifo.analysis_export
        self.output_export = self.output_fifo.analysis_export
        self.passed = True

    def connect_phase(self):
        self.input_get_port.connect(self.input_fifo.get_export)
        self.output_get_port.connect(self.output_fifo.get_export)

    def check_phase(self):
        while self.output_get_port.can_get():
            _, result = self.output_get_port.try_get()
            op_success, op = self.input_get_port.try_get()
            if not op_success:
                self.logger.critical(f"result {result} had no input operation")
            else:
                (mode, key, data) = op
                aes = AES.new(key.buff, AES.MODE_ECB)
                if not mode:
                    reference = aes.encrypt(data.buff)
                else:
                    reference = aes.decrypt(data.buff)
                if result.buff == reference:
                    self.logger.info(f"PASSED: {Mode(mode).name} {data.hex()} with key "
                                      f"{key.hex()} = {result.hex()}")
                else:
                    self.logger.error(f"FAILED: {Mode(mode).name} {data.hex()} with key "
                                      f"{key.hex()} = 0x{result.hex()}, "
                                      f"expected {reference.hex()}")
                    self.passed = False

    def report_phase(self):
        assert self.passed, "Test failed"


class Monitor(uvm_component):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.bfm = VaiBfm()
        self.get_method = getattr(self.bfm, method_name)

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    async def run_phase(self):
        while True:
            datum = await self.get_method()
            self.logger.debug(f"MONITORED {datum}")
            self.ap.write(datum)


# Coverage collector and checker
class Coverage(uvm_subscriber):

    def start_of_simulation_phase(self):
        self.cg = covergroup()
        try:
            self.disable_errors = ConfigDB().get(
                self, "", "DISABLE_COVERAGE_ERRORS")
        except UVMConfigItemNotFound:
            self.disable_errors = False

    def write(self, data):
        (mode, key, _) = data
        self.cg.sample(mode, key)

    def report_phase(self):
        if not self.disable_errors:
            if self.cg.get_coverage() != 100.0:
                self.logger.warning(
                    f"Functional coverage incomplete.")
            else:
                self.logger.info("Covered all operations")
        with open('results/tb_aes_fcover.txt', 'a', encoding='utf-8') as f:
            f.write(get_coverage_report(details=True))
        vsc.write_coverage_db('results/tb_aes_fcover.xml')


# AES test bench environment
# Creates instances of components and connects them
class AesEnv(uvm_env):

    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)
        self.driver = Driver.create("driver", self)
        self.input_mon = Monitor("input_mon", self, "get_input")
        self.coverage = Coverage("coverage", self)
        self.scoreboard = Scoreboard("scoreboard", self)

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)
        self.input_mon.ap.connect(self.scoreboard.input_export)
        self.input_mon.ap.connect(self.coverage.analysis_export)
        self.driver.ap.connect(self.scoreboard.output_export)

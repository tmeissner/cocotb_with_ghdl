The original repository is now located on my own git-server at [https://git.goodcleanfun.de/tmeissner/cocotb_with_ghdl](https://git.goodcleanfun.de/tmeissner/cocotb_with_ghdl)
It is mirrored to github with every push, so both should be in sync.

# cocotb_with_ghdl

*At the moment, this repo is in an early state and serves as a learning tool for me. So it contains a a lot of quirks and code which can be done much better by cocotb-professionals.*

A collection of examples of using [cocotb](https://www.cocotb.org/) for functional verification of VHDL designs with [GHDL](https://github.com/ghdl/ghdl).

This is a project with the purpose to learn using cocotb with GHDL. It is  intended for my simple (and more complex in future) experiments with using the Python language instead of VHDL or SV to verify digital designs.

It is recommended to use an up-to-date version of GHDL as potential bugs are fixed very quickly. You can build GHDL from source or use one of the Docker images of the [hdl containers project](https://hdl.github.io/containers/) (recommended). For example the `hdlc/sim:scipy` docker image. This image contains a recent version of cocotb and a C++ compiler (needed to build some wheels during installing requirements with pip).

Have fun!

## Quickstart guide


### Change into docker container & install requirements
```
$ git clone https://git.goodcleanfun.de/tmeissner/cocotb_with_ghdl.git
$ cd cocotb_with_ghdl
$ ./env-setup.sh
$ docker run --rm -ti --volume=$(pwd):/build -e DISPLAY=$DISPLAY \
  --volume /tmp/.X11-unix:/tmp/.X11-unix hdlc/sim:scipy /bin/bash
$ ./docker-setup.sh
Collecting cocotb-bus
  Downloading cocotb-bus-0.2.1.tar.gz (28 kB)
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
    Preparing wheel metadata ... done
...
Successfully built cocotb-bus wavedrom python-constraint
Installing collected packages: lxml, cocotb-bus, toposort, svgwrite, pyyaml, pyucis, python-constraint, pyboolector, cocotbext-axi, attrdict, wavedrom, pyvsc, pyuvm, cocotbext-uart, cocotbext-spi, cocotbext-pcie, cocotbext-eth, cocotb-coverage
Successfully installed attrdict-2.0.1 cocotb-bus-0.2.1 cocotb-coverage-1.1.0 cocotbext-axi-0.1.18 cocotbext-eth-0.1.18 cocotbext-pcie-0.1.20 cocotbext-spi-0.1.2 cocotbext-uart-0.1.2 lxml-4.7.1 pyboolector-3.2.2.20220125.14 python-constraint-1.4.0 pyucis-0.0.5.20211020.1 pyuvm-2.6.1 pyvsc-0.6.7.1792877175 pyyaml-6.0 svgwrite-1.4.1 toposort-1.7 wavedrom-2.0.3.post2

```

### Run default test (UART TX)
```
root@6ee2bee145d4:~# cd /build/tests/
root@6ee2bee145d4:/build/tests# make
make -f Makefile results/uarttx.xml
make[1]: Entering directory '/build/tests'
mkdir -p results
mkdir -p work
/usr/local/bin/ghdl -i  --std=08 --workdir=work --work=libvhdl ../libvhdl/common/UtilsP.vhd      &&  \
/usr/local/bin/ghdl -i  --std=08 --workdir=work --work=work ../libvhdl/syn/*.vhd && \
/usr/local/bin/ghdl -m  --std=08 --workdir=work -Pwork --work=work uarttx
analyze ../libvhdl/common/UtilsP.vhd
analyze ../libvhdl/syn/UartTx.vhd
elaborate uarttx
MODULE=tb_uart TESTCASE=test_uarttx TOPLEVEL=uarttx TOPLEVEL_LANG=vhdl \
 /usr/local/bin/ghdl -r  --workdir=work -Pwork --work=work uarttx --vpi=/usr/local/lib/python3.9/dist-packages/cocotb/libs/libcocotbvpi_ghdl.so --wave=results/uarttx.ghw --psl-report=results/uarttx_psl.json --vpi-trace=results/uarttx_vpi.log
loading VPI module '/usr/local/lib/python3.9/dist-packages/cocotb/libs/libcocotbvpi_ghdl.so'
     -.--ns INFO     cocotb.gpi                         ..mbed/gpi_embed.cpp:76   in set_program_name_in_venv        Did not detect Python virtual environment. Using system-wide Python interpreter
     -.--ns INFO     cocotb.gpi                         ../gpi/GpiCommon.cpp:99   in gpi_print_registered_impl       VPI registered
VPI module loaded!
     0.00ns INFO     Running on GHDL version 2.0.0-dev (v1.0.0-974-g0e46300c) [Dunoon edition]
     0.00ns INFO     Running tests with cocotb v1.7.0.dev0 from /usr/local/lib/python3.9/dist-packages/cocotb
     0.00ns INFO     Seeding Python random module with 1644236947
/usr/local/lib/python3.9/dist-packages/attrdict/mapping.py:4: DeprecationWarning: Using or importing the ABCs from 'collections' instead of from 'collections.abc' is deprecated since Python 3.3, and in 3.10 it will stop working
  from collections import Mapping
/usr/local/lib/python3.9/dist-packages/attrdict/mixins.py:5: DeprecationWarning: Using or importing the ABCs from 'collections' instead of from 'collections.abc' is deprecated since Python 3.3, and in 3.10 it will stop working
  from collections import Mapping, MutableMapping, Sequence
     0.00ns INFO     Found test tb_uart.test_uarttx
     0.00ns INFO     running test_uarttx (1/1)
                       First simple test
     0.00ns INFO     Valid-accept driver
     0.00ns INFO       cocotbext-vai version 0.0.1
     0.00ns INFO       Copyright (c) 2022 Torsten Meissner
     0.00ns INFO     UART receiver
     0.00ns INFO       cocotbext-uart version 0.0.1
     0.00ns INFO       Copyright (c) 2022 Torsten Meissner
     0.00ns INFO     Hold reset
   100.00ns INFO     Released reset
   110.00ns INFO     Sending data:  0xaf
  1170.00ns INFO     Received data: 0xaf
  1190.00ns INFO     Sending data:  0x56
  2280.00ns INFO     Received data: 0x56
  2300.00ns INFO     Sending data:  0xb1
  3390.00ns INFO     Received data: 0xb1
  3410.00ns INFO     Sending data:  0x80
  4500.00ns INFO     Received data: 0x80
  4520.00ns INFO     Sending data:  0xc4
  5610.00ns INFO     Received data: 0xc4
  5630.00ns INFO     Sending data:  0x8
  6720.00ns INFO     Received data: 0x8
  6740.00ns INFO     Sending data:  0x68
  7830.00ns INFO     Received data: 0x68
  7850.00ns INFO     Sending data:  0x30
  8940.00ns INFO     Received data: 0x30
  8960.00ns INFO     Sending data:  0xa2
 10050.00ns INFO     Received data: 0xa2
 10070.00ns INFO     Sending data:  0x70
 11160.00ns INFO     Received data: 0x70
 11160.00ns INFO     test_uarttx passed
 11160.00ns INFO     **************************************************************************************
                     ** TEST                          STATUS  SIM TIME (ns)  REAL TIME (s)  RATIO (ns/s) **
                     **************************************************************************************
                     ** tb_uart.test_uarttx            PASS       11160.00           0.23      48943.29  **
                     **************************************************************************************
                     ** TESTS=1 PASS=1 FAIL=0 SKIP=0              11160.00           0.31      35939.72  **
                     **************************************************************************************

make[1]: Leaving directory '/build/tests
```

## Available Tests

### UART

Simple tests of UART transmitter & receiver of the *libvhdl* project

* `make DUT=uarttx` or `make`
* `make DUT=uartrx`

### Wishbone

Simple tests of Wishbone slave of the *libvhdl* project

* `make DUT=wishbone`

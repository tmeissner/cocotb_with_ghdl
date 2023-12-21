# Default test
DUT ?= uarttx

# Path to ext deps
EXT := ../ext

ifeq (${DUT}, wishbone)
  TOPLEVEL := wishboneslavee
  SIM_ARGS := -gSimulation=true \
    -gAddressWidth=8 \
    -gDataWidth=16
else
  TOPLEVEL := ${DUT}
endif

# Cocotb related
MODULE              := tb_${DUT}
COCOTB_LOG_LEVEL    := DEBUG
CUSTOM_COMPILE_DEPS := results
COCOTB_RESULTS_FILE := results/${MODULE}.xml

# Simulator & RTL related
SIM                  ?= ghdl
TOPLEVEL_LANG        := vhdl
VHDL_SOURCES_libvhdl := ${EXT}/libvhdl/common/UtilsP.vhd
VHDL_SOURCES         := ${EXT}/libvhdl/syn/*  \
  ${EXT}/cryptocores/aes/rtl/vhdl/*.vhd
SIM_BUILD            := build

ifeq (${SIM}, ghdl)
  COMPILE_ARGS := --std=08
  SIM_ARGS             += \
    --wave=results/${MODULE}.ghw \
    --psl-report=results/${MODULE}_psl.json \
    --vpi-trace=results/${MODULE}_vpi.log
else
  EXTRA_ARGS := --std=08
  VHDL_LIB_ORDER := libvhdl
endif


include $(shell cocotb-config --makefiles)/Makefile.sim


results:
	mkdir -p results


.PHONY: clean
clean::
	rm -rf *.o __pycache__ uarttx uartrx wishboneslavee aes results $(SIM_BUILD)

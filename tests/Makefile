# Default test
DUT ?= uarttx

# Test related variables
ifeq (${DUT}, uarttx)
  MODULE   := tb_uart
  TOPLEVEL := ${DUT}
else ifeq (${DUT}, uartrx)
  MODULE   := tb_uart
  TOPLEVEL := ${DUT}
else ifeq (${DUT}, wishbone)
  MODULE   := tb_wishbone
  TOPLEVEL := wishboneslavee
  SIM_ARGS := -gSimulation=true
else
  $(error ${DUT} not available)
endif


# Simulator (GHDL) & RTL related
SIM                  := ghdl
TOPLEVEL_LANG        := vhdl
VHDL_SOURCES_libvhdl := ../libvhdl/common/UtilsP.vhd	
VHDL_SOURCES         := ../libvhdl/syn/*.vhd
SIM_BUILD            := work
COMPILE_ARGS         := --std=08
SIM_ARGS             += \
  --wave=results/${TOPLEVEL}.ghw \
  --psl-report=results/${TOPLEVEL}_psl.json \
  --vpi-trace=results/${TOPLEVEL}_vpi.log

# Cocotb related
TESTCASE            := test_${DUT}
COCOTB_LOG_LEVEL    := DEBUG
CUSTOM_COMPILE_DEPS := results
COCOTB_RESULTS_FILE := results/${TOPLEVEL}.xml


include $(shell cocotb-config --makefiles)/Makefile.sim


results:
	mkdir -p results


.PHONY: clean
clean::
	rm -rf *.o __pycache__ uarttx uartrx results

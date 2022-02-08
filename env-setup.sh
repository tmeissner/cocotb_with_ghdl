#!/bin/bash

if [ ! -d cocotbext-wishbone/.git ]; then
  git clone https://github.com/wallento/cocotbext-wishbone.git
  cd cocotbext-wishbone && patch < ../setup.py.patch
  cd ..
fi

set signals [list]
lappend signals "top.UartTx.reset_n_i"
lappend signals "top.UartTx.clk_i"
lappend signals "top.UartTx.valid_i"
lappend signals "top.UartTx.accept_o"
lappend signals "top.UartTx.data_i"
lappend signals "top.UartTx.tx_o"
lappend signals "top.UartTx.s_uart_state"
set num_added [ gtkwave::addSignalsFromList $signals ]

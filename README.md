# py4hw

[![Join the chat at https://gitter.im/davidcastells/py4hw](https://badges.gitter.im/davidcastells/py4hw.svg)](https://gitter.im/davidcastells/py4hw?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

py4hw is an HDL library based on python to create digital circuits following a structural design methodology. It is highly influenced by the JHDL principles.

clock is implicit

A hardware system is defined by HWSystem


All Hardware blocks inherit from class Logic

There are 2 types of Logic circuits structural and behavioural ones.

Structural circuits just instantiate other circuits.

Behavioural circuits describe the circuit behaviour by some functions.
There are 2 types of behavioural circuits: Combinational and Sequential.

Combination circuits must implement the "propagate" function

Sequential circuits must implement the "clock" function.

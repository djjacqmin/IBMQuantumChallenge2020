# Double encode the qRAM?
# Load 16 bits, vs. 4 bits (qram), 4 (moves in binary)
# Load qram = 6 options (3 bits) + 8 position (11 total) + 8 (moves) + 3 (counter) +1 ancilla +4() =28
# load qram = 6 optins (3 bits) + 4 position (in binary, 00, 01 ..) (10 total)


# Check for empty rows might not be legal
# Think from perspective of oracle ... what are we checking for?
# How are we marking the solution?

# Oracle: Mark the problem that is false.
# How do you define a problem that is false?
# Only solvable with 4 beams? (Or, can be solved in 2,3 beams)
# Has zero blank rows and columns.

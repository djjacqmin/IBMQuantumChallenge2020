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

problem_set = [
    [["0", "2"], ["1", "0"], ["1", "2"], ["1", "3"], ["2", "0"], ["3", "3"]],
    [["0", "0"], ["0", "1"], ["1", "2"], ["2", "2"], ["3", "0"], ["3", "3"]],
    [["0", "0"], ["1", "1"], ["1", "3"], ["2", "0"], ["3", "2"], ["3", "3"]],
    [["0", "0"], ["0", "1"], ["1", "1"], ["1", "3"], ["3", "2"], ["3", "3"]],
    [["0", "2"], ["1", "0"], ["1", "3"], ["2", "0"], ["3", "2"], ["3", "3"]],
    [["1", "1"], ["1", "2"], ["2", "0"], ["2", "1"], ["3", "1"], ["3", "3"]],
    [["0", "2"], ["0", "3"], ["1", "2"], ["2", "0"], ["2", "1"], ["3", "3"]],
    [["0", "0"], ["0", "3"], ["1", "2"], ["2", "2"], ["2", "3"], ["3", "0"]],
    [["0", "3"], ["1", "1"], ["1", "2"], ["2", "0"], ["2", "1"], ["3", "3"]],
    [["0", "0"], ["0", "1"], ["1", "3"], ["2", "1"], ["2", "3"], ["3", "0"]],
    [["0", "1"], ["0", "3"], ["1", "2"], ["1", "3"], ["2", "0"], ["3", "2"]],
    [["0", "0"], ["1", "3"], ["2", "0"], ["2", "1"], ["2", "3"], ["3", "1"]],
    [["0", "1"], ["0", "2"], ["1", "0"], ["1", "2"], ["2", "2"], ["2", "3"]],
    [["0", "3"], ["1", "0"], ["1", "3"], ["2", "1"], ["2", "2"], ["3", "0"]],
    [["0", "2"], ["0", "3"], ["1", "2"], ["2", "3"], ["3", "0"], ["3", "1"]],
    [["0", "1"], ["1", "0"], ["1", "2"], ["2", "2"], ["3", "0"], ["3", "1"]],
]


def convert_problem_set_to_binary(ps: list):

    ps_binary = list()

    for row in ps:
        row_binary = ["0" for n in range(16)]
        for pair in row:
            # Convert pair to binary location:
            location = int(pair[0]) * 4 + int(pair[1])
            row_binary[location] = "1"

        row_binary = "".join(row_binary)
        ps_binary.append(row_binary)

    print(ps_binary)


if __name__ == "__main__":
    convert_problem_set_to_binary(problem_set)

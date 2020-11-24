from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import execute
from qc_grader import prepare_ex3, grade_ex3
import numpy as np

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


def qram_loader(
    problem_set, qc,
):
    pass


def oracle():
    pass


def diffusion():
    pass


def week3_ans_func(problem_set):
    # Build your quantum circuit here
    # In addition, please make it a function that can solve the problem even with different inputs (problem_set). We do validation with different inputs.

    qr_shot_h = QuantumRegister(4, name="h_shots")
    qr_shot_v = QuantumRegister(4, name="v_shots")

    qr_data_h = QuantumRegister(4, name="h_data")
    qr_data_v = QuantumRegister(4, name="v_data")
    qr_addr = QuantumRegister(4, name="address")

    cr_addr = ClassicalRegister(4, name="")
    qc = QuantumCircuit(qr_shot)

    # Code for Grover's algorithm with iterations = 1 will be as follows.
    for i in range(1):
        oracle()
        diffusion()

    return qc


if __name__ == "__main__":

    # Execute your circuit with following prepare_ex3() function.
    # The prepare_ex3() function works like the execute() function with only QuantumCircuit as an argument.
    job = prepare_ex3(week3_ans_func)

    result = job.result()
    counts = result.get_counts()
    original_problem_set_counts = counts[0]

    print(original_problem_set_counts)
    # The bit string with the highest number of observations is treated as the solution.

    grade_ex3(job)

# Thoughts:
# Adder to verify shots does not exceed 3
# Hint about computation basis set of three - what could that mean?

from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import execute, Aer
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

    return ps_binary


def data_loader(qc, qr_data, problem):
    for i, bit in enumerate(problem):
        if bit == "1":
            qc.x(qr_data[i])

    return qc


def oracle(qc, qr_shot, qr_data, qr_ancl):

    connections = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [8, 9, 10, 11],
        [12, 13, 14, 15],
        [0, 4, 8, 12],
        [1, 5, 9, 13],
        [2, 6, 10, 14],
        [3, 7, 11, 15],
    ]

    # Append logic for game
    for i, box in enumerate(connections):
        for connection in box:
            qc.cz(qr_shot[i], qr_data[connection])

    qc.mct(qr_shot, qr_ancl)

    # Uncompute logic for game
    for i, box in enumerate(reversed(connections)):
        for connection in reversed(box):
            qc.cx(qr_shot[i], qr_data[connection])

    return qc


def diffusion(qc, qubits, qr_extr):
    qc.h(qubits)
    qc.x(qubits)
    qc.h(qubits[-1])
    qc.mct(qubits[:-1], qubits[-1], qr_extr, mode="recursion")
    qc.h(qubits[-1])
    qc.x(qubits)
    qc.h(qubits)

    return qc


def week3_ans_func(problem_set):
    # Build your quantum circuit here
    # In addition, please make it a function that can solve the problem even with different inputs (problem_set). We do validation with different inputs.

    problem = convert_problem_set_to_binary(problem_set)[1]

    qr_shot = QuantumRegister(8)
    qr_data = QuantumRegister(16)
    qr_ancl = QuantumRegister(1)
    qr_extr = QuantumRegister(2)

    cr = ClassicalRegister(8)

    qc = QuantumCircuit(qr_shot, qr_data, qr_ancl, qr_extr, cr)

    # Load data
    qc = data_loader(qc, qr_data, problem)

    # Prepare ancilla
    qc.x(qr_ancl)
    qc.h(qr_ancl)

    # Put solution into superposition
    qc.h(qr_shot)

    # Code for Grover's algorithm with iterations = 1 will be as follows.
    for i in range(5):
        oracle(qc, qr_shot, qr_data, qr_ancl)
        diffusion(qc, qr_shot, qr_extr)

    qc.measure(qr_shot, cr)
    qc = qc.reverse_bits()

    return qc


if __name__ == "__main__":

    qc = week3_ans_func(problem_set)

    backend = Aer.get_backend("qasm_simulator")
    job = execute(
        qc,
        backend=backend,
        shots=1000,
        seed_simulator=12345,
        backend_options={"fusion_enable": True},
    )
    result = job.result()
    count = result.get_counts()

    for k, v in count.items():
        print(f"{k} : {v}")
    qc.draw(output="mpl")


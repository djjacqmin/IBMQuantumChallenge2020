from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import execute, Aer

# from qc_grader import prepare_ex3, grade_ex3
import numpy as np
from heapq import nlargest


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


def qft_dagger(n):
    """n-qubit QFTdagger the first n qubits in circ"""
    circ = QuantumCircuit(n)
    # Don't forget the Swaps!
    for qubit in range(n // 2):
        circ.swap(qubit, n - qubit - 1)
    for j in range(n):
        for m in range(j):
            circ.cp(-np.pi / float(2 ** (j - m)), m, j)
        circ.h(j)

    qft_dag = circ.to_gate()
    qft_dag.name = "$QFT_dag$"
    return qft_dag


def oracle(
    qc, qr_shot_h, qr_shot_v, qr_clustr, qr_countr, qr_anclla, qr_extra, problem
):

    # Step 1: Enter logic for the game
    for i, pair in enumerate(problem):
        horz_num = int(pair[0])
        vert_num = int(pair[1])

        # Connect shot with cluster:
        qc.cx(qr_shot_h[horz_num], qr_clustr[i])
        qc.cx(qr_shot_v[vert_num], qr_clustr[i])

    # Step 2: Append counting logic
    qc.h(qr_countr)

    for q_shot in qr_shot_h[:] + qr_shot_v[:]:
        for i, q_countr in enumerate(qr_countr):
            qc.cp(np.pi / 2 ** (len(qr_countr) - i - 1), q_shot, q_countr)

    qc.append(qft_dagger(len(qr_countr)), qr_countr)

    # Mark the desired state: 3 or less = 00**
    qc.x(qr_countr[2:])

    qc.mct(qr_clustr[:] + qr_countr[2:], qr_anclla, qr_extra, mode="v-chain")

    # Unmark the desired state
    qc.x(qr_countr[2:])

    # Uncompute counting logic
    qc.append(qft_dagger(len(qr_countr)).inverse(), qr_countr)

    for q_shot in qr_shot_h[:] + qr_shot_v[:]:
        for i, q_countr in enumerate(qr_countr):
            qc.cp(np.pi / 2 ** (len(qr_countr) - i - 1), q_shot, q_countr)

    qc.h(qr_countr)

    # Uncompute game logic
    for i, pair in enumerate(problem):
        horz_num = int(pair[0])
        vert_num = int(pair[1])

        # Connect shot with cluster:
        qc.cx(qr_shot_v[vert_num], qr_clustr[i])
        qc.cx(qr_shot_h[horz_num], qr_clustr[i])

    qc.barrier()

    return qc


def diffusion(qc, qubits, qr_extr):
    qc.h(qubits)
    qc.x(qubits)
    qc.h(qubits[-1])
    qc.mct(qubits[:-1], qubits[-1], qr_extr, mode="v-chain")
    qc.h(qubits[-1])
    qc.x(qubits)
    qc.h(qubits)

    qc.barrier()

    return qc


def week3_ans_func(problem_set):
    # Build your quantum circuit here
    # In addition, please make it a function that can solve the problem even with different inputs (problem_set). We do validation with different inputs.

    # problem = convert_problem_set_to_binary(problem_set)[1]
    problem = problem_set[0]

    # 4 + 4 (shot options) + 6 (clusters) + 4 (address) + 3 (counting) + 1 (ancilla) = 22, 6 extra!
    qr_shot_h = QuantumRegister(4, name="horz shots")
    qr_shot_v = QuantumRegister(4, name="vert shots")
    qr_clustr = QuantumRegister(6, name="clusters")
    qr_addres = QuantumRegister(4, name="address")
    qr_countr = QuantumRegister(3, name="counting")
    qr_anclla = QuantumRegister(1, name="ancl")
    qr_extra = QuantumRegister(6, name="extra")

    cr = ClassicalRegister(8)
    cr_test = ClassicalRegister(6)
    cr_count = ClassicalRegister(3)

    qc = QuantumCircuit(
        qr_shot_h, qr_shot_v, qr_clustr, qr_countr, qr_anclla, qr_extra, cr
    )  # , cr_count)

    # Set cluster status to 0
    # No code required

    # Prepare ancilla
    qc.x(qr_anclla)
    qc.h(qr_anclla)

    # Put solution into superposition
    qc.h(qr_shot_h[:] + qr_shot_v[:])

    qc.barrier()

    # Code for Grover's algorithm with iterations = 1 will be as follows.
    for i in range(1):
        oracle(
            qc, qr_shot_h, qr_shot_v, qr_clustr, qr_countr, qr_anclla, qr_extra, problem
        )
        diffusion(qc, qr_shot_h[:] + qr_shot_v[:], qr_extra)

    qc.measure(qr_shot_h[:] + qr_shot_v[:], cr)
    # qc.measure(qr_countr, cr_count)
    qc = qc.reverse_bits()

    return qc


qc = week3_ans_func(problem_set)
# qc.draw(output="mpl")

backend = Aer.get_backend("qasm_simulator")
job = execute(
    qc,
    backend=backend,
    shots=10000,
    seed_simulator=12345,
    # backend_options={"fusion_enable": True},
)
result = job.result()
count = result.get_counts()

# N largest values in dictionary
# Using nlargest
N = 10
res = nlargest(N, count, key=count.get)

# print("The top N value pairs are  " + str(res))
# print(f"Expected solution: 10010010: {count['10010010']} counts")

for k, v in count.items():
    print(f"{k}:{v}")

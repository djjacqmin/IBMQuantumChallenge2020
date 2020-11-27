import time
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import execute, Aer
from qc_grader import prepare_ex3, grade_ex3
import numpy as np
from counter import count_oracle
from week3_func import game_logic_oracle, diffusion

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


def week3_ans_func(problem_set, count_shots=False):

    num_problems = len(problem_set)
    address_qubits = int(np.sqrt(num_problems))
    counting_qubits = 4

    # 4 + 4 (shot options) + 6 (clusters) + 4 (address) + 3 (counting) + 1 (ancilla) = 22, 6 extra!
    qr_shot_h = QuantumRegister(4, name="horz shots")
    qr_shot_v = QuantumRegister(4, name="vert shots")
    qr_clustr = QuantumRegister(6, name="clusters")
    qr_addres = QuantumRegister(address_qubits, name="address")
    qr_countr = QuantumRegister(counting_qubits, name="counting")
    qr_ancl_g = QuantumRegister(1, name="game ancilla")
    qr_ancl_c = QuantumRegister(1, name="count ancilla")
    num_extra = 28 - len(
        qr_shot_h[:]
        + qr_shot_v[:]
        + qr_clustr[:]
        + qr_addres[:]
        + qr_countr[:]
        + qr_ancl_g[:]
        + qr_ancl_c[:]
    )

    qr_extra = QuantumRegister(num_extra, name="extra")

    cr_shots = ClassicalRegister(len(qr_shot_h[:] + qr_shot_v[:]))
    cr_address = ClassicalRegister(address_qubits)

    if count_shots:
        qc = QuantumCircuit(
            qr_shot_h,
            qr_shot_v,
            qr_addres,
            qr_clustr,
            qr_countr,
            qr_ancl_g,
            qr_ancl_c,
            qr_extra,
            cr_shots,
        )
    else:
        qc = QuantumCircuit(
            qr_shot_h,
            qr_shot_v,
            qr_addres,
            qr_clustr,
            qr_countr,
            qr_ancl_g,
            qr_ancl_c,
            qr_extra,
            cr_address,
        )

    # Set cluster status to 0
    # No code required

    # Prepare ancilla
    qc.x(qr_ancl_g[:] + qr_ancl_c[:])
    qc.h(qr_ancl_g[:] + qr_ancl_c[:])

    # Put solution into superposition
    qc.h(qr_shot_h[:] + qr_shot_v[:] + qr_addres[:])

    qc.barrier()

    # Load gates
    game_qubits = (
        qr_shot_h[:] + qr_shot_v[:] + qr_addres[:] + qr_clustr[:] + qr_extra[:]
    )

    game_gate = game_logic_oracle(
        qr_horizontal=qr_shot_h,
        qr_vertical=qr_shot_v,
        qr_address=qr_addres,
        qr_cluster=qr_clustr,
        qr_extra=qr_extra,
    )
    counter_qubits = qr_shot_h[:] + qr_shot_v[:] + qr_countr[:]
    count_me_qubits = qr_shot_h[:] + qr_shot_v[:]
    counter_gate = count_oracle(
        qr_count_me=count_me_qubits, qr_counter=qr_countr, return_gate=True
    )

    game_iterations = 1
    count_iterations = 1

    # Code for Grover's algorithm with iterations = 1 will be as follows.
    for i in range(1):

        # Perform Grover's algorithm for game logic
        for j in range(game_iterations):

            # Append game gate
            qc.append(game_gate, game_qubits)

            # Check solution
            try:
                qc.mct(qr_clustr, qr_ancl_g, qr_extra, mode="v-chain")
            except ValueError:
                qc.mct(qr_clustr, qr_ancl_g, qr_extra, mode="recursion")

            # Uncompute game gate
            qc.append(game_gate.inverse(), game_qubits)

            # Diffusion circuit
            qc = diffusion(qc, qr_shot_h[:] + qr_shot_v[:], qr_extra)

        # Perform Grover's algorithm for counting logic
        for j in range(count_iterations):

            # Append count gate
            qc.append(counter_gate, counter_qubits)

            # Check solution
            try:
                qc.mct(qr_countr, qr_ancl_c, qr_extra, mode="v-chain")
            except ValueError:
                qc.mct(qr_countr, qr_ancl_c, qr_extra, mode="recursion")

            # Uncompute game gate
            qc.append(counter_gate.inverse(), counter_qubits)

            # Diffusion circuit
            qc = diffusion(qc, qr_addres, qr_extra)

    # Measure results
    if count_shots:
        qc.measure(qr_shot_h[:] + qr_shot_v[:], cr_shots)
    else:
        qc.measure(qr_addres, cr_address)

    qc = qc.reverse_bits()

    return qc


if __name__ == "__main__":
    qc = week3_ans_func(problem_set[8:12], count_shots=True)

    backend = Aer.get_backend("qasm_simulator")
    tic = time.perf_counter()
    job = execute(
        qc, backend=backend, shots=15000, backend_options={"fusion_enable": True},
    )
    toc = time.perf_counter()

    print(f"Circuit executed in {toc - tic:0.4f} seconds")

    result = job.result()
    count = result.get_counts()

    for k, v in count.items():
        print(k, v)


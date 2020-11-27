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
    qr_shots = QuantumRegister(8, name="shots")
    qr_cluster = QuantumRegister(6, name="clusters")
    qr_address = QuantumRegister(address_qubits, name="address")
    qr_counter = QuantumRegister(counting_qubits, name="counting")
    qr_ancilla = QuantumRegister(2, name="ancilla")
    num_extra = 28 - len(
        qr_shots[:] + qr_cluster[:] + qr_address[:] + qr_counter[:] + qr_ancilla[:]
    )

    qr_extra = QuantumRegister(num_extra, name="extra")

    cr_shots = ClassicalRegister(len(qr_shots))
    cr_address = ClassicalRegister(address_qubits)

    if count_shots:
        qc = QuantumCircuit(
            qr_shots,
            qr_address,
            qr_cluster,
            qr_counter,
            qr_ancilla,
            qr_extra,
            cr_shots,
        )
    else:
        qc = QuantumCircuit(
            qr_shots,
            qr_address,
            qr_cluster,
            qr_counter,
            qr_ancilla,
            qr_extra,
            cr_address,
        )

    # Set cluster status to 0
    # No code required

    # Prepare ancilla
    qc.x(qr_ancilla)
    qc.h(qr_ancilla)

    # Put solution into superposition
    qc.h(qr_shots[:] + qr_address[:])

    qc.barrier()

    # Load game gate
    game_qubits = qr_shots[:] + qr_address[:] + qr_cluster[:] + qr_extra[:]

    game_gate = game_logic_oracle(
        qr_shots=qr_shots,
        qr_address=qr_address,
        qr_cluster=qr_cluster,
        qr_extra=qr_extra,
        prob_set=problem_set,
    )

    # Load counter gate
    counter_qubits = qr_shots[:] + qr_counter[:]
    counter_gate = count_oracle(
        qr_count_me=qr_shots, qr_counter=qr_counter, return_gate=True
    )

    game_iterations = 1
    # Code for Grover's algorithm with iterations = 1 will be as follows.
    for _ in range(1):

        # Perform Grover's algorithm for game logic
        for j in range(game_iterations):

            # Append game gate
            qc.append(game_gate, game_qubits)

            # Check solution
            try:
                qc.mct(qr_cluster, qr_ancilla[0], qr_extra, mode="v-chain")
            except ValueError:
                qc.mct(qr_cluster, qr_ancilla[0], qr_extra, mode="recursion")

            # Uncompute game gate
            qc.append(game_gate.inverse(), game_qubits)

            # Diffusion circuit
            qc = diffusion(qc, qr_shots, qr_extra)

        # Append counter gate
        qc.append(counter_gate, counter_qubits)

        # Mark the desired state: Exactly 4: 0100
        qc.x(qr_counter[0:2])
        qc.x(qr_counter[3])

        # Check for the solution
        qc.h(qr_ancilla[1])
        qc.mct(qr_counter, qr_ancilla[1], qr_extra, mode="v-chain")
        qc.h(qr_ancilla[1])

        # Unmark the desired state
        qc.x(qr_counter[0:2])
        qc.x(qr_counter[3])

        # Uncompute counter gate
        qc.append(counter_gate.inverse(), counter_qubits)

        # Reverse Grover's algorithm for game logic
        for j in range(game_iterations):

            # Diffusion circuit
            qc = diffusion(qc, qr_shots, qr_extra)

            # Append game gate
            qc.append(game_gate.inverse(), game_qubits)

            # Check solution
            try:
                qc.mct(qr_cluster, qr_ancilla[0], qr_extra, mode="v-chain")
            except ValueError:
                qc.mct(qr_cluster, qr_ancilla[0], qr_extra, mode="recursion")

            # Uncompute game gate
            qc.append(game_gate, game_qubits)

        # Diffusion circuit
        qc = diffusion(qc, qr_address, qr_extra)

    # Measure results
    if count_shots:
        qc.measure(qr_shots, cr_shots)
    else:
        qc.measure(qr_address, cr_address)

    qc = qc.reverse_bits()

    return qc


if __name__ == "__main__":
    qc = week3_ans_func(problem_set, count_shots=False)

    backend = Aer.get_backend("qasm_simulator")
    tic = time.perf_counter()
    job = execute(
        qc,
        backend=backend,
        shots=2000,
        optimization_level=3,
        backend_options={"fusion_enable": True},
    )

    result = job.result()
    count = result.get_counts()

    for k, v in count.items():
        print(k, v)

    toc = time.perf_counter()

    print(f"Circuit executed in {toc - tic:0.4f} seconds")

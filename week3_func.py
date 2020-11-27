from qiskit import QuantumRegister, QuantumCircuit
import numpy as np


def diffusion(qc: QuantumCircuit, qubits: QuantumRegister, qr_extra: QuantumRegister):

    qc.h(qubits)
    qc.x(qubits)
    qc.h(qubits[-1])
    try:
        qc.mct(qubits[:-1], qubits[-1], qr_extra, mode="v-chain")
    except ValueError:
        qc.mct(qubits[:-1], qubits[-1], qr_extra, mode="recursion")
    qc.h(qubits[-1])
    qc.x(qubits)
    qc.h(qubits)

    qc.barrier()

    return qc


def mark_address(qc: QuantumCircuit, qubits: QuantumRegister, index: int):

    if index not in range(len(qubits) ** 2):
        raise ValueError("index must be in range(16)")

    # if len(qubits) != 4:
    #    raise ValueError("qubits must have length of 4")

    # Convert index to a binary string
    if len(qubits) == 1:
        bin_str = f"{index:01b}"
    if len(qubits) == 2:
        bin_str = f"{index:02b}"
    if len(qubits) == 4:
        bin_str = f"{index:04b}"

    for i in range(len(qubits)):
        if bin_str[i] == "0":
            qc.x(qubits[i])

    return qc


def game_logic_oracle(
    qr_horizontal: QuantumRegister,
    qr_vertical: QuantumRegister,
    qr_address: QuantumRegister,
    qr_cluster: QuantumRegister,
    qr_extra: QuantumRegister,
    prob_set,
    return_gate: bool = True,
):

    qc = QuantumCircuit(qr_horizontal, qr_vertical, qr_address, qr_cluster, qr_extra)

    for p, puzzle in enumerate(prob_set):  # for each puzzle

        puzzle = np.array(puzzle, int)  # convert to int
        # Mark the puzzle's address (p):
        qc = mark_address(qc, qr_address, p)

        for c, (h, v) in enumerate(puzzle):  # for each position pair in puzzle
            # Control cluster c with address and the puzzle's horizontal number
            qc.mct(
                qr_address[:] + [qr_horizontal[h]],
                qr_cluster[c],
                qr_extra,
                mode="v-chain",
            )
            qc.mct(
                qr_address[:] + [qr_vertical[v]],
                qr_cluster[c],
                qr_extra,
                mode="v-chain",
            )

        # Unmark the puzzles's address:
        qc = mark_address(qc, qr_address, p)
    # Convert to gate and return
    if return_gate:

        game_logic = qc.to_gate()
        game_logic.name = "Game Logic"
        return game_logic
    else:
        return qc

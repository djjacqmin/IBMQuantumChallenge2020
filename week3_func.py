import numpy as np
from itertools import permutations
from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister, Aer, execute
import time


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

    if index not in range(2 ** len(qubits)):
        raise ValueError(f"index is {index} must be in range(16)")

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
    qr_shots: QuantumRegister,
    qr_address: QuantumRegister,
    qr_cluster: QuantumRegister,
    qr_extra: QuantumRegister,
    prob_set,
    return_gate: bool = True,
):

    qc = QuantumCircuit(qr_shots, qr_address, qr_cluster, qr_extra)

    for p, puzzle in enumerate(prob_set):  # for each puzzle

        puzzle = np.array(puzzle, int)  # convert to int
        # Mark the puzzle's address (p):
        qc = mark_address(qc, qr_address, p)

        for c, (h, v) in enumerate(puzzle):  # for each position pair in puzzle
            # Control cluster c with address and the puzzle's horizontal number
            qc.mct(
                qr_address[:] + [qr_shots[h]], qr_cluster[c], qr_extra, mode="v-chain",
            )
            qc.mct(
                qr_address[:] + [qr_shots[v + 4]],
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


def row_to_dict(row):

    row_dict = {}
    for i, item in enumerate(row):

        if len(row) == 1:
            bin_str = f"{i:01b}"
        if len(row) == 2:
            bin_str = f"{i:01b}"
        if len(row) == 4:
            bin_str = f"{i:02b}"
        if len(row) == 8:
            bin_str = f"{i:02b}"
        if len(row) == 16:
            bin_str = f"{i:04b}"

        row_dict[bin_str] = item

    return row_dict


def get_qram_logic_score(cluster_dict, bit_string="", branch_order=[3, 2, 1, 0]):

    score_array = [10, 69, 223, 487, 1015]

    # Check to see if there is only one value in the dictionary.values()
    if len(set(cluster_dict.values())) == 1:
        # Unique_value = set(cluster_dict.values()).pop()
        # print(f"We have a leaf with value {unique_value} with bit_string {bit_string}")
        return score_array[len(bit_string)]

    zero_dict = {}
    one_dict = {}
    current_bit = branch_order[0]

    for k, v in cluster_dict.items():
        if k[current_bit] == "0":
            zero_dict[k] = v
        else:
            one_dict[k] = v

    score1 = get_qram_logic_score(zero_dict, bit_string + "0", branch_order[1:])
    score2 = get_qram_logic_score(one_dict, bit_string + "1", branch_order[1:])

    return score1 + score2


def get_lowest_score_branching_order(row_of_positions):
    best_score = 9999999
    best_perm = None

    for p in permutations([0, 1, 2, 3]):
        score = get_qram_logic_score(row_to_dict(row_of_positions), branch_order=p)
        if score < best_score:
            best_score = score
            best_perm = p

        return best_perm, best_score


def load_data_with_recursion(
    qc,
    target_cluster,
    control_address,
    control_shots,
    extra_qubits,
    cluster_dict,
    bit_string="",
    branch_order=[0, 1, 2, 3],
):

    depth = len(bit_string)

    # Check to see if there is only one value in the dictionary.values()
    if len(set(cluster_dict.values())) == 1:
        shot_index = set(cluster_dict.values()).pop()
        # print(f"We have a leaf with value {unique_value} with bit_string {bit_string}")
        depth = len(bit_string)

        # Mark address qubits
        for i in range(depth):
            if bit_string[i] == "0":
                address_index = branch_order[i]
                qc.x(control_address[address_index])

        if depth == 0:
            # All problems have same value. CNOT will suffice
            qc.cx(control_shots[shot_index], target_cluster)
        elif depth == 1:
            # One address, one shot, are in control
            qc.ccx(
                control_shots[shot_index],
                control_address[branch_order[0]],
                target_cluster,
            )
        elif depth > 1:
            addr_indices = branch_order[0:depth]
            control_qubits = [control_shots[shot_index]]
            for index in addr_indices:
                control_qubits += [control_address[index]]
            qc.mct(control_qubits, target_cluster, extra_qubits, mode="v-chain")

        # De-mark address qubits
        for i in range(depth):
            if bit_string[i] == "0":
                address_index = branch_order[i]
                qc.x(control_address[address_index])

        return qc

    zero_dict = {}
    one_dict = {}
    current_bit = branch_order[depth]

    for k, v in cluster_dict.items():
        if k[current_bit] == "0":
            zero_dict[k] = v
        else:
            one_dict[k] = v

    qc = load_data_with_recursion(
        qc=qc,
        target_cluster=target_cluster,
        control_address=control_address,
        control_shots=control_shots,
        extra_qubits=extra_qubits,
        cluster_dict=zero_dict,
        bit_string=bit_string + "0",
        branch_order=branch_order,
    )
    qc = load_data_with_recursion(
        qc=qc,
        target_cluster=target_cluster,
        control_address=control_address,
        control_shots=control_shots,
        extra_qubits=extra_qubits,
        cluster_dict=one_dict,
        bit_string=bit_string + "1",
        branch_order=branch_order,
    )

    return qc


def game_logic_oracle_opt(
    qr_shots: QuantumRegister,
    qr_address: QuantumRegister,
    qr_cluster: QuantumRegister,
    qr_extra: QuantumRegister,
    prob_set,
    return_gate: bool = True,
):

    qc = QuantumCircuit(qr_shots, qr_address, qr_cluster, qr_extra)

    ps = np.array(prob_set, int)
    cluster_horz = ps.T[0]
    cluster_vert = ps.T[1]

    for i, cluster in enumerate(cluster_horz):

        # Identify optimal branching order for this cluster
        cluster_dict = row_to_dict(cluster)
        perm, _ = get_lowest_score_branching_order(cluster_dict)

        qc = load_data_with_recursion(
            qc=qc,
            target_cluster=qr_cluster[i],
            control_address=qr_address,
            control_shots=qr_shots[0:4],
            extra_qubits=qr_extra,
            cluster_dict=cluster_dict,
            branch_order=perm,
        )

    for i, cluster in enumerate(cluster_vert):

        # Identify optimal branching order for this cluster
        cluster_dict = row_to_dict(cluster)
        perm, _ = get_lowest_score_branching_order(cluster_dict)

        qc = load_data_with_recursion(
            qc=qc,
            target_cluster=qr_cluster[i],
            control_address=qr_address,
            control_shots=qr_shots[4:8],
            extra_qubits=qr_extra,
            cluster_dict=cluster_dict,
            branch_order=perm,
        )

    # Convert to gate and return
    if return_gate:

        game_logic = qc.to_gate()
        game_logic.name = "Game Logic"
        return game_logic
    else:
        return qc


if __name__ == "__main__":

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

    problem_set = problem_set

    count_shots = True

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

    # Prepare ancilla
    qc.x(qr_ancilla)
    qc.h(qr_ancilla)

    # Put solution into superposition
    qc.h(qr_shots[:] + qr_address[:])

    qc.barrier()

    # Load game gate
    game_qubits = qr_shots[:] + qr_address[:] + qr_cluster[:] + qr_extra[:]

    game_gate = game_logic_oracle_opt(
        qr_shots=qr_shots,
        qr_address=qr_address,
        qr_cluster=qr_cluster,
        qr_extra=qr_extra,
        prob_set=problem_set,
    )

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

    qc.measure(qr_shots, cr_shots)

    ######

    backend = Aer.get_backend("qasm_simulator")
    tic = time.perf_counter()
    job = execute(
        qc, backend=backend, shots=200, backend_options={"fusion_enable": True},
    )

    result = job.result()
    count = result.get_counts()

    for k, v in count.items():
        print(k, v)

    toc = time.perf_counter()

    print(f"Circuit executed in {toc - tic:0.4f} seconds")

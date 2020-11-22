from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import Aer, execute
import numpy as np

# provider = IBMQ.load_account()

from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import Unroller


def calculate_score(qc):
    pass_ = Unroller(["u3", "cx"])
    pm = PassManager(pass_)
    new_circuit = pm.run(qc)
    count_dict = new_circuit.count_ops()

    return count_dict["u3"] + count_dict["cx"] * 10, count_dict


def get_lightsout4_as_qram(lightsout4, invert_bits=True):

    address = QuantumRegister(2, name="addr")
    data = QuantumRegister(9, name="data")
    qc = QuantumCircuit(address, data)

    # Invert bits if needed
    if invert_bits:
        lightsout4 = [[(item + 1) % 2 for item in row] for row in lightsout4]

    # Load data
    for i, addr in enumerate(["00", "01", "10", "11"]):

        # Set address bits
        if addr[0] == "0":
            qc.x(address[0])
        if addr[1] == "0":
            qc.x(address[1])

        # Write data
        for j, bit in enumerate(lightsout4[i]):
            if bit == 1:
                qc.ccx(address[0], address[1], data[j])

        # Reset address bits
        if addr[0] == "0":
            qc.x(address[0])
        if addr[1] == "0":
            qc.x(address[1])

    # Convert to gate and return
    load_qram = qc.to_gate()
    load_qram.name = "Load_qRAM"
    return load_qram


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


def get_rot_about_oracle(qr_soln, qr_addr, qr_data, qr_coun, qr_ancl, counting_qubits):

    qc = QuantumCircuit(qr_soln, qr_addr, qr_data, qr_coun, qr_ancl)

    connections = [
        [0, 1, 3],
        [0, 1, 2, 4],
        [1, 2, 5],
        [0, 3, 4, 6],
        [1, 3, 4, 5, 7],
        [2, 4, 5, 8],
        [3, 6, 7],
        [4, 6, 7, 8],
        [5, 7, 8],
    ]

    # Append logic for game
    for i, box in enumerate(connections):
        for connection in box:
            qc.cx(qr_soln[i], qr_data[connection])

    # Append counting logic
    # Prepare an equisuperposition state for soln qubits
    qc.h(qr_coun)

    for q_soln in qr_soln:
        for i, q_coun in enumerate(qr_coun):
            # For each less significant qubit, we need to do a
            # smaller-angled controlled rotation:
            qc.cp(np.pi / 2 ** (len(qr_coun) - i - 1), q_soln, q_coun)

    qc.append(qft_dagger(counting_qubits), qargs=qr_coun)

    # Mark the desired state: 3 or less = 00**
    qc.x(qr_coun[2:])

    # Check for solution
    qc.mct(qr_data[:] + qr_coun[2:], qr_ancl)

    # Unmark the desired state: 3 or less = 00**
    qc.x(qr_coun[2:])

    # Uncompute counting logic
    qc.append(qft_dagger(counting_qubits).inverse(), qargs=qr_coun)

    for q_soln in qr_soln:
        for i, q_coun in enumerate(qr_coun):
            # For each less significant qubit, we need to do a
            # smaller-angled controlled rotation:
            qc.cp(-np.pi / 2 ** (len(qr_coun) - i - 1), q_soln, q_coun)

    qc.h(qr_coun)

    # Uncompute logic for game
    for i, box in enumerate(reversed(connections)):
        for connection in reversed(box):
            qc.cx(qr_soln[i], qr_data[connection])

    # Convert to gate and return
    rot_oracle = qc.to_gate()
    rot_oracle.name = "Rot_Oracle"
    return rot_oracle


def add_rot_about_equisuperpos(qc, qubits):

    qc.h(qubits)
    qc.x(qubits)
    qc.h(qubits[-1])
    qc.mct(qubits[:-1], qubits[-1])
    qc.h(qubits[-1])
    qc.x(qubits)
    qc.h(qubits)

    return qc


def week2b_ans_func(lightsout4):
    # Build your circuit here
    #  In addition, please make sure your function can solve the problem with
    # different inputs (lightout4). We will cross validate with different inputs.
    counting_qubits = 4

    # We will have many quantum registers.
    qr_soln = QuantumRegister(9, name="soln")  # One for the solution part of the oracle
    qr_addr = QuantumRegister(2, name="addr")  # One for the address part of qRAM
    qr_data = QuantumRegister(9, name="data")  # One for data part of qRAM
    qr_coun = QuantumRegister(counting_qubits, name="count")
    qr_ancl = QuantumRegister(1, name="ancl")  # One working qubit for Grover's Alg

    cr_addr = ClassicalRegister(2, name="addr_c")

    # qc = QuantumCircuit(qr_soln, qr_addr, qr_data, qr_coun, qr_ancl, cr_soln, cr_addr, cr_data)
    qc = QuantumCircuit(qr_soln, qr_addr, qr_data, qr_coun, qr_ancl, cr_addr)

    # Put address and solution qubits into superposition
    qc.h(qr_soln)
    qc.h(qr_addr)

    # Prepare the ancilla qubit
    qc.x(qr_ancl)
    qc.h(qr_ancl)
    qc.barrier()

    # Load commonly used gates:
    qram_gate = get_lightsout4_as_qram(lightsout4)
    oracle_gate = get_rot_about_oracle(
        qr_soln, qr_addr, qr_data, qr_coun, qr_ancl, counting_qubits=4
    )

    qc.append(qram_gate, qr_addr[:] + qr_data[:])

    num_iterations = 15
    for i in range(num_iterations):

        # Perform qRAM operation
        # qc.append(qram_gate, qr_addr[:] + qr_data[:])

        # Perform rotation about solution state
        qc.append(
            oracle_gate, qr_soln[:] + qr_addr[:] + qr_data[:] + qr_coun[:] + qr_ancl[:]
        )

        # Reverse qRAM operation
        # qc.append(qram_gate.inverse(), qr_addr[:] + qr_data[:])

        # Perform rotation about equisuperposition state
        qc = add_rot_about_equisuperpos(qc, qr_soln[:] + qr_addr[:])

        qc.barrier()

    qc.measure(qr_addr, cr_addr)
    # qc.measure(qr_data, cr_data)
    qc = qc.reverse_bits()

    return qc


if __name__ == "__main__":

    lightsout4 = [
        [1, 1, 1, 0, 0, 0, 1, 0, 0],
        [1, 0, 1, 0, 0, 0, 1, 1, 0],
        [1, 0, 1, 1, 1, 1, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 1, 0, 0],
    ]

    # Pushes Q1:[1,4,5,6], Q2[5,6,2,4], Q3:[6,5,4,3]
    Q1 = [
        [0, 0, 0, 0, 0, 1, 0, 1, 1],
        [0, 1, 0, 1, 0, 1, 0, 1, 0],
        [0, 1, 1, 1, 0, 1, 0, 1, 0],
        [1, 1, 1, 0, 1, 0, 1, 1, 0],
        "00",
    ]
    Q2 = [
        [1, 0, 1, 1, 0, 1, 0, 0, 1],
        [0, 1, 0, 0, 0, 1, 1, 1, 1],
        [0, 1, 1, 1, 0, 0, 1, 0, 0],
        [1, 0, 0, 1, 0, 0, 1, 0, 0],
        "10",
    ]
    Q3 = [
        [0, 0, 0, 0, 1, 1, 0, 0, 1],
        [0, 1, 0, 1, 1, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 1, 0, 1],
        "11",
    ]

    lightsout4 = Q2[:-1]

    # Reverse the output string.
    qc = week2b_ans_func(lightsout4=lightsout4)

    # backend = provider.get_backend('ibmq_qasm_simulator')
    backend = Aer.get_backend("qasm_simulator")
    job = execute(
        qc,
        backend=backend,
        shots=3000,
        seed_simulator=12345,
        backend_options={"fusion_enable": True},
    )
    # job = execute(qc, backend=backend, shots=8192)
    result = job.result()
    count = result.get_counts()
    print(count)

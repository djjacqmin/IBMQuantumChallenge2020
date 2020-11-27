from qiskit import QuantumRegister, QuantumCircuit, ClassicalRegister, execute, Aer
import numpy as np


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


def count_oracle(
    qr_count_me: QuantumRegister, qr_counter: QuantumRegister, return_gate: bool = True,
):
    """ Creates a gate/circuit that counts the number of 1's in
    qr_count_me and writes to qr_counter

    ----------
    PARAMETERS
    ----------
    qr_count_me:
        A quantum register whose 1's will be counted
    qr_counter:
        A quantum register that will record the count
    return_gate:
        Returns gate if true, quantum circuit if false.

    -------
    RETURNS
    -------
    A gate or quantum circuit that counts qr_count_me and writes to qr_counter

    """

    qc = QuantumCircuit(qr_count_me, qr_counter)

    # Step 1: Put the counter into superposition
    qc.h(qr_counter)

    for qubit_count_me in qr_count_me:
        for i, qubit_counter in enumerate(qr_counter):
            # For each less significant qubit, we need to do a
            # smaller-angled controlled rotation:
            qc.cp(np.pi / 2 ** (len(qr_counter) - i - 1), qubit_count_me, qubit_counter)

    qc.append(qft_dagger(len(qr_counter)), qargs=qr_counter)

    if return_gate:
        counter_gate = qc.to_gate()
        counter_gate.name = "Counter"
        return counter_gate
    else:
        return qc


if __name__ == "__main__":

    count_me_size = 8
    counter_size = 4

    qr_count_me = QuantumRegister(count_me_size)
    qr_counter = QuantumRegister(counter_size)

    cr_count_me = ClassicalRegister(count_me_size)
    cr_counter = ClassicalRegister(counter_size)

    qc = QuantumCircuit(qr_count_me, qr_counter, cr_count_me, cr_counter)

    # Put qr_count_me into superposition
    qc.h(qr_count_me)

    counter_gate = count_oracle(
        qr_count_me=qr_count_me, qr_counter=qr_counter, return_gate=True
    )

    qc.append(
        counter_gate, qr_count_me[:] + qr_counter[:],
    )

    qc.measure(qr_count_me, cr_count_me)
    qc.measure(qr_counter, cr_counter)

    backend = Aer.get_backend("qasm_simulator")
    job = execute(qc, backend=backend, shots=2000,)

    result = job.result()
    count = result.get_counts()

    for k, v in count.items():
        print(k, v)

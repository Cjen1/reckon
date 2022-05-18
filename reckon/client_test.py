from typing import cast, IO, Tuple, List, Any, Union
from threading import Thread
import shlex

import subprocess as sp

import reckon.reckon_types as t
import reckon.client_runner as cr


def spawn(command: List[str]) -> Tuple[t.Client, sp.Popen[bytes]]:
    p = sp.Popen(command, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    return t.Client(cast(IO[bytes], p.stdin), cast(IO[bytes], p.stdout), "Test"), p


def check_alive(p: sp.Popen[Any]) -> bool:
    if p.poll():
        return False
    else:
        return True


class DummyWorkload(t.AbstractWorkload):
    def __init__(self, client):
        self.client = client
        self._clients = [client]

    @property
    def prerequisites(self):
        return [
            t.Operation(
              time=-1,
              payload=t.Write(
                kind=t.OperationKind.Write, key="preload", value="preload"
                ),
              )
            for _ in range(3)
        ]

    @property
    def workload(self):
        i = 0
        while True:
            yield (
                self.client,
                (
                    t.Operation(
                        time=i,
                        payload=t.Write(kind=t.OperationKind.Write, key="k", value="v"),
                    )
                    if i % 2 == 0
                    else t.Operation(
                        time=i, payload=t.Read(kind=t.OperationKind.Read, key="k")
                    )
                ),
            )
            i += 1


class CannedClient(t.Client):
    def __init__(self, canned_output: str):
        self._sent_messages: List[t.Message] = []
        cat = sp.Popen(f"cat {canned_output}", stdout=sp.PIPE, shell=True)
        self.stdout = cat.stdout
        self.id = "pseudoclient"

    def send(self, msg: t.Message):
        self._sent_messages.append(msg)

    @property
    def sent_messages(self) -> List[t.Message]:
        return self._sent_messages


def client_bootstrap(input_file, output_file):
    with open(input_file, "wb") as f_in:
        cat = sp.Popen(f"cat {output_file}", stdout=sp.PIPE, shell=True)
        c = t.Client(f_in, cat.stdout, "test")  # type: ignore
        results = cr.test_steps([c], DummyWorkload(c), [], 10)
        print(results)


class TaggedFailure(t.AbstractFailureGenerator):
    def __init__(self):
        self.failures = []

    def get_failures(self, net, system, restarters, stoppers) -> List[t.AbstractFault]:
        del net, system, restarters, stoppers  # unused

        class failure(t.AbstractFault):
            def __init__(self, parent, id):
                self._id = id
                self.parent = parent

            @property
            def id(self) -> str:
                return self._id

            def apply_fault(self):
                self.parent.failures.append(self.id)

        return [failure(self, 1), failure(self, 2)]


def test_client_runner():
    canned_output_file = "scripts/out.bin"
    expected_input_file = "scripts/in.bin"

    c_out = CannedClient(canned_output_file)
    fault = TaggedFailure()
    results = cr.test_steps(
        [c_out], DummyWorkload(c_out), fault.get_failures(1, 2, 3, 4), 10
    )

    # Test if the sent messages are as expected
    c_in = CannedClient(expected_input_file)
    expected_sent_messages: List[t.Message] = []
    try:
        while True:
            msg = c_in.recv()
            expected_sent_messages.append(msg)
    except EOFError:
        pass

    assert c_out.sent_messages == expected_sent_messages

    # Test if the results are as expected
    results = results.__root__
    assert len(results) == 11
    assert all([r.result == "Success" for r in results])
    assert len([r for r in results if r.op_kind == t.OperationKind.Write]) == 6
    assert len([r for r in results if r.op_kind == t.OperationKind.Read]) == 5

    # Test if the faults were applied in the right order
    assert fault.failures == [1, 2]

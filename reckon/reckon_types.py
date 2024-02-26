from enum import Enum
from typing import Union, Tuple, List, Iterator, Any, NewType, Dict, Callable, IO
from typing_extensions import Literal
import logging
from struct import pack, unpack
from abc import ABC, abstractproperty, abstractmethod
from selectors import EVENT_READ, EVENT_WRITE, BaseSelector, SelectorKey
import time
import os
import shlex
import threading

from mininet.net import Mininet
from mininet.node import Host
from pydantic import BaseModel, Field


class OperationKind(str, Enum):
    Write = "write"
    Read = "read"

    def __str__(self):
        return self.value


class Write(BaseModel):
    kind: Literal[OperationKind.Write]
    key: str
    value: str


class Read(BaseModel):
    kind: Literal[OperationKind.Read]
    key: str


class Operation(BaseModel):
    payload: Union[Write, Read] = Field(..., descriminator="kind")
    time: float


class Preload(BaseModel):
    kind: Literal["preload"]
    prereq: bool
    operation: Operation


class Finalise(BaseModel):
    kind: Literal["finalise"]


class Ready(BaseModel):
    kind: Literal["ready"]


class Start(BaseModel):
    kind: Literal["start"]


class Result(BaseModel):
    kind: Literal["result"]
    t_submitted: float
    t_result: float
    result: str
    op_kind: OperationKind
    clientid: str
    other: dict


class Finished(BaseModel):
    kind: Literal["finished"]


class Message(BaseModel):
    __root__: Union[Preload, Finalise, Ready, Start, Result, Finished] = Field(
        ..., discriminator="kind"
    )


class Client(object):
    def __init__(self, p_in: IO[bytes], p_out: IO[bytes], id: str):
        self.stdin = p_in
        self.stdout = p_out
        self.id = id

    def _send_packet(self, payload: str):
        size = pack("<l", len(payload))  # Little endian signed long (4 bytes)
        self.stdin.write(size + bytes(payload, "ascii"))

    def _recv_packet(self) -> str:
        size = self.stdout.read(4)
        if size:
            size = unpack("<l", bytearray(size))  # Little endian signed long (4 bytes)
            payload = self.stdout.read(size[0])
            return str(payload, "ascii")
        else:
            logging.error(f"Tried to recv from |{self.id}|, received nothing")
            raise EOFError

    def send(self, msg: Message):
        payload = msg.json()
        self._send_packet(payload)
        self.stdin.flush()

    def recv(self) -> Message:
        pkt = self._recv_packet()
        return Message.parse_raw(pkt)

    def register_selector(self, s: BaseSelector, e: Any, data: Any) -> SelectorKey:
        if e == EVENT_READ:
            return s.register(self.stdout, e, data)
        if e == EVENT_WRITE:
            return s.register(self.stdin, e, data)
        raise KeyError()

    def unregister_selector(self, s: BaseSelector, e: Any) -> SelectorKey:
        if e == EVENT_READ:
            return s.unregister(self.stdout)
        if e == EVENT_WRITE:
            return s.unregister(self.stdin)
        raise KeyError()

class RedirectClient(Client):
    def __init__(self, file, p_in: IO[bytes], p_out: IO[bytes], id: str):
        self.file = open(file, "bw")
        super().__init__(p_in, p_out, id)

    def _send_packet(self, payload: str):
        size = pack("<l", len(payload))  # Little endian signed long (4 bytes)
        self.stdin.write(size + bytes(payload, "ascii"))
        self.file.write(size + bytes(payload, "ascii"))

WorkloadOperation = Tuple[Client, Operation]


class Results(BaseModel):
    __root__: List[Result]

class AbstractKeyGenerator(ABC):
    @abstractproperty
    def prerequisites(self) -> List[Write]:
        return []

    @abstractproperty
    def workload(self) -> Iterator[Union[Read, Write]]:
        """
        Returns an iterator through the workload from time = 0

        The time for each operation strictly increases.
        """
        return iter([])


class AbstractArrivalProcess(ABC):
    @abstractproperty
    def arrival_times(self) -> Iterator[float]:
        return iter([])

class AbstractWorkload(ABC):
    @property
    def clients(self):
        return self._clients

    @clients.setter
    def clients(self, value):
        self._clients = value

    @abstractproperty
    def prerequisites(self) -> List[Operation]:
        return []

    @abstractproperty
    def workload(self) -> Iterator[WorkloadOperation]:
        """
        Returns an iterator through the workload from time = 0

        The time for each operation strictly increases.
        """
        return iter([])


# Helper constructors
def preload(prereq: bool, operation: Operation) -> Message:
    return Message(
        __root__=Preload(kind="preload", prereq=prereq, operation=operation),
    )


def finalise() -> Message:
    return Message(__root__=Finalise(kind="finalise"))


def ready() -> Message:
    return Message(__root__=Ready(kind="ready"))


def start() -> Message:
    return Message(__root__=Start(kind="start"))


def result(
    t_s: float, t_r: float, result: str, kind: OperationKind, clientid: str, other: dict
) -> Message:
    return Message(
        __root__=Result(
            kind="result",
            t_submitted=t_s,
            t_result=t_r,
            result=result,
            op_kind=kind,
            clientid=clientid,
            other=other,
        )
    )


MininetHost = NewType("MininetHost", Host)


class AbstractClient(ABC):
    @abstractmethod
    def cmd(self, ips: List[str], client_id: str) -> str:
        pass

class AbstractSystem(ABC):
    def __init__(self, args):
        ctime = time.localtime()
        creation_time = time.strftime("%H:%M:%S", ctime)

        self.system_type = args.system_type
        self.log_location = args.system_logs
        if not os.path.exists(args.system_logs):
            os.makedirs(args.system_logs)
        self.creation_time = creation_time
        self.client_class = self.get_client(args)
        self.client_type = args.client
        self.data_dir = args.data_dir
        self.failure_timeout = args.failure_timeout
        self.delay_interval = args.delay_interval

        super(AbstractSystem, self).__init__()

    def __str__(self):
        return "{0}-{1}".format(self.system_type, self.client_type)

    def get_client_tag(self, host: MininetHost):
        return "mc_" + host.name

    def get_node_tag(self, host: MininetHost):
        return "node_" + host.name

    def start_screen(self, host: MininetHost, command: str):
        FNULL = open(os.devnull, "w")
        quotedcommand = command.translate(str.maketrans({"\\": r"\\", "\"": r"\""})) # Quote all speech marks
        cmd = 'screen -dmS {tag} bash -c "{command}"'.format(
            tag=self.get_node_tag(host), command=quotedcommand
        )
        print("Starting screen on {0} with cmd: {1}".format(host.name, cmd))
        host.popen(shlex.split(cmd), stdout=FNULL, stderr=FNULL)

    def kill_screen(self, host: MininetHost):
        cmd = ("screen -X -S {0} quit").format(self.get_node_tag(host))
        logging.debug("Killing screen on host {0} with cmd {1}".format(host.name, cmd))
        host.cmd(shlex.split(cmd))

    def add_stderr_logging(self, cmd: str, tag: str):
        time = self.creation_time
        log = self.log_location
        return f"{cmd} 2> {log}/{time}_{tag}.err"

    def add_stdout_logging(self, cmd: str, tag: str):
        time = self.creation_time
        log = self.log_location
        return f"{cmd} > {log}/{time}_{tag}.out"

    def add_tee_stdout_logging(self, cmd: str, tag: str):
        time = self.creation_time
        log = self.log_location
        return f"{cmd} | tee {log}/{time}_{tag}.out"

    def add_tee_stdin_logging(self, cmd: str, tag: str):
        time = self.creation_time
        log = self.log_location
        return f"tee {log}/{time}_{tag}.in | {cmd}"

    @abstractmethod
    def stat(self, host: MininetHost) -> str:
        pass

    @abstractmethod
    def get_client(self, args) -> AbstractClient:
        pass

    @abstractmethod
    def start_nodes(
        self, cluster: List[MininetHost]
    ) -> Tuple[Dict[Any, Callable[[], None]], Dict[Any, Callable[[], None]]]:
        pass

    @abstractmethod
    def start_client(
        self, client: MininetHost, client_id: str, cluster: List[MininetHost]
    ) -> Client:
        pass

    @abstractmethod
    def get_leader(self, cluster: List[MininetHost]) -> MininetHost:
        return None


class AbstractFault(ABC):
    def id(self) -> str:
        return "Generic Fault"

    @abstractmethod
    def apply_fault(self):
        pass


class NullFault(AbstractFault):
    def id(self):
        return ""

    def apply_fault(self):
        pass


class AbstractFailureGenerator(ABC):
    @abstractmethod
    def get_failures(
        self,
        cluster: List[MininetHost],
        system: AbstractSystem,
        restarters: Dict[Any, Callable[[], None]],
        stoppers: Dict[Any, Callable[[], None]],
    ) -> List[AbstractFault]:
        pass


class AbstractTopologyGenerator(ABC):
    @abstractmethod
    def setup(self) -> Tuple[Mininet, List[MininetHost], List[MininetHost]]:
        pass


class ThreadWithResult(threading.Thread):
    def __init__(
        self, group=None, target=None, name=None, args=(), kwargs={}, *, daemon=None
    ):
        self._result: Any = None

        def function():
            if target:
                self._result = target(*args, **kwargs)

        super().__init__(group=group, target=function, name=name, daemon=daemon)

    @property
    def result(self) -> Any:
        return self._result

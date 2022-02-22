from enum import Enum
from typing import Union, Tuple, List, Iterator, Any, NewType, Dict, Callable
import logging
from struct import pack, unpack
from abc import ABC, abstractproperty, abstractmethod
from selectors import EVENT_READ, EVENT_WRITE, BaseSelector, SelectorKey
import time
import os
import shlex

from pydantic import BaseModel

class OperationKind(Enum):
    Write = "write"
    Read = "read"
    def __str__(self):
        return self.value

class Write(BaseModel):
    key: str
    value: str

class Read(BaseModel):
    key: str

class Operation(BaseModel):
    kind: OperationKind
    payload: Union[Write, Read]
    time: float

class MessageKind(Enum):
    Preload = "preload"
    Finalise = "finalise"
    Ready = "ready"
    Start = "start"
    Result = "result"
    Finished = "finished"
    def __str__(self):
        return self.value

class Preload(BaseModel):
    prereq: bool
    operation: Operation

class Finalise(BaseModel):
    pass
class Ready(BaseModel):
    pass
class Start(BaseModel):
    pass
class Result(BaseModel):
    t_submitted: float
    t_result: float
    result: str
    kind: Union[Write, Read]
    other: dict
class Finished(BaseModel):
    pass

class Message(BaseModel):
    kind: MessageKind
    payload: Union[Preload, Finalise, Ready, Start, Result, Finished]

class Client(object):
    def __init__(self, p_in, p_out, id):
        self.stdin = p_in
        self.stdout = p_out
        self.id = id

    def send_packet(self, payload: str):
        size = pack("<l", len(payload)) # Little endian signed long (4 bytes)
        self.stdin.write(str(size) + payload)
    
    def recv_packet(self) -> str:
        size = self.stdout.read(4)
        if size:
            size = unpack("<l", size) # Little endian signed long (4 bytes)
            payload = self.stdout.read(size[0])
            return payload
        else:
            logging.error(f"Tried to recv from |{self.id}|, received nothing")
            raise EOFError

    def send(self, msg: Message):
        payload = msg.json()
        self.send_packet(payload)

    def recv(self) -> Message:
        pkt = self.recv_packet()
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

WorkloadOperation = Tuple[Client, Operation]

class Results(BaseModel):
    responses: List[Result]

class AbstractWorkload(ABC):
    @property
    def clients(self):
        return self._clients

    @clients.setter
    def clients(self, value):
        self._clients = value

    @abstractproperty
    def prerequisites(self) -> List[WorkloadOperation]:
        return []

    @abstractmethod
    def workload(self) -> Iterator[WorkloadOperation]:
        """
        Returns an iterator through the workload from time = 0

        The time for each operation strictly increases.
        """
        return iter([])

# Helper constructors
def preload(prereq : bool, operation : Operation) -> Message:
    return Message(
            kind = MessageKind.Preload,
            payload = Preload(
                prereq= prereq,
                operation= operation),
            )

def finalise() -> Message:
    return Message(
            kind = MessageKind.Finalise,
            payload = Finalise()
            )

def ready() -> Message:
    return Message(
            kind = MessageKind.Ready,
            payload = Ready()
            )

def start() -> Message:
    return Message(
            kind = MessageKind.Start,
            payload = Start()
            )

def result(t_s: float, t_r: float, result: str, kind: Union[Write, Read], other: dict) -> Message:
    return Message(
            kind = MessageKind.Result,
            payload = Result(
                t_submitted=t_s,
                t_result=t_r,
                result=result,
                kind=kind,
                other=other
                )
            )

class AbstractFault(ABC):
    @abstractproperty
    def id(self) -> str:
        return ""

    @abstractmethod
    def apply_fault(self):
        pass

class NullFault(AbstractFault):
    def id(self):
        return ""

    def apply_fault(self):
        pass

MininetHost = NewType("MininetHost", Any)

class AbstractClient(ABC):
    @abstractmethod
    def cmd(self, ips: List[str], client_id: Any):
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
        super(AbstractSystem, self).__init__()

    def __str__(self):
        return "{0}-{1}".format(self.system_type, self.client_type)

    def get_client_tag(self, host: MininetHost):
        return "mc_" + host.name

    def get_node_tag(self, host: MininetHost):
        return "node_" + host.name

    def start_screen(self, host: MininetHost, command: str):
        FNULL = open(os.devnull, "w")
        cmd = 'screen -dmS {tag} bash -c "{command}"'.format(
            tag=self.get_node_tag(host), command=command
        )
        logging.debug("Starting screen on {0} with cmd {1}".format(host.name, cmd))
        host.popen(shlex.split(cmd), stdout=FNULL, stderr=FNULL)

    def kill_screen(self, host: MininetHost):
        cmd = ("screen -X -S {0} quit").format(self.get_node_tag(host))
        logging.debug("Killing screen on host {0} with cmd {1}".format(host.name, cmd))
        host.cmd(shlex.split(cmd))

    def add_logging(self, cmd: str, tag: str):
        return cmd + " 2>&1 | tee -a {log}/{time_tag}_{tag}".format(
            log=self.log_location, tag=tag, time_tag=self.creation_time
        )

    @abstractmethod
    def get_client(self, args) -> AbstractClient:
        pass

    @abstractmethod
    def start_nodes(self, cluster: List[MininetHost]) -> Tuple[Dict[Any, Callable[[], None]], Dict[Any, Callable[[], None]]]:
        pass

    @abstractmethod
    def start_client(self, client: MininetHost, client_id: Any, cluster: List[MininetHost]) -> Client:
        pass

    @abstractmethod
    def get_leader(self, cluster: List[MininetHost]) -> MininetHost:
        return None

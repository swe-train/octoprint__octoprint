from typing import Dict

from octoprint.schema import BaseModel


class StateFlags(BaseModel):
    operational: bool = False
    printing: bool = False
    cancelling: bool = False
    pausing: bool = False
    resuming: bool = False
    finishing: bool = False
    closedOrError: bool = False
    error: bool = False
    paused: bool = False
    ready: bool = False
    sdReady: bool = False


class PrinterState(BaseModel):
    text: str = None
    flags: StateFlags = StateFlags()
    error: str = None


class FileInfo(BaseModel):
    name: str = None
    path: str = None
    size: int = None
    origin: str = None
    date: int = None


class FilamentInfo(BaseModel):
    length: float = None
    volume: float = None


class JobData(BaseModel):
    file: FileInfo = None
    estimatedPrintTime: float = None
    lastPrintTime: float = None
    filament: FilamentInfo = None
    user: str = None

    def update(self, other):
        if not isinstance(other, JobData):
            return

        if other.file is not None:
            self.file = other.file
        if other.estimatedPrintTime is not None:
            self.estimatedPrintTime = other.estimatedPrintTime
        if other.lastPrintTime is not None:
            self.lastPrintTime = other.lastPrintTime
        if other.filament is not None:
            self.filament = other.filament
        if other.user is not None:
            self.user = other.user


class JobProgress(BaseModel):
    completion: float = None
    filepos: float = None
    printTime: float = None
    printTimeLeft: float = None
    printTimeLeftOrigin: str = None


class ResendInfo(BaseModel):
    count: int = 0
    transmitted: int = 0
    ratio: float = 0.0


class CurrentData(BaseModel):
    state: PrinterState = PrinterState()
    job: JobData = JobData()
    currentZ: float = 0.0
    progress: JobProgress = JobProgress()
    offsets: Dict[str, float] = {}
    resends: ResendInfo = ResendInfo()

    def reset(self, state: PrinterState = None):
        if state is None:
            state = PrinterState()
        self.state = state
        self.job = JobData()
        self.currentZ = 0.0
        self.progress = JobProgress()
        self.offsets = {}
        self.resends = ResendInfo()

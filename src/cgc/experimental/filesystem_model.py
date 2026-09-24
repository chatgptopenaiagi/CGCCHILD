"""Finite action-scoped filesystem closure MODEL; no live observer or proof producer."""
from dataclasses import dataclass
import re
from .quiescence import Truth, MAX_TTL_NS

CHANNELS = ('WINDOWS_HOST','LINUX_DOMAIN','OTHER_LINUX_PEERS','OTHER_WSL',
            'CONTAINER_OR_NETWORK','ALIASES','PREOPENED_DESCRIPTORS','DEPUTIES','QUEUED_IO')
BASE = ('WORKTREE','INDEX','REFS','OBJECTS','CONFIG','OPERATIONS','HANDOFF_STORE')
DOMAINS = BASE+('TEST_INPUTS','TEST_OUTPUTS','DESTINATION_OBJECTS','DESTINATION_REFS','DESTINATION_CONFIG')
SCOPES = {
    'READ_ONLY_ANALYSIS': (),
    'CONTINUE_EDITING': BASE,
    'RUN_TESTS': BASE+('TEST_INPUTS','TEST_OUTPUTS'),
    'CREATE_CHECKPOINT': BASE,
    'PUBLISH_CHECKPOINT': BASE+('DESTINATION_OBJECTS','DESTINATION_REFS','DESTINATION_CONFIG'),
    'REPAIR_KNOWN_FAILURE': (),
}
MAX_CELLS = len(DOMAINS)*len(CHANNELS)


def _label(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',value) is not None


def required_cells(action):
    if type(action) is not str or action not in SCOPES:raise ValueError('INVALID_ACTION')
    return tuple((domain,channel) for domain in SCOPES[action] for channel in CHANNELS)


@dataclass(frozen=True)
class Cell:
    domain: str
    channel: str
    status: Truth

    def __post_init__(self):
        if (type(self.domain) is not str or type(self.channel) is not str
                or self.domain not in DOMAINS or self.channel not in CHANNELS or type(self.status) is not Truth):
            raise ValueError('INVALID_CELL')


@dataclass(frozen=True)
class Model:
    project: str
    generation: str
    action: str
    observed_ns: int
    expires_ns: int
    cells: tuple
    provenance: str = 'SYNTHETIC'

    def __post_init__(self):
        if not _label(self.project) or not _label(self.generation):raise ValueError('INVALID_SCOPE')
        required=required_cells(self.action)
        if any(type(n) is not int for n in (self.observed_ns,self.expires_ns)):
            raise ValueError('INVALID_CLOCK')
        if not 0<=self.observed_ns<=self.expires_ns<(1<<63) or self.expires_ns-self.observed_ns>MAX_TTL_NS:
            raise ValueError('INVALID_CLOCK')
        if type(self.provenance) is not str or self.provenance not in ('SYNTHETIC','IMPORTED'):
            raise ValueError('NO_LIVE_FILESYSTEM_ADAPTER')
        if type(self.cells) is not tuple or len(self.cells)>MAX_CELLS or any(type(c) is not Cell for c in self.cells):
            raise ValueError('INVALID_CELLS')
        keys=tuple((c.domain,c.channel) for c in self.cells)
        if len(set(keys))!=len(keys) or keys!=tuple(k for k in required if k in keys):
            raise ValueError('DUPLICATE_UNORDERED_OR_OUT_OF_SCOPE_CELL')


@dataclass(frozen=True)
class Result:
    model_filesystem: str
    production_filesystem: Truth
    production_p3: Truth
    mutation_authorized: bool
    missing: tuple
    contradicted: tuple
    reasons: tuple


def assess(model, *, project, generation, action, now_ns):
    if type(model) is not Model or not _label(project) or not _label(generation):
        raise ValueError('INVALID_ASSESSMENT')
    required_cells(action)
    if type(now_ns) is not int or not 0<=now_ns<(1<<63):raise ValueError('INVALID_CLOCK')
    values={(c.domain,c.channel):c.status for c in model.cells}
    missing=tuple(k for k in required_cells(model.action) if values.get(k,Truth.UNKNOWN) is Truth.UNKNOWN)
    contradicted=tuple(k for k in required_cells(model.action) if values.get(k) is Truth.NO)
    reasons=[]
    if (model.project,model.generation,model.action)!=(project,generation,action):reasons.append('SCOPE_MISMATCH')
    if not model.observed_ns<=now_ns<model.expires_ns:reasons.append('STALE_OR_FUTURE')
    if model.provenance=='IMPORTED':reasons.append('IMPORTED_NOT_CURRENT')
    if reasons:verdict='UNKNOWN'
    elif action=='REPAIR_KNOWN_FAILURE':verdict='UNKNOWN';reasons.append('UNSUPPORTED_REPAIR_SCOPE')
    elif action=='READ_ONLY_ANALYSIS':verdict='NOT_APPLICABLE'
    elif contradicted:verdict='NO';reasons.append('MODEL_UNCLOSED_ACCESS_ROUTE')
    elif missing:verdict='UNKNOWN';reasons.append('MODEL_MISSING_ROUTE_COVERAGE')
    else:verdict='YES'
    return Result(verdict,Truth.UNKNOWN,Truth.UNKNOWN,False,missing,contradicted,
                  tuple(reasons)+('NO_ACCEPTED_FILESYSTEM_ADAPTER',))

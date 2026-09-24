"""Pure bounded quiescence model. No observer, live producer or mutation adapter.

Even a complete synthetic profile cannot create production evidence. Keeping the
model result separate permits adversarial integration tests without forging P3.
"""
from dataclasses import dataclass
from enum import Enum


class Truth(str, Enum):
    YES = 'YES'
    NO = 'NO'
    UNKNOWN = 'UNKNOWN'


OBLIGATIONS = ('launch_identity', 'controller_continuity', 'closed_admission',
               'domain_empty', 'filesystem_exclusive', 'epoch_current')
MAX_TTL_NS = 60_000_000_000


@dataclass(frozen=True)
class Claim:
    obligation: str
    status: Truth

    def __post_init__(self):
        if self.obligation not in OBLIGATIONS or type(self.status) is not Truth:
            raise ValueError('INVALID_CLAIM')


@dataclass(frozen=True)
class Profile:
    project: str
    generation: str
    observed_ns: int
    expires_ns: int
    claims: tuple
    provenance: str = 'SYNTHETIC'

    def __post_init__(self):
        for value in (self.project, self.generation):
            if type(value) is not str or not 1 <= len(value) <= 128 or not value.isascii() or not all(
                    c.isalnum() or c in '-_.' for c in value):
                raise ValueError('INVALID_SCOPE')
        if any(type(v) is not int for v in (self.observed_ns, self.expires_ns)):
            raise ValueError('INVALID_CLOCK')
        if not 0 <= self.observed_ns <= self.expires_ns <= (1 << 63)-1:
            raise ValueError('INVALID_CLOCK')
        if self.expires_ns-self.observed_ns > MAX_TTL_NS:
            raise ValueError('INVALID_TTL')
        if self.provenance not in ('SYNTHETIC', 'IMPORTED'):
            raise ValueError('NO_LIVE_ADAPTER')
        if type(self.claims) is not tuple or len(self.claims) != len(OBLIGATIONS):
            raise ValueError('INVALID_OBLIGATIONS')
        if any(type(c) is not Claim for c in self.claims) or tuple(c.obligation for c in self.claims) != OBLIGATIONS:
            raise ValueError('INVALID_OBLIGATIONS')


@dataclass(frozen=True)
class Assessment:
    model_result: Truth
    production_p3: Truth
    mutation_authorized: bool
    reasons: tuple


def assess(profile, *, project, generation, now_ns):
    if type(profile) is not Profile or type(now_ns) is not int or not 0 <= now_ns < 1 << 63:
        raise ValueError('INVALID_ASSESSMENT_INPUT')
    reasons = []
    if profile.project != project or profile.generation != generation:
        reasons.append('SCOPE_MISMATCH')
    if not profile.observed_ns <= now_ns < profile.expires_ns:
        reasons.append('STALE_OR_FUTURE')
    if profile.provenance == 'IMPORTED':
        reasons.append('IMPORTED_NOT_CURRENT')
    if reasons:
        result = Truth.UNKNOWN
    elif any(c.status is Truth.NO for c in profile.claims):
        result = Truth.NO
        reasons.append('MODEL_CONTRADICTION')
    elif any(c.status is Truth.UNKNOWN for c in profile.claims):
        result = Truth.UNKNOWN
        reasons.append('MODEL_MISSING_EVIDENCE')
    else:
        result = Truth.YES
    return Assessment(result, Truth.UNKNOWN, False,
                      tuple(reasons)+('NO_ACCEPTED_LIVE_PRODUCER',))

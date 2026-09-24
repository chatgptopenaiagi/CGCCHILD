"""Bounded engineering measurements; synthetic fixtures, no production gate."""
import hashlib
import json
from pathlib import Path
import platform
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from cgc.experimental import snapshot_profiles as profiles,capsule,readonly_service as svc
from cgc.experimental.capsule_chunks import Receiver,CHUNK_BYTES
from test_child_state_protocol import state
from test_child_chunks import large_state


def measure(fn,count):
    durations=[]
    for _ in range(count):
        start=time.perf_counter_ns();fn();durations.append(time.perf_counter_ns()-start)
    return {'iterations':count,'median_ns':int(statistics.median(durations)),
            'min_ns':min(durations),'max_ns':max(durations),'samples_ns':durations}


def transfer(value):
    core=svc.ReadOnlyCore(profiles.encode(value));digest=profiles.digest(value)
    receiver=Receiver(digest);offset=0
    while True:
        request=dict(id='bench',method='capsule.chunk',snapshot_digest=digest,offset=offset)
        out=json.loads(core.dispatch((json.dumps(request,separators=(',',':'))+'\n').encode('ascii')))
        piece=out['result'];receiver.accept(piece)
        if piece['done']:break
        offset+=CHUNK_BYTES
    assert receiver.finish().snapshot()==value


def main():
    result={'scope':'SYNTHETIC_MODEL_AND_CONTINUITY_ONLY','production_accepted':False,
            'python':platform.python_version(),'platform':platform.system(),'machine':platform.machine(),
            'harness_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':{}}
    for name,value in (('model',state()),('continuity_108k',large_state())):
        raw=profiles.encode(value);archive=capsule.export_capsule(value)
        result['cases'][name]={'state_bytes':len(raw),'capsule_bytes':len(archive),
            'snapshot_digest':profiles.digest(value),
            'decode':measure(lambda:profiles.decode(raw),10),
            'capsule_roundtrip':measure(lambda:capsule.import_capsule(capsule.export_capsule(value)),5),
            'core_chunk_transfer':measure(lambda:transfer(value),5)}
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':main()

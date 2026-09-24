"""Read-only retained native source-binding audit; no fixture imports or execution."""
import hashlib,json,re,stat,sys
from pathlib import Path

NAMES=tuple(sorted(('bootstrap','protocol','ancillary','sender','lifecycle','dbus','dbus_encode',
 'filtered_sender','rights_sender','fd_identity','session','bound_session','dbus_auth','dbus_stream',
 'dbus_owner','dbus_connection','dbus_socket','dbus_filtered_socket','dbus_encoded_socket',
 'dbus_query_binding','dbus_bound_socket','effect_session','effect_rejection','atomic_launch','scalar_launch')))
MAX_BYTES=262144
EXPECTED_BINDINGS={
    'scalar_launch':('driver_sha256', 'filter_evidence', 'source_sha256'),
    'atomic_launch':('driver_sha256', 'source_sha256'),
    'ancillary':('driver_sha256', 'payload_prefix_sha256', 'source_sha256'),
    'bootstrap':('source_sha256',),
    'bound_session':('driver_sha256', 'lifecycle_prefix_sha256', 'payload_prefix_sha256', 'socket_types_sha256', 'source_sha256'),
    'dbus':('driver_sha256', 'source_sha256'),
    'dbus_auth':('driver_sha256', 'source_sha256'),
    'dbus_bound_socket':('driver_sha256', 'filter_driver_sha256', 'filter_evidence', 'prefixes_sha256', 'query_source_sha256', 'source_sha256'),
    'dbus_connection':('auth_prefix_sha256', 'decoder_prefix_sha256', 'driver_sha256', 'owner_prefix_sha256', 'source_sha256'),
    'dbus_encode':('driver_sha256', 'source_sha256'),
    'dbus_encoded_socket':('driver_sha256', 'filter_driver_sha256', 'filter_evidence', 'prefixes_sha256', 'query_source_sha256', 'source_sha256'),
    'dbus_filtered_socket':('driver_sha256', 'filter_evidence', 'prefixes_sha256', 'source_sha256'),
    'dbus_owner':('decoder_prefix_sha256', 'driver_sha256', 'source_sha256'),
    'dbus_query_binding':('driver_sha256', 'prefixes_sha256', 'sources_sha256'),
    'dbus_socket':('driver_sha256', 'prefixes_sha256', 'source_sha256'),
    'dbus_stream':('decoder_prefix_sha256', 'driver_sha256', 'source_sha256'),
    'effect_rejection':('driver_sha256', 'lifecycle_prefix_sha256', 'payload_prefix_sha256', 'source_sha256'),
    'effect_session':('driver_sha256', 'lifecycle_prefix_sha256', 'payload_prefix_sha256', 'source_sha256'),
    'fd_identity':('driver_sha256', 'payload_prefix_sha256', 'receive_prefix_sha256', 'source_sha256'),
    'filtered_sender':('driver_sha256', 'payload_prefix_sha256', 'receive_prefix_sha256', 'source_sha256'),
    'lifecycle':('driver_sha256', 'payload_prefix_sha256', 'source_sha256'),
    'protocol':('driver_sha256', 'source_sha256'),
    'rights_sender':('driver_sha256', 'payload_prefix_sha256', 'receive_prefix_sha256', 'source_sha256'),
    'sender':('driver_sha256', 'payload_prefix_sha256', 'receive_prefix_sha256', 'source_sha256'),
    'session':('driver_sha256', 'lifecycle_prefix_sha256', 'payload_prefix_sha256', 'socket_types_sha256', 'source_sha256'),
}
EXPECTED_HEADERS={'dbus_bound_socket': ('auth.h', 'binding.h', 'connection.h', 'decoder.h', 'encoder.h', 'owner.h'), 'dbus_encoded_socket': ('auth.h', 'connection.h', 'decoder.h', 'encoder.h', 'owner.h'), 'dbus_filtered_socket': ('auth.h', 'connection.h', 'decoder.h', 'owner.h'), 'dbus_query_binding': ('decoder.h', 'encoder.h', 'owner.h'), 'dbus_socket': ('auth.h', 'connection.h', 'decoder.h', 'owner.h')}



class AuditError(ValueError):pass


def sha(raw):return hashlib.sha256(raw).hexdigest()


def pairs(items):
    value={}
    for key,item in items:
        if key in value:raise AuditError('DUPLICATE_EVIDENCE_KEY')
        value[key]=item
    return value


def audit_reader(read):
    cache={}
    def data(name):
        if not re.fullmatch(r'[a-z0-9_]+\.(?:c|py|json)',name):raise AuditError('INVALID_FIXED_PATH')
        if name not in cache:
            raw=read(name)
            if type(raw) is not bytes or not 1<=len(raw)<=MAX_BYTES:raise AuditError('ARTIFACT_BOUND')
            cache[name]=raw
        return cache[name]
    def prefix(name,marker):
        raw=data(name)
        if raw.count(marker)!=1:raise AuditError('PREFIX_MARKER')
        return raw.split(marker,1)[0]
    def segment(name,start,end):
        raw=data(name)
        if raw.count(start)!=1 or raw.count(end)!=1:raise AuditError('SEGMENT_MARKER')
        return start+raw.split(start,1)[1].split(end,1)[0]
    def check(raw,expected):
        if type(expected) is not str or not re.fullmatch('[0-9a-f]{64}',expected) or sha(raw)!=expected:
            raise AuditError('DIGEST_MISMATCH')
    prefixes={
      'payload':lambda:prefix('child_protocol.c',b'struct vector {'),
      'decoder':lambda:prefix('child_dbus.c',b'struct vector {'),
      'encoder':lambda:prefix('child_dbus_encode.c',b'struct vector {'),
      'owner':lambda:prefix('child_dbus_owner.c',b'struct step {'),
      'auth':lambda:prefix('child_dbus_auth.c',b'struct uid_vector {'),
      'connection':lambda:prefix('child_dbus_connection.c',b'struct step {'),
      'lifecycle':lambda:prefix('child_lifecycle.c',b'struct step {'),
      'binding':lambda:prefix('child_dbus_query_binding.c',b'struct packet {').replace(b'#include "owner.h"',b'')}
    rows=[]
    for name in NAMES:
        base='child_'+name
        try:
            v=json.loads(data(base+'_evidence.json').decode('utf-8'),object_pairs_hook=pairs)
            if type(v) is not dict:raise AuditError('EVIDENCE_SHAPE')
            binding_keys=tuple(sorted(k for k in v if k in ('source_sha256','sources_sha256','driver_sha256','prefixes_sha256','socket_types_sha256','query_source_sha256','filter_driver_sha256','filter_evidence') or k.endswith('_prefix_sha256')))
            if binding_keys!=EXPECTED_BINDINGS[name]:raise AuditError('BINDING_SET')
            if 'prefixes_sha256' in v:
                if type(v['prefixes_sha256']) is not dict or tuple(sorted(v['prefixes_sha256']))!=EXPECTED_HEADERS[name]:raise AuditError('HEADER_SET')
            checked=[]
            if name=='dbus_query_binding':
                expected_names={'child_dbus_query_binding.c','child_dbus_model_queries.c'}
                if set(v['sources_sha256'])!=expected_names:raise AuditError('SOURCE_SET')
                for source in sorted(expected_names):check(data(source),v['sources_sha256'][source]);checked.append(source)
            else:check(data(base+'.c'),v['source_sha256']);checked.append(base+'.c')
            if name!='bootstrap':check(data(base+'_validate.py'),v['driver_sha256']);checked.append(base+'_validate.py')
            for key,expected in v.items():
                if key.endswith('_prefix_sha256'):
                    kind=key[:-len('_prefix_sha256')]
                    if kind=='receive':
                        raw=segment('child_ancillary.c',b'struct iov {',b'static int inventory(')
                        if name in ('sender','filtered_sender'):
                            raw+=segment('child_ancillary.c',b'static int ancillary(',b'static int exchange(')
                    elif kind in prefixes:raw=prefixes[kind]()
                    else:raise AuditError('UNKNOWN_PREFIX')
                    check(raw,expected);checked.append(key)
            if 'socket_types_sha256' in v:
                check(segment('child_ancillary.c',b'struct iov {',b'static const char packet[]'),v['socket_types_sha256']);checked.append('socket_types_sha256')
            for key,expected in v.get('prefixes_sha256',{}).items():
                if not key.endswith('.h') or key[:-2] not in prefixes:raise AuditError('UNKNOWN_HEADER')
                check(prefixes[key[:-2]](),expected);checked.append(key)
            if 'query_source_sha256' in v:
                query='child_dbus_fixed_queries.c' if name=='dbus_encoded_socket' else 'child_dbus_model_queries.c'
                check(data(query),v['query_source_sha256']);checked.append(query)
            if 'filter_driver_sha256' in v:
                check(data('child_dbus_filtered_socket_validate.py'),v['filter_driver_sha256']);checked.append('filter_driver_sha256')
            if 'filter_evidence' in v:
                check(data('m4_validate.py'),v['filter_evidence']['generator_sha256']);checked.append('filter_generator')
            rows.append(dict(fixture=base,source_bindings='MATCH',checked=checked,
                driver_binding='UNRECORDED' if name=='bootstrap' else 'MATCH',
                generated_and_binary_artifacts='NOT_REBUILT',current_execution='NOT_EXECUTED'))
        except (ValueError,TypeError,KeyError,UnicodeError,RecursionError,OSError) as error:
            code=str(error) if type(error) is AuditError else 'INVALID_OR_MISSING_ARTIFACT'
            raise AuditError(base+':'+code) from None
    return dict(version='cgcchild-native-source-audit-0.1',scope='RETAINED_SOURCE_BINDINGS_ONLY',
                fixtures=rows,files_read=len(cache),production_accepted=False,live_proof='UNKNOWN')


def audit(root):
    def read(name):
        path=root/name
        if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):raise AuditError('NONREGULAR_ARTIFACT')
        with path.open('rb') as handle:return handle.read(MAX_BYTES+1)
    return audit_reader(read)


def main():
    if len(sys.argv)!=1:print('INVALID_AUDIT_ARGUMENTS');return 2
    try:result=audit(Path(__file__).resolve().parent)
    except AuditError as error:print(str(error));return 1
    print(json.dumps(result,sort_keys=True,separators=(',',':')));return 0


if __name__=='__main__':raise SystemExit(main())

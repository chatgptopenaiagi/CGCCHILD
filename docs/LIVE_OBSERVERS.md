# Live continuity observers

CGCCHILD observes one explicitly selected Windows project. Observation never grants
repository mutation authority or establishes filesystem exclusivity. All APIs below
are in `cgcchild.live.observers`; imports perform no observation or process launch.

## Filesystem metadata

`FileObserver(project, max_entries=10000, baseline=None)` uses Windows-native Python
directory enumeration and no-follow metadata reads. `snapshot()` returns relative
paths, size, modification time and filesystem identity. Source contents and source
digests are not collected. Reparse roots/ancestors are refused; encountered junctions,
symlinks and other reparse points are excluded. Credential-related names and selected
dependency/cache directories are excluded. The result reports excluded counts.

`poll()` returns bounded payloads for CREATED, MODIFIED, REMOVED and RENAMED changes.
Rename means an unambiguous sampled nonzero file-identity match; it is not an operating
system event-stream guarantee. Windows `os.stat(..., follow_symlinks=False)` obtains
the identity because `DirEntry.stat()` find-data may contain a zero inode.

The initial poll reports BASELINE_ESTABLISHED. Persist `last_snapshot` outside the
project and pass it as the next process's baseline. The session controller binds the
derived baseline digest to the canonical journal. Missing/untrusted baselines reset
continuity explicitly. Entry/depth/read limits produce PARTIAL coverage; incomplete
samples never establish file removals. Polling can miss edits between samples. Hostile
same-user path races, alias access and production filesystem closure remain UNKNOWN.

## Git observations

`git_snapshot(project, verify_remote=False)` reads HEAD, branch, working-tree/index
status, changed paths, remote names and `origin/main`. `head_object_verified` is true
only after local commit-object resolution and `git cat-file -t` confirmation.
`working_tree_clean` is a boolean for a successful status read and null otherwise.

Git runs with optional writes disabled, no prompt, system/global Git configuration
isolated, hooks and fsmonitor disabled, and finite process/output bounds. Local
configuration is inspected with `--no-includes`; includes, command-valued options,
alternate object stores, linked worktrees, partial clones and unsupported transport
profiles are refused. Remote URLs are not exported. This conservative profile can
return UNKNOWN for an otherwise usable repository.

Remote verification is explicit. Direct HTTPS and ordinary local paths are supported.
`git ls-remote` is the first independent reader. For a strict HTTPS github.com origin,
the supported `gh api` CLI can read the fixed repository main-ref route using its own
existing authentication. CGC does not read authentication files or token values.
SSH/custom helpers and unavailable remote access remain UNKNOWN.

Publication is VERIFIED only when local HEAD, `origin/main` and the independent live
main ref agree. A different live ref is CONTRADICTED. A matching live ref with absent
or stale tracking state is UNKNOWN. No fetch, commit, push or ref update is performed.
Results describe their observation time; they are not permanent publication claims.

Git configuration behavior is grounded in the official
[Git environment documentation](https://git-scm.com/docs/git) and
[Git configuration documentation](https://git-scm.com/docs/git-config).

## Explicit test attempts

`run_test(project, command, framework='unittest', timeout=60)` is an explicit caller
action. Structured agent events cannot dispatch it. Tests execute project code and
may have side effects; the wrapper is not a sandbox. It retains timestamps, duration,
exit status, stream byte counts/SHA256 digests, parsed counts and redacted excerpts.
It does not persist raw terminal transcripts. Excerpts are bounded to 2048 characters
per stream, parser input to 64 KiB and stream processing to 2 MiB per stream. The
requested timeout is positive and no greater than 600 seconds.

Windows `PeekNamedPipe` prevents descendants that retain inherited stdout/stderr from
stranding blocked drain threads. Timeout/output exhaustion terminates only the owned
direct process; descendant containment is false. Incomplete streams yield UNKNOWN
and no complete-stream digest claim.

Built-in parsers cover Python unittest, pytest summaries and Node TAP/spec summaries
commonly produced by npm test. On Windows `npm test` invokes Node's installed
`npm-cli.js` directly rather than constructing a batch command. Unsupported npm
runner output remains TEST_COUNTS_UNKNOWN. Trusted local Python integrations can
register a bounded parser name through `register_test_parser`; events cannot install
parsers or code.

An exit zero without recognized test counts is COMMAND_SUCCESS_TEST_COUNTS_UNKNOWN.
VERIFIED_PASS requires a recognized nonempty summary, zero parsed failures and exit
zero. Output/exit disagreement is CONTRADICTED. These labels corroborate an observed
framework summary, not test adequacy or the authenticity of arbitrary project output.

## Windows acceptance

`tests/test_live_observers.py` exercises real temporary Git repositories and local
bare remotes, index nonmutation, real Windows junction exclusion, persistent baselines,
bounded output/timeouts/inherited pipes, actual unittest and offline npm attempts,
parser results, redaction and the fixed GitHub API route. The engineering session
also verified the child's private GitHub main through its owner-authenticated CLI;
this is remote-ref evidence, not production security acceptance.

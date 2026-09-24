# Executor model

cgcchild.execution.ExecutorInterface takes a closed action and Mode, never a command,
callback, path or imported plan. NullExecutor is the default. DryRunExecutor returns
steps and zero effects. SimulationExecutor requires SIMULATION or DEVELOPER_LAB,
labels synthetic success, and retains production P3 UNKNOWN. LocalExperimentalExecutor
and ProductionExecutorPlaceholder refuse every action.

Preservation, reconciliation, review, reporting, recovery, safe-resume, checkpoint,
publication and verification have plan structures. Mutation/checkpoint/publication/
verification gates remain blocked. Verification plans do not claim a verified result.
Production needs a future accepted adapter and use-time authority, not a JSON flag.

cgcchild.evidence defines Windows provider and writer/alias/cross-runtime/mapping/
metadata contracts. Caller-provided YES components cannot promote production status:
no attestation provider is accepted in this release.

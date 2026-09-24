# SECURITY_ACCEPTANCE_DEBT

Product build is nonblocking; dependent production acceptance remains blocked.
Canonical records: src/cgcchild/resources/security-debt.json.

## FILESYSTEM_EXCLUSIVITY

- **claim**: Complete writer exclusion
- **current_status**: UNKNOWN
- **missing_evidence**: Windows writer inventory, aliases, mappings, metadata, queued IO and cross-runtime closure
- **affected_features**: ["Production mutation"]
- **runtime_consequence**: PRODUCTION_MUTATION_DISABLED
- **safe_fallback**: Read-only analysis / dry-run
- **future_acceptance_test**: Adversarial alias/mapping/metadata writer acceptance
- **blocking_or_nonblocking**: {"product_build": "NONBLOCKING", "production_acceptance": "BLOCKING"}

## PROTECTED_IDENTITIES

- **claim**: Protected controller and worker identity
- **current_status**: UNRESOLVED
- **missing_evidence**: Accepted Windows identity/bootstrap contract
- **affected_features**: ["Privileged executor"]
- **runtime_consequence**: PRODUCTION_MUTATION_DISABLED
- **safe_fallback**: NullExecutor
- **future_acceptance_test**: Independent identity and bootstrap audit
- **blocking_or_nonblocking**: {"product_build": "NONBLOCKING", "production_acceptance": "BLOCKING"}

## EFFECTIVE_POLICY

- **claim**: Effective host policy supports protected operation
- **current_status**: UNRESOLVED
- **missing_evidence**: Scoped policy evidence; RO-1..RO-5 not executed
- **affected_features**: ["Protected execution"]
- **runtime_consequence**: PRODUCTION_MUTATION_DISABLED
- **safe_fallback**: No host policy actions
- **future_acceptance_test**: Approved platform-specific policy review
- **blocking_or_nonblocking**: {"product_build": "NONBLOCKING", "production_acceptance": "BLOCKING"}

## R6

- **claim**: Adversarial production acceptance
- **current_status**: NOT_EXECUTED
- **missing_evidence**: Accepted protected prerequisites and R6 campaign
- **affected_features**: ["Production executor"]
- **runtime_consequence**: PRODUCTION_MUTATION_DISABLED
- **safe_fallback**: SimulationExecutor
- **future_acceptance_test**: R6 falsification campaign after prerequisite acceptance
- **blocking_or_nonblocking**: {"product_build": "NONBLOCKING", "production_acceptance": "BLOCKING"}

## CURRENT_P3

- **claim**: Current scoped quiescence
- **current_status**: UNKNOWN
- **missing_evidence**: Accepted live producer and current action evidence
- **affected_features**: ["Autonomous checkpoint/publication"]
- **runtime_consequence**: PRODUCTION_MUTATION_DISABLED
- **safe_fallback**: Plan-only gates
- **future_acceptance_test**: Current project proof at use time
- **blocking_or_nonblocking**: {"product_build": "NONBLOCKING", "production_acceptance": "BLOCKING"}

## CURRENT_AUTHORITY

- **claim**: Current scoped action authority
- **current_status**: UNKNOWN
- **missing_evidence**: Independent authority and use-time revalidation
- **affected_features**: ["Mutation/recovery"]
- **runtime_consequence**: PRODUCTION_MUTATION_DISABLED
- **safe_fallback**: Refuse with reason
- **future_acceptance_test**: Authority revocation and replay acceptance
- **blocking_or_nonblocking**: {"product_build": "NONBLOCKING", "production_acceptance": "BLOCKING"}

## HOST_INTEROPERABILITY

- **claim**: Installed plugin compatibility
- **current_status**: NOT_EXECUTED
- **missing_evidence**: Actual Codex host integration acceptance
- **affected_features**: ["Plugin integration"]
- **runtime_consequence**: ACCEPTANCE_NOT_CLAIMED
- **safe_fallback**: Offline package validation
- **future_acceptance_test**: Explicit installation and bounded interoperability test
- **blocking_or_nonblocking**: {"product_build": "NONBLOCKING", "production_acceptance": "BLOCKING"}

## CLEAN_WINDOWS

- **claim**: Clean-machine release acceptance
- **current_status**: PARTIAL
- **missing_evidence**: Separate pristine Windows VM validation and trusted signing
- **affected_features**: ["Release deployment acceptance"]
- **runtime_consequence**: ACCEPTANCE_NOT_CLAIMED
- **safe_fallback**: Unsigned experimental portable build
- **future_acceptance_test**: Install/start/export/uninstall on clean Windows 10
- **blocking_or_nonblocking**: {"product_build": "NONBLOCKING", "production_acceptance": "BLOCKING"}

## B11

- **claim**: Inherited pack interruption fixture stability
- **current_status**: UNRESOLVED
- **missing_evidence**: Cause of historical intermittent POSIX tree-equality failures
- **affected_features**: ["Inherited POSIX mutation acceptance"]
- **runtime_consequence**: ACCEPTANCE_NOT_CLAIMED
- **safe_fallback**: Windows product does not invoke POSIX executors
- **future_acceptance_test**: Separate authorized platform investigation
- **blocking_or_nonblocking**: {"product_build": "NONBLOCKING", "production_acceptance": "BLOCKING"}

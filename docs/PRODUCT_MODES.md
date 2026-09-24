# Product modes

| Mode | Behavior |
|---|---|
| READ_ONLY_SAFE | Default historical reading, analysis, exports and dry-run |
| EXPERIMENTAL_LOCAL | Explicit experimental selection; live executor still refuses |
| SIMULATION | Explicit synthetic transitions; zero repository effects |
| DEVELOPER_LAB | Local simulation/API use; no privileged actions |
| PRODUCTION_CANDIDATE | Refusal gates; cannot enable production execution |

Mode selection is never authority. No imported YES, forged plan or SDK mode name
activates production mutation. Exports are explicit output operations. No listener
or automatic account observation starts in any mode.

Live Continuity observation, evidence journals/checkpoints and inert capsule exports
are available under the default mode after explicit project selection. The separate
`live test` wrapper executes only the command explicitly supplied by the caller;
tests may have their own project effects and the wrapper is not a sandbox. MCP
report calls cannot invoke it. A mode, event, next action or imported capsule grants
no command authority. All production repository executors remain refusal-only.

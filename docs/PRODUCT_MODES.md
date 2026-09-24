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

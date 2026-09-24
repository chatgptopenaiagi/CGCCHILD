# Local Agent Fabric foundation

cgcchild.sdk.LocalAgentRouter exposes the bounded in-process ReadRouter. Register a
snapshot route, issue a principal-bound opaque grant, dispatch closed read requests,
inspect audit events, revoke or close. Existing capability checks enforce expiry and
monotonic clocks. The router lifetime is a local session. Host callers supply trusted
principal and clock bindings. Serialized remote claims cannot import grants.

This is an experimental local foundation, not distributed authentication/execution.
No socket, tunnel, cloud agent, arbitrary command or callback is accepted.

# Windows product architecture

GUI and CLI share Workbench, the versioned SDK facade and existing historical codecs.
The bounded MCP adapter and scoped local ReadRouter are reused. Product code lives
in src/cgcchild; inherited src/cgc semantics remain unchanged. Startup has no snapshot
and performs no host discovery. Explicit file selection loads bounded inert documents.

Python cgcchild.sdk and Node cgcchild-sdk negotiate cgcchild-sdk-1. Experimental wire
profile versions remain unchanged. Public errors are INVALID_SNAPSHOT, INVALID_CAPSULE,
and UNSUPPORTED_SDK_VERSION. Existing independent codecs own canonical bytes,
deterministic capsules and semantic checks. Integrity is not authenticity.

V3 Windows offline planning/review is experimental; fresh capture and execution remain
partial/blocked. V4 protocol/capsule/stdio/SDK are shipped experimental components.
GUI scope is a historical workbench, not a live quota monitor. Remote gateway is
deferred; local contracts imply no remote authentication or authority.

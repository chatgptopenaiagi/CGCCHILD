# CGCCHILD experimental Node snapshot codec

Independent JavaScript implementation of the [model-only state0.1 contract](../../docs/CGCCHILD_STATE_PROTOCOL.md).
No dependencies; uses installed Node built-ins. Not a browser, TypeScript, capsule or live
CGC SDK. Original [Apache-2.0 license](../../LICENSE) and attribution apply.

Exports: validateState, encodeState, decodeState, stateDigest, humanStatus. Decode requires
Uint8Array/Buffer canonical bytes. No network, filesystem, subprocess or execution API in
state.mjs. Model clocks are validated as BigInt from canonical decimal strings, then retained
as strings. UNKNOWN and false remain distinct; missing/null obligations refuse. Imported
claims remain inert; this SDK cannot evaluate production proof or grant authorization.

Node JSON.parse alone collapses duplicate keys. This decoder never returns that intermediate
value: it validates the fixed shape and requires byte-identical canonical re-encoding, so
duplicate keys and noncanonical encodings refuse. It does not accept arbitrary recursive data.
The small CLI-like conformance file is an offline test harness, not a product transport.

Run from CGCCHILD:

```text
node sdk/javascript/test_state.mjs
```

Windows Node v26.8.1 passed692 checks, including all truncations of the pinned snapshot,
duplicate fields, authority promotion, invalid dates, integer bounds and status preservation.
The Python unittest corpus independently compares acceptance, bytes, digests and full human
output. It skips explicitly if Node is absent; a skip does not establish platform support.

Review found a language-specific pitfall before publication: JavaScript dollar anchors can
match before a final newline. Full-match equality was added for identifiers/clocks, with
LF/CR/CRLF adversarial tests. No safety check was weakened. No package was installed.
V4.4 is EXPERIMENTAL/PARTIAL for this one profile and runtime; generated bindings, browser
compatibility, other languages and full V3 record projection remain unaccepted.

# Installer

CGCCHILD-Setup-0.3.0.exe is an unsigned experimental x64 Inno installer. Default is
per-user, without elevation. Explicit all-users selection supports Program Files
through normal Windows authorization. Build does not escalate. Start Menu shortcut,
optional Desktop shortcut, version metadata and uninstall are supported. Stable AppId
supports upgrades. User exports belong outside installation and are not removed.
No service, startup entry or automatic plugin installation exists.

Extract the portable ZIP and keep CGC.exe beside _internal. It requires no installation.
The console binary provides CLI/MCP. Signing and clean-VM acceptance remain deferred;
no host protections are changed for packaging or execution.

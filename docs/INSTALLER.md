# Installer

CGCCHILD-Setup-0.4.0.exe is an unsigned experimental x64 Inno installer. Default is
per-user, without elevation. Explicit all-users selection supports Program Files
through normal Windows authorization. Build does not escalate. Start Menu shortcut,
optional Desktop shortcut, version metadata and uninstall are supported. Stable AppId
supports upgrades. User exports belong outside installation and are not removed.
No service, startup entry or automatic plugin installation exists.

Live session storage defaults to LOCALAPPDATA outside the installation directory.
Installer upgrades/uninstall do not delete those sessions or outside exports.

0.4 current-host lifecycle acceptance uses QA-only application IDs with the same
installer script and 0.3/0.4 payloads. This prevents overwriting an existing user's
shipping-AppId registration. Baseline install, real previous-version upgrade,
reinstall, uninstall and external export/session retention are tested. The exact
shipping-AppId lifecycle and independent clean-VM acceptance remain NOT_EXECUTED;
the default shipping installer is built and its payload is tested separately.

Extract the portable ZIP and keep CGC.exe beside _internal. It requires no installation.
The console binary provides CLI/MCP. Signing and clean-VM acceptance remain deferred;
no host protections are changed for packaging or execution.

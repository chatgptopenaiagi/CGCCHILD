"""Copy only explicit release resources; no environment or user data collection."""
import importlib.metadata
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
dest = root/'dist/CGC'
for name in ('LICENSE', 'README.md', 'THIRD_PARTY_NOTICES.md'):
    shutil.copy2(root/name, dest/name)
for name in ('WINDOWS_BUILD.md','PRODUCT_GUIDE.md','PRODUCT_MODES.md','EXECUTOR_MODEL.md',
             'SECURITY_ACCEPTANCE_DEBT.md','RELEASE_PROCESS.md','INSTALLER.md','RELEASE_NOTES.md'):
    (dest/'docs').mkdir(exist_ok=True)
    shutil.copy2(root/'docs'/name, dest/'docs'/name)
for source, target in [('plugins/cgcchild-readonly','plugin'),('sdk/javascript','sdk/javascript'),
                       ('docs/child-schemas','schemas')]:
    shutil.copytree(root/source, dest/target, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__','*.tgz','node_modules'))
shutil.copy2(root/'src/cgcchild/resources/example.json',dest/'example.json')
(dest/'safe-defaults.json').write_text('{"mode":"READ_ONLY_SAFE","production_mutation":false,"network_listener":false}\n')
# Preserve upstream distribution license texts for dynamically bundled libraries.
for name in ('PySide6','PySide6_Essentials','PySide6_Addons','shiboken6','pyinstaller'):
    dist = importlib.metadata.distribution(name)
    for file in dist.files or []:
        if any(x in str(file).lower() for x in ('license','copying','copyright')) and dist.locate_file(file).is_file():
            target = dest/'licenses'/name/Path(str(file))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dist.locate_file(file),target)
print('Staged documentation, plugin, SDK, schemas and dependency licenses')

import ast
from pathlib import Path

ROOT = Path("src/wats")


def module_name(path: Path) -> str:
    return "src.wats." + ".".join(path.relative_to(ROOT).with_suffix("").parts)


files = [p for p in ROOT.rglob("*.py") if "__pycache__" not in p.parts]
mods = {module_name(p): p for p in files}
imports = {m: set() for m in mods}

for m, p in mods.items():
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        continue

    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                imports[m].add(a.name)
        elif isinstance(n, ast.ImportFrom):
            if n.level and n.module:
                pkg = ".".join(m.split(".")[: -n.level])
                imports[m].add((pkg + "." + n.module).strip("."))
            elif n.module:
                imports[m].add(n.module)

ref_count = {m: 0 for m in mods}
for _, imps in imports.items():
    for imp in imps:
        for m in mods:
            if imp == m or imp.startswith(m + "."):
                ref_count[m] += 1

entry_points = {
    "src.wats.main",
    "src.wats.config",
    "src.wats.app_window",
}

potential_unreferenced = [
    str(mods[m]).replace("\\", "/")
    for m, c in ref_count.items()
    if c == 0 and m not in entry_points and not m.endswith("__init__")
]

print("POTENTIAL_UNREFERENCED_MODULES", len(potential_unreferenced))
for item in sorted(potential_unreferenced):
    print(item)

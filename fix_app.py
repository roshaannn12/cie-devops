from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

# Remove accidental PowerShell wrapper lines if present.
lines = s.splitlines()
if lines and lines[0].strip() == "@'":
    lines = lines[1:]
if lines and lines[-1].strip() == "'@":
    lines = lines[:-1]

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("Removed accidental wrapper, if present.")

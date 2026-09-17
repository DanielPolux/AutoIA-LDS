"""Regenera UN SOLO CPxxx.py desde generate_scripts.py (sin tocar los
otros 61), para validar cambios de plantilla/cuerpo puntuales antes de
decidir si se propagan a todo el proyecto."""
import sys
import generate_scripts as gs

cp = sys.argv[1] if len(sys.argv) > 1 else "CP009"
casos = [c for c in gs.CASES if c["cp"] == cp]
assert casos, f"{cp} no encontrado en CASES"
(gs.OUT_DIR / f"{cp}.py").write_text(gs.render(casos[0]), encoding="utf-8")
print(f"{cp}.py regenerado desde generate_scripts.py")

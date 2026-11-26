"""
Genera reportes de las pruebas en PDF y HTML.
Usa fpdf2 (pip install fpdf2).
Uso:
    python generate_report.py
Entrada: test_results.json
Salida : reporte_pruebas.pdf  +  reporte_pruebas.html
"""
import json
import os
from datetime import datetime
from html import escape

from fpdf import FPDF, XPos, YPos

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(BASE_DIR, "test_results.json")
OUTPUT_PDF = os.path.join(BASE_DIR, "reporte_pruebas.pdf")
OUTPUT_HTML = os.path.join(BASE_DIR, "reporte_pruebas.html")


# ============================================================
# SANITIZADOR: convierte cualquier Unicode a latin-1 seguro
# ============================================================
def safe_latin1(text):
    """
    Convierte un string a algo que la fuente core de fpdf2 (latin-1)
    pueda dibujar. Caracteres no representables -> '?'.
    """
    if text is None:
        return ""
    text = str(text)
    try:
        # Intenta codificar/decodificar en latin-1; si falla, reemplaza
        return text.encode("latin-1", errors="replace").decode("latin-1")
    except Exception:
        return "".join(c if ord(c) < 256 else "?" for c in text)


def load_results():
    if not os.path.exists(RESULTS_FILE):
        raise FileNotFoundError(f"No se encontro {RESULTS_FILE}. Ejecuta pytest primero.")
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def short(value, limit):
    if value is None:
        return "-"
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text.replace("\n", " ").replace("\r", " ")


# ============================================================
# PDF
# ============================================================
class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 58, 95)
        self.cell(0, 8, safe_latin1("Reporte de Pruebas Automatizadas - Guitar Store"),
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)
        self.set_draw_color(203, 213, 225)
        self.line(10, self.get_y(), 287, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 6, safe_latin1(f"Pagina {self.page_no()}"), align="C")


def build_pdf(data):
    results = data["results"]
    first = results[0] if results else {}
    total = data["total"]

    pdf = ReportPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # --- Metadatos ---
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(0, 5, safe_latin1(f"Fecha de generacion: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, safe_latin1(f"Commit: {first.get('commit_sha', 'local')}   |   Rama: {first.get('branch', 'local')}   |   Actor: {first.get('actor', 'local')}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, safe_latin1(f"Timestamp de ejecucion: {data['timestamp']}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # --- Resumen general ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 7, "Resumen general", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(40, 7, f"Total: {total}")
    pdf.cell(40, 7, f"Aprobadas: {data['passed']}")
    pdf.cell(40, 7, f"Fallidas: {data['failed']}")
    pdf.cell(40, 7, f"Omitidas: {data['skipped']}")
    tasa = f"{(data['passed']/total*100):.2f}%" if total else "0%"
    pdf.cell(40, 7, f"Tasa de exito: {tasa}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    # --- Resumen por suite ---
    suites = {}
    for r in results:
        s = suites.setdefault(r["suite"], {"total": 0, "passed": 0, "failed": 0, "skipped": 0})
        s["total"] += 1
        s[r["status"]] += 1

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 7, "Resumen por suite", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(30, 58, 95)
    pdf.set_text_color(255, 255, 255)
    headers = ["Suite", "Total", "Aprobadas", "Fallidas", "Omitidas", "Tasa"]
    widths = [70, 30, 35, 35, 35, 40]
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(15, 23, 42)
    fill = False
    for name, c in sorted(suites.items()):
        pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
        tasa_s = f"{(c['passed']/c['total']*100):.1f}%" if c["total"] else "0%"
        pdf.cell(widths[0], 6, safe_latin1(short(name, 40)), border=1, fill=True)
        pdf.cell(widths[1], 6, str(c["total"]), border=1, fill=True, align="C")
        pdf.cell(widths[2], 6, str(c["passed"]), border=1, fill=True, align="C")
        pdf.cell(widths[3], 6, str(c["failed"]), border=1, fill=True, align="C")
        pdf.cell(widths[4], 6, str(c["skipped"]), border=1, fill=True, align="C")
        pdf.cell(widths[5], 6, tasa_s, border=1, fill=True, align="C")
        pdf.ln()
        fill = not fill

    # --- Detalle de pruebas ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 58, 95)
    pdf.cell(0, 7, safe_latin1(f"Detalle de pruebas ({total})"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(30, 58, 95)
    pdf.set_text_color(255, 255, 255)
    headers = ["#", "Test", "Descripcion", "Metodo", "Endpoint", "Status", "TR(ms)", "Estado", "ms"]
    widths = [10, 45, 55, 18, 30, 14, 16, 18, 14]
    for h, w in zip(headers, widths):
        pdf.cell(w, 6, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(15, 23, 42)
    fill = False
    for i, r in enumerate(results, start=1):
        if pdf.get_y() > 185:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_fill_color(30, 58, 95)
            pdf.set_text_color(255, 255, 255)
            for h, w in zip(headers, widths):
                pdf.cell(w, 6, h, border=1, fill=True, align="C")
            pdf.ln()
            pdf.set_font("Helvetica", "", 6)
            pdf.set_text_color(15, 23, 42)

        pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(widths[0], 5, str(i), border=1, fill=True, align="C")
        pdf.cell(widths[1], 5, safe_latin1(short(r["test_name"], 40)), border=1, fill=True)
        pdf.cell(widths[2], 5, safe_latin1(short(r.get("description"), 50)), border=1, fill=True)
        pdf.cell(widths[3], 5, safe_latin1(r.get("method") or "-"), border=1, fill=True, align="C")
        pdf.cell(widths[4], 5, safe_latin1(short(r.get("endpoint"), 20)), border=1, fill=True)
        pdf.cell(widths[5], 5, str(r.get("status_code") or "-"), border=1, fill=True, align="C")
        pdf.cell(widths[6], 5, str(r.get("response_time_ms") or "-"), border=1, fill=True, align="C")
        pdf.cell(widths[7], 5, r["status"].upper(), border=1, fill=True, align="C")
        pdf.cell(widths[8], 5, str(r["duration_ms"]), border=1, fill=True, align="C")
        pdf.ln()
        fill = not fill

    # --- Detalle de fallos ---
    failed = [r for r in results if r["status"] == "failed"]
    if failed:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(185, 28, 28)
        pdf.cell(0, 7, safe_latin1(f"Detalle de fallos ({len(failed)})"),
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(15, 23, 42)
        for i, r in enumerate(failed, start=1):
            pdf.set_font("Helvetica", "B", 9)
            pdf.multi_cell(0, 5, safe_latin1(f"{i}. {r['test_name']}"))
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(0, 4, safe_latin1(f"Descripcion: {short(r.get('description'), 300)}"))
            pdf.multi_cell(0, 4, safe_latin1(f"Metodo: {r.get('method') or '-'} | Endpoint: {r.get('endpoint') or '-'} | Status: {r.get('status_code') or '-'}"))
            pdf.multi_cell(0, 4, safe_latin1(f"Input: {short(r.get('input'), 300)}"))
            pdf.multi_cell(0, 4, safe_latin1(f"Expected: {short(r.get('expected'), 300)}"))
            pdf.multi_cell(0, 4, safe_latin1(f"Error: {short(r.get('error_message'), 500)}"))
            pdf.ln(2)

    pdf.output(OUTPUT_PDF)
    print(f"[OK] PDF generado: {OUTPUT_PDF}")


# ============================================================
# HTML (soporta Unicode completo, sin sanitizar)
# ============================================================
def build_html(data):
    results = data["results"]
    first = results[0] if results else {}
    total = data["total"]
    passed = data["passed"]
    failed = data["failed"]
    skipped = data["skipped"]
    tasa = f"{(passed/total*100):.2f}%" if total else "0%"

    suites = {}
    for r in results:
        s = suites.setdefault(r["suite"], {"total": 0, "passed": 0, "failed": 0, "skipped": 0})
        s["total"] += 1
        s[r["status"]] += 1

    def status_color(s):
        return {"passed": "#16a34a", "failed": "#dc2626", "skipped": "#ca8a04"}.get(s, "#64748b")

    rows_suites = ""
    for name, c in sorted(suites.items()):
        tasa_s = f"{(c['passed']/c['total']*100):.1f}%" if c["total"] else "0%"
        rows_suites += f"""
        <tr>
            <td>{escape(name)}</td>
            <td class="num">{c['total']}</td>
            <td class="num passed">{c['passed']}</td>
            <td class="num failed">{c['failed']}</td>
            <td class="num skipped">{c['skipped']}</td>
            <td class="num">{tasa_s}</td>
        </tr>"""

    rows_tests = ""
    for i, r in enumerate(results, start=1):
        sc = status_color(r["status"])
        rows_tests += f"""
        <tr>
            <td class="num">{i}</td>
            <td><code>{escape(r['test_name'])}</code></td>
            <td>{escape(str(r.get('description') or '-'))}</td>
            <td>{escape(str(r.get('method') or '-'))}</td>
            <td><code>{escape(str(r.get('endpoint') or '-'))}</code></td>
            <td class="num">{r.get('status_code') or '-'}</td>
            <td class="num">{r.get('response_time_ms') or '-'}</td>
            <td style="color:{sc};font-weight:bold;">{r['status'].upper()}</td>
            <td class="num">{r['duration_ms']}</td>
        </tr>"""

    failed_tests = [r for r in results if r["status"] == "failed"]
    failed_html = ""
    if failed_tests:
        items = ""
        for i, r in enumerate(failed_tests, start=1):
            items += f"""
            <div class="fail-card">
                <h4>{i}. {escape(r['test_name'])}</h4>
                <p><b>Descripcion:</b> {escape(str(r.get('description') or '-'))}</p>
                <p><b>Metodo:</b> {escape(str(r.get('method') or '-'))} |
                   <b>Endpoint:</b> <code>{escape(str(r.get('endpoint') or '-'))}</code> |
                   <b>Status:</b> {r.get('status_code') or '-'}</p>
                <p><b>Input:</b> {escape(short(r.get('input'), 300))}</p>
                <p><b>Expected:</b> {escape(short(r.get('expected'), 300))}</p>
                <pre>{escape(short(r.get('error_message'), 800))}</pre>
            </div>"""
        failed_html = f"<h2 class='fail-title'>Detalle de fallos ({len(failed_tests)})</h2>{items}"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Reporte de Pruebas - Guitar Store</title>
<style>
    body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background:#f8fafc; color:#0f172a; margin:0; padding:2rem; }}
    header {{ background:#1e3a5f; color:white; padding:1.5rem 2rem; border-radius:8px; margin-bottom:2rem; }}
    header h1 {{ margin:0; font-size:1.6rem; }}
    header p {{ margin:.4rem 0 0; opacity:.9; font-size:.9rem; }}
    .cards {{ display:grid; grid-template-columns:repeat(5,1fr); gap:1rem; margin-bottom:2rem; }}
    .card {{ background:white; border-radius:8px; padding:1rem; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
    .card .num {{ font-size:1.8rem; font-weight:bold; }}
    .card.passed .num {{ color:#16a34a; }}
    .card.failed .num {{ color:#dc2626; }}
    .card.skipped .num {{ color:#ca8a04; }}
    .card.total .num {{ color:#1e3a5f; }}
    .card.rate .num {{ color:#2563eb; }}
    .card .label {{ font-size:.8rem; color:#64748b; text-transform:uppercase; letter-spacing:.05em; }}
    table {{ width:100%; background:white; border-collapse:collapse; border-radius:8px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.08); margin-bottom:2rem; font-size:.85rem; }}
    th {{ background:#1e3a5f; color:white; padding:.6rem; text-align:left; font-size:.8rem; text-transform:uppercase; }}
    td {{ padding:.5rem .6rem; border-bottom:1px solid #e2e8f0; vertical-align:top; }}
    tr:nth-child(even) {{ background:#f8fafc; }}
    td.num {{ text-align:center; }}
    td.passed {{ color:#16a34a; font-weight:bold; }}
    td.failed {{ color:#dc2626; font-weight:bold; }}
    td.skipped {{ color:#ca8a04; font-weight:bold; }}
    h2 {{ color:#1e3a5f; border-bottom:2px solid #cbd5e1; padding-bottom:.4rem; margin-top:2rem; }}
    .fail-title {{ color:#dc2626; }}
    .fail-card {{ background:white; border-left:4px solid #dc2626; padding:1rem; border-radius:6px; margin-bottom:1rem; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
    .fail-card h4 {{ margin:0 0 .5rem; color:#dc2626; }}
    .fail-card p {{ margin:.3rem 0; font-size:.85rem; }}
    .fail-card pre {{ background:#fef2f2; padding:.6rem; border-radius:4px; overflow-x:auto; font-size:.75rem; color:#7f1d1d; }}
    code {{ background:#f1f5f9; padding:.1rem .3rem; border-radius:3px; font-size:.8rem; }}
</style>
</head>
<body>
<header>
    <h1>Reporte de Pruebas Automatizadas - Guitar Store API</h1>
    <p>Fecha de generacion: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    <p>Commit: <code style="background:#334155;color:white;">{first.get('commit_sha','local')}</code>
       &nbsp;|&nbsp; Rama: <code style="background:#334155;color:white;">{first.get('branch','local')}</code>
       &nbsp;|&nbsp; Actor: <code style="background:#334155;color:white;">{first.get('actor','local')}</code></p>
    <p>Timestamp de ejecucion: {data['timestamp']}</p>
</header>

<div class="cards">
    <div class="card total"><div class="num">{total}</div><div class="label">Total</div></div>
    <div class="card passed"><div class="num">{passed}</div><div class="label">Aprobadas</div></div>
    <div class="card failed"><div class="num">{failed}</div><div class="label">Fallidas</div></div>
    <div class="card skipped"><div class="num">{skipped}</div><div class="label">Omitidas</div></div>
    <div class="card rate"><div class="num">{tasa}</div><div class="label">Tasa de exito</div></div>
</div>

<h2>Resumen por suite</h2>
<table>
    <thead><tr><th>Suite</th><th>Total</th><th>Aprobadas</th><th>Fallidas</th><th>Omitidas</th><th>Tasa</th></tr></thead>
    <tbody>{rows_suites}</tbody>
</table>

<h2>Detalle de pruebas ({total})</h2>
<table>
    <thead><tr><th>#</th><th>Test</th><th>Descripcion</th><th>Metodo</th><th>Endpoint</th><th>Status</th><th>TR (ms)</th><th>Estado</th><th>Duracion (ms)</th></tr></thead>
    <tbody>{rows_tests}</tbody>
</table>

{failed_html}
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] HTML generado: {OUTPUT_HTML}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    data = load_results()
    build_pdf(data)
    build_html(data)
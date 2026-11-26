import json
import html
from pathlib import Path
from datetime import datetime

from fpdf import FPDF


# Rutas del proyecto
BASE_DIR = Path(__file__).resolve().parent
RESULTS_FILE = BASE_DIR / "reports" / "results.json"
HTML_FILE = BASE_DIR / "frontend_report.html"
PDF_FILE = BASE_DIR / "frontend_report.pdf"


def load_results():
    """Carga los resultados generados por Playwright."""
    if not RESULTS_FILE.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de resultados:\n{RESULTS_FILE}\n\n"
            "Ejecuta primero las pruebas de Playwright con el reporter JSON."
        )

    with RESULTS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_test_status(test):
    """Obtiene el estado de un test a partir de sus resultados."""
    results = test.get("results", [])

    if not results:
        return "unknown"

    # Si hay varios intentos, se toma el último resultado.
    result = results[-1]
    status = result.get("status", "unknown")

    if status == "passed":
        return "passed"
    if status == "failed" or status == "timedOut":
        return "failed"
    if status == "skipped" or status == "interrupted":
        return "skipped"

    return "unknown"


def get_test_error(test):
    """Extrae el mensaje de error, si existe."""
    results = test.get("results", [])

    if not results:
        return ""

    result = results[-1]
    error = result.get("error")

    if isinstance(error, dict):
        return error.get("message", "")

    if isinstance(error, str):
        return error

    errors = result.get("errors", [])
    messages = []

    for item in errors:
        if isinstance(item, dict):
            messages.append(item.get("message", ""))
        elif isinstance(item, str):
            messages.append(item)

    return "\n".join(message for message in messages if message)


def get_test_duration(test):
    """Obtiene la duración total del test en milisegundos."""
    results = test.get("results", [])

    if not results:
        return 0

    return sum(result.get("duration", 0) for result in results)


def collect_tests(suites, parent_title=""):
    """Recorre las suites de Playwright y reúne todos los tests."""
    collected = []

    for suite in suites:
        suite_title = suite.get("title", "")
        full_title = " > ".join(
            part for part in [parent_title, suite_title] if part
        )

        for spec in suite.get("specs", []):
            spec_title = spec.get("title", "Test sin título")
            file_name = spec.get("file", suite.get("file", ""))

            for test in spec.get("tests", []):
                status = get_test_status(test)

                collected.append({
                    "title": spec_title,
                    "suite": full_title,
                    "file": file_name,
                    "status": status,
                    "duration": get_test_duration(test),
                    "error": get_test_error(test),
                    "project": test.get("projectName", ""),
                })

        # Algunas versiones o configuraciones anidan suites.
        collected.extend(
            collect_tests(suite.get("suites", []), full_title)
        )

    return collected


def parse_playwright_results(raw_data):
    """Convierte el JSON de Playwright en información para el reporte."""
    suites = raw_data.get("suites", [])
    tests = collect_tests(suites)

    passed = sum(test["status"] == "passed" for test in tests)
    failed = sum(test["status"] == "failed" for test in tests)
    skipped = sum(test["status"] == "skipped" for test in tests)
    unknown = sum(test["status"] == "unknown" for test in tests)

    total = len(tests)
    completed = passed + failed

    pass_rate = (passed / completed * 100) if completed else 0
    total_duration = sum(test["duration"] for test in tests)

    return {
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "unknown": unknown,
        "pass_rate": pass_rate,
        "duration": total_duration,
        "tests": tests,
    }


def build_html(data):
    """Genera el reporte HTML."""
    rows = []

    for test in data["tests"]:
        status = test["status"]

        if status == "passed":
            status_label = "Aprobada"
        elif status == "failed":
            status_label = "Fallida"
        elif status == "skipped":
            status_label = "Omitida"
        else:
            status_label = "Desconocido"

        error_html = html.escape(test["error"]).replace("\n", "<br>")

        rows.append(
            f"""
            <tr>
                <td>{html.escape(test["title"])}</td>
                <td>{html.escape(test["suite"])}</td>
                <td>{html.escape(test["file"])}</td>
                <td class="status {status}">{status_label}</td>
                <td>{test["duration"]} ms</td>
                <td class="error">{error_html}</td>
            </tr>
            """
        )

    tests_rows = "\n".join(rows)

    document = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de pruebas frontend</title>

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            padding: 30px;
            font-family: Arial, Helvetica, sans-serif;
            background: #f3f6fb;
            color: #1f2937;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        h1 {{
            margin-bottom: 8px;
            color: #1e3a8a;
        }}

        .generated {{
            margin-bottom: 25px;
            color: #64748b;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}

        .summary-card {{
            padding: 20px;
            border-radius: 10px;
            background: white;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
        }}

        .summary-card h2 {{
            margin: 0 0 10px;
            font-size: 14px;
            color: #64748b;
        }}

        .summary-card p {{
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }}

        .table-container {{
            overflow-x: auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 900px;
        }}

        th, td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
            text-align: left;
            vertical-align: top;
        }}

        th {{
            background: #1e3a8a;
            color: white;
        }}

        .status {{
            font-weight: bold;
        }}

        .passed {{
            color: #15803d;
        }}

        .failed {{
            color: #b91c1c;
        }}

        .skipped {{
            color: #a16207;
        }}

        .unknown {{
            color: #64748b;
        }}

        .error {{
            max-width: 450px;
            color: #b91c1c;
            white-space: normal;
            overflow-wrap: anywhere;
        }}

        @media (max-width: 600px) {{
            body {{
                padding: 15px;
            }}
        }}
    </style>
</head>

<body>
    <main class="container">
        <h1>Reporte de pruebas frontend</h1>
        <p class="generated">Generado: {html.escape(data["generated_at"])}</p>

        <section class="summary">
            <div class="summary-card">
                <h2>Total de pruebas</h2>
                <p>{data["total"]}</p>
            </div>

            <div class="summary-card">
                <h2>Aprobadas</h2>
                <p class="passed">{data["passed"]}</p>
            </div>

            <div class="summary-card">
                <h2>Fallidas</h2>
                <p class="failed">{data["failed"]}</p>
            </div>

            <div class="summary-card">
                <h2>Omitidas</h2>
                <p class="skipped">{data["skipped"]}</p>
            </div>

            <div class="summary-card">
                <h2>Porcentaje de aprobación</h2>
                <p>{data["pass_rate"]:.2f}%</p>
            </div>

            <div class="summary-card">
                <h2>Duración total</h2>
                <p>{data["duration"] / 1000:.2f} s</p>
            </div>
        </section>

        <section class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Prueba</th>
                        <th>Suite</th>
                        <th>Archivo</th>
                        <th>Estado</th>
                        <th>Duración</th>
                        <th>Error</th>
                    </tr>
                </thead>

                <tbody>
                    {tests_rows}
                </tbody>
            </table>
        </section>
    </main>
</body>
</html>
"""

    HTML_FILE.write_text(document, encoding="utf-8")
    print(f"Reporte HTML generado: {HTML_FILE}")


def build_pdf(data):
    """Genera el reporte PDF."""
    pdf = FPDF(orientation="L", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(10, 10, 10)

    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 12, "Reporte de pruebas frontend", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(
        0,
        7,
        f"Generado: {data['generated_at']}",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.ln(4)
    pdf.set_font("Arial", "B", 11)

    pdf.cell(45, 7, f"Total: {data['total']}")
    pdf.cell(45, 7, f"Aprobadas: {data['passed']}")
    pdf.cell(45, 7, f"Fallidas: {data['failed']}")
    pdf.cell(45, 7, f"Omitidas: {data['skipped']}")
    pdf.cell(45, 7, f"Aprobación: {data['pass_rate']:.2f}%")
    pdf.ln(7)

    pdf.cell(
        0,
        7,
        f"Duración total: {data['duration'] / 1000:.2f} segundos",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(5)

    # Encabezados de la tabla
    widths = [55, 55, 45, 25, 25, 72]
    headers = ["Prueba", "Suite", "Archivo", "Estado", "Duración", "Error"]

    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)

    for header, width in zip(headers, widths):
        pdf.cell(width, 8, header, border=1, fill=True)

    pdf.ln()

    pdf.set_font("Arial", "", 7)
    pdf.set_text_color(30, 30, 30)

    for test in data["tests"]:
        status = test["status"]

        if status == "passed":
            status_label = "Aprobada"
        elif status == "failed":
            status_label = "Fallida"
        elif status == "skipped":
            status_label = "Omitida"
        else:
            status_label = "Desconocido"

        values = [
            test["title"],
            test["suite"],
            test["file"],
            status_label,
            f"{test['duration']} ms",
            test["error"],
        ]

        # Limita la longitud para que las celdas no se desborden.
        values = [
            str(value).replace("\n", " ")[:250]
            for value in values
        ]

        for value, width in zip(values, widths):
            pdf.cell(width, 8, value, border=1)

        pdf.ln()

    pdf.output(str(PDF_FILE))
    print(f"Reporte PDF generado: {PDF_FILE}")


def main():
    print("Leyendo resultados de Playwright...")

    raw_data = load_results()
    data = parse_playwright_results(raw_data)

    build_html(data)
    build_pdf(data)

    print("Reportes generados correctamente.")


if __name__ == "__main__":
    main()
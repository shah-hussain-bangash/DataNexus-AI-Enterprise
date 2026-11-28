"""Install the All data page into an existing DataNexus Power BI project."""

import argparse
import json
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "dashboards/powerbi/DataNexus_EndToEnd.Report/definition/pages/allData"
)
PAGE_NAME = "allData"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_model(report):
    model_path = read_json(report / "definition.pbir")["datasetReference"]["byPath"]["path"]
    tables = (report / model_path).resolve() / "definition" / "tables"
    definitions = {}
    missing = set()
    for visual in SOURCE.glob("visuals/*/visual.json"):
        query = read_json(visual)["visual"].get("query", {}).get("queryState", {})
        for role in query.values():
            for projection in role["projections"]:
                for kind, field in projection["field"].items():
                    entity = field["Expression"]["SourceRef"]["Entity"]
                    if entity not in definitions:
                        table = tables / f"{entity}.tmdl"
                        definitions[entity] = table.read_text(encoding="utf-8-sig") if table.is_file() else ""
                    name = re.escape(field["Property"])
                    pattern = rf"^\s*{kind.lower()} (?:'{name}'|{name})(?=\s|$)"
                    if not re.search(pattern, definitions[entity], re.MULTILINE):
                        missing.add(f"{entity}[{field['Property']}]")
    if missing:
        raise ValueError("The local semantic model is missing " + ", ".join(sorted(missing)))


def install(project):
    if not (SOURCE / "page.json").is_file():
        raise ValueError("Run the installer from a complete checkout of the updated branch.")
    if project.name != "DataNexus_EndToEnd.pbip":
        raise ValueError("Select the existing DataNexus_EndToEnd.pbip file.")
    report_path = read_json(project)["artifacts"][0]["report"]["path"]
    report = (project.parent / report_path).resolve()
    metadata = report / "definition" / "pages" / "pages.json"
    installed = metadata.parent / PAGE_NAME
    check_model(report)

    settings = read_json(metadata)
    previous_order = settings["pageOrder"]
    source_files = {path.relative_to(SOURCE): path.read_bytes() for path in SOURCE.rglob("*") if path.is_file()}
    if installed.exists():
        installed_files = {
            path.relative_to(installed): path.read_bytes()
            for path in installed.rglob("*") if path.is_file()
        }
        if installed_files != source_files:
            raise ValueError("The project already has a different All data page. It was preserved.")
    elif PAGE_NAME in previous_order:
        raise ValueError("Page metadata already references All data, but its page folder is missing.")

    settings["pageOrder"] = [PAGE_NAME, *(page for page in previous_order if page != PAGE_NAME)]
    settings["activePageName"] = PAGE_NAME
    with TemporaryDirectory(prefix=".all-data-", dir=report / "definition") as temp:
        stage = Path(temp)
        staged_metadata = stage / metadata.name
        staged_metadata.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        if not installed.exists():
            staged_page = stage / PAGE_NAME
            shutil.copytree(SOURCE, staged_page)
            staged_page.rename(installed)
            try:
                staged_metadata.replace(metadata)
            except OSError:
                installed.rename(staged_page)
                raise
        else:
            staged_metadata.replace(metadata)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="The local DataNexus_EndToEnd.pbip to update.")
    args = parser.parse_args()
    project = args.project.resolve()
    try:
        install(project)
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        parser.exit(1, f"Could not install All data. {error}\n")
    print(f"Installed All data as the startup page. Reopen {project} in Power BI Desktop.")


if __name__ == "__main__":
    main()

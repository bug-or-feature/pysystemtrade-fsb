import shutil
from pathlib import Path
from jinja2 import Environment, select_autoescape, FileSystemLoader

from sysdata.data_blob import dataBlob
from sysdata.config.production_config import get_production_config
from syslogging.logger import *
from sysproduction.data.reports import dataReports
from sysproduction.reporting.reporting_functions import (
    resolve_report_filename,
    resolve_report_filepath,
)


def build_dashboard(data: dataBlob, context: dict):
    data.log.info(f"Starting build of monitor page with context: {context.keys()} ...")
    jinja = _get_env()
    template = jinja.get_template("monitor.html")
    with open(get_site_path("index.html"), "w") as file:
        file.write(template.render(context))
    data.log.info("monitor build complete")


def build_report_files(data: dataBlob, context: dict):
    data_reports = dataReports(data)
    data.log.info(f"Starting build of site reports with context: {context.keys()} ...")
    jinja = _get_env()
    template = jinja.get_template("report_file.html")

    all_configs = data_reports.get_report_configs_to_run()

    site_path = Path(data.config.get_element("site_dir"))
    rep_path = site_path / "reports"

    for report_config in all_configs.values():
        report_name = report_config.title
        raw_report_path = Path(resolve_report_filepath(report_config, data))

        if raw_report_path.name.endswith("pdf"):
            if raw_report_path.exists():
                shutil.copy(raw_report_path, rep_path)
            else:
                data.log.info(f"{report_name}: no file, skipping")
        else:
            if raw_report_path.exists():
                data.log.info(f"{report_name}: generating HTML wrapper")
                with open(get_site_report_file_path(raw_report_path.name), "w") as file:
                    file.write(
                        template.render(
                            {"name": report_name, "filename": raw_report_path.name},
                        )
                    )
            else:
                data.log.info(f"{report_name}: no raw file, skipping")

    # build report index
    build_report_list(data)

    data.log.info("Site reports build complete")


def build_report_list(data: dataBlob):
    data.log.info(f"Starting build of report list...")
    jinja = _get_env()
    template = jinja.get_template("report_list.html")
    with open(get_site_path("reports.html"), "w") as file:
        file.write(
            template.render(
                {"reports": get_report_list_context(data)},
            )
        )
    data.log.info(f"Report list finished.")


def get_site_path(filename):
    config = get_production_config()
    site_path = Path(config.get_element("site_dir"))
    resolved_path = resolve_path_and_filename_for_package(str(site_path), filename)
    return resolved_path


def get_site_report_file_path(filename):
    html_file = os.path.splitext(filename)[0] + ".html"
    config = get_production_config()
    site_path = Path(config.get_element("site_dir"))
    full_path = site_path / "reports"
    resolved_path = resolve_path_and_filename_for_package(str(full_path), html_file)
    return resolved_path


def get_report_list_context(data: dataBlob):
    data_reports = dataReports(data)
    all_configs = data_reports.get_report_configs_to_run()
    site_path = Path(data.config.get_element("site_dir"))

    report_list = []
    for report_config in all_configs.values():
        report_name = report_config.title
        if hasattr(report_config, "suffix"):
            html_name = resolve_report_filename(
                report_config, data, report_config.suffix
            )
        else:
            html_name = resolve_report_filename(report_config, data, ".html")

        html_full_path = site_path / "reports" / html_name
        if html_full_path.exists():
            data.log.info(f"Including in report list: {report_name}")
            report_list.append((report_name, html_name))
        else:
            data.log.info(f"Not including in report list: {report_name}")

    return report_list


def _get_env():
    templates = get_production_config().get_element("site_templates")
    jinja = Environment(
        loader=FileSystemLoader(templates),
        autoescape=select_autoescape(),
    )
    return jinja


if __name__ == "__main__":
    build_dashboard(None, {})

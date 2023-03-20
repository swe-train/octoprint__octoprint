import fnmatch
import os
import shutil

from invoke import task


@task
def clean(ctx, dry_run=False):
    source_folder = "src"
    abs_source_folder = os.path.abspath(source_folder)

    def delete_folder_if_empty(path):
        if next(os.scandir(path), None):
            return
        if not dry_run:
            shutil.rmtree(path)
        print(f"removed {path[len(abs_source_folder)+1:]} since it was empty")

    def delete_file(path):
        print(f"removing file '{path[len(abs_source_folder)+1:]}'")
        if not dry_run:
            os.remove(path)

    def delete_folder(path):
        print(f"removing directory '{path[len(abs_source_folder)+1:]}'")
        if not dry_run:
            shutil.rmtree(path)

    rules = [
        ("f", "*.pyc", delete_file),
        ("d", "*.egg-info", delete_folder),
        ("d", "*", delete_folder_if_empty),
    ]

    def process(root, rules):
        for entry in os.scandir(root):
            if entry.is_dir():
                process(entry.path, rules)

            for rule in rules:
                if (
                    (rule[0] == "f" and entry.is_file)
                    or (rule[0] == "d" and entry.is_dir())
                ) and fnmatch.fnmatch(entry.name, rule[1]):
                    rule[2](entry.path)
                    break

    process(abs_source_folder, rules)
    print("Cleaned up!")


@task
def css_build(ctx):
    ctx.run("octoprint dev css:build --all")


@task
def scan_deps(ctx):
    try:
        from setuptools.config.setupcfg import read_configuration
    except ImportError:
        from setuptools.config import read_configuration

    from collections import namedtuple

    import pkg_resources
    import requests
    from packaging.version import InvalidVersion
    from packaging.version import parse as parse_version

    PYPI = "https://pypi.org/simple/{package}/"

    config = read_configuration("setup.cfg")
    install_requires = config.get("options", {}).get("install_requires", [])
    extra_requires = config.get("options.extras_requires", {})

    Update = namedtuple("Update", ["name", "spec", "current", "latest"])
    update_lower_bounds = []
    update_bounds = []

    all_requires = list(install_requires)
    for value in extra_requires.values():
        all_requires += value

    # strip any comments
    all_requires = [r.split("#")[0].strip() for r in all_requires]

    for r in all_requires:
        print(f"Checking {r}...")
        requirement = pkg_resources.Requirement.parse(r)

        resp = requests.get(
            PYPI.format(package=requirement.project_name),
            headers={"Accept": "application/vnd.pypi.simple.v1+json"},
        )
        resp.raise_for_status()

        data = resp.json()

        def safe_parse_version(version):
            try:
                return parse_version(version)
            except InvalidVersion:
                return None

        versions = list(
            filter(
                lambda x: x and not x.is_prerelease and not x.is_devrelease,
                map(lambda x: safe_parse_version(x), data.get("versions", [])),
            )
        )
        if not versions:
            continue

        lower = None
        for spec in requirement.specs:
            if spec[0] == ">=":
                lower = spec[1]
                break

        latest = versions[-1]

        update = Update(requirement.project_name, str(requirement), lower, latest)

        if str(latest) not in requirement:
            update_bounds.append(update)
        elif lower and parse_version(lower) < latest:
            update_lower_bounds.append(update)

    def print_update(update):
        print(
            f"{update.spec}: latest {update.latest}, pypi: https://pypi.org/project/{update.name}/"
        )

    if update_lower_bounds:
        print("")
        print("The following dependencies can get their lower bounds updated:")
        print("")
        for update in update_lower_bounds:
            print_update(update)

    if update_bounds:
        print("")
        print("The following dependencies should get looked at for a full update:")
        print("")
        for update in update_bounds:
            print_update(update)

    if not update_lower_bounds and not update_bounds:
        print("All dependencies are up to date!")


try:
    import babel  # noqa: F401

    def _normalize_locale(locale):
        from babel.core import Locale

        return str(Locale.parse(locale))

    @task
    def babel_new(ctx, locale):
        locale = _normalize_locale(locale)
        output_dir = "translations"
        pot_file = os.path.join(output_dir, "messages.pot")
        ctx.run(f"pybabel init -l {locale} -i {pot_file} -o {output_dir}")

    @task
    def babel_extract(ctx):
        output_dir = "translations"
        mapping_file = "babel.cfg"
        input_dirs = "."
        mail_address = "i18n@octoprint.org"
        copyright_holder = "The OctoPrint Project"
        pot_file = os.path.join(output_dir, "messages.pot")

        ctx.run(
            f"pybabel extract -F '{mapping_file}' -o '{pot_file}' --msgid-bugs-address='{mail_address}' --copyright-holder='{copyright_holder}' {input_dirs}"
        )

    @task
    def babel_refresh(ctx, locale=None):
        locale = _normalize_locale(locale) if locale else None
        output_dir = "translations"
        mapping_file = "babel.cfg"
        input_dirs = "."
        mail_address = "i18n@octoprint.org"
        copyright_holder = "The OctoPrint Project"
        pot_file = os.path.join(output_dir, "messages.pot")

        ctx.run(
            f"pybabel extract -F '{mapping_file}' -o '{pot_file}' --msgid-bugs-address='{mail_address}' --copyright-holder='{copyright_holder}' {input_dirs}"
        )
        ctx.run(
            f"pybabel update -i '{pot_file}' -d '{output_dir}'"
            + (f" -l {locale}" if locale else "")
        )

    @task
    def babel_compile(ctx):
        output_dir = "translations"
        ctx.run(f"pybabel compile -d '{output_dir}'")

    @task
    def babel_bundle(ctx, locale):
        locale = _normalize_locale(locale)
        source_path = os.path.join("translations", locale)
        target_path = os.path.join("src", "octoprint", "translations")

        if not os.path.exists(source_path):
            raise RuntimeError(f"Locale {locale} does not exist")

        if os.path.exists(target_path):
            if not os.path.isdir(target_path):
                raise RuntimeError(f"Target path {target_path} is not a directory")
            shutil.rmtree(target_path)

        print(
            f"Copying translations for locale {locale} from {source_path} to {target_path}"
        )
        shutil.copytree(source_path, target_path)

    @task
    def babel_pack(ctx, locale, target=None, author=None):
        locale = _normalize_locale(locale)
        source_path = os.path.join("translations", locale)

        if not os.path.exists(source_path):
            raise RuntimeError(
                f"translation for locale {locale} does not exist, please create it first"
            )

        import datetime

        now = datetime.datetime.utcnow().replace(microsecond=0)

        if target is None:
            target = source_path

        zip_path = os.path.join(f"OctoPrint-i18n-{locale}_{now}.zip")
        print(f"Packing translation to {zip_path}")

        def add_recursively(zip, path, prefix):
            if not os.path.isdir(path):
                return

            for entry in os.listdir(path):
                entry_path = os.path.join(path, entry)
                new_prefix = prefix + "/" + entry
                if os.path.isdir(entry_path):
                    add_recursively(zip, entry_path, new_prefix)
                elif os.path.isfile(entry_path):
                    print(f"Adding {entry_path} as {new_prefix}")
                    zip.write(entry_path, new_prefix)

        meta_str = f"last_update: {now.isoformat()}\n"
        if author:
            meta_str += f"author: {author}\n"

        zip_locale_root = locale

        import zipfile

        with zipfile.ZipFile(zip_path, "w") as zip:
            add_recursively(zip, source_path, zip_locale_root)

            print(f"Adding meta.yaml as {zip_locale_root}/meta.yaml")
            zip.writestr(zip_locale_root + "/meta.yaml", meta_str)

except ImportError:
    pass

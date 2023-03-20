import os
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class custom_build_py(_build_py):
    FILES = {
        "octoprint/templates/_data": [
            "AUTHORS.md",
            "SUPPORTERS.md",
            "THIRDPARTYLICENSES.md",
        ]
    }

    def run(self):
        self._copy_files(self.FILES)
        super().run()
        self._run_versioneer()

    def _copy_files(self, files):
        for directory, entries in files.items():
            target_dir = os.path.join(self.build_lib, directory)
            self.mkpath(target_dir)

            for entry in entries:
                if isinstance(entry, tuple):
                    if len(entry) != 2:
                        continue
                    source, dest = entry[0], os.path.join(target_dir, entry[1])
                else:
                    source = entry
                    dest = os.path.join(target_dir, source)

                print("copying {} -> {}".format(source, dest))
                shutil.copy2(source, dest)

    def _run_versioneer(self):
        from versioneer import (
            get_config_from_root,
            get_root,
            get_versions,
            write_to_version_file,
        )

        root = get_root()
        cfg = get_config_from_root(root)
        versions = get_versions()
        if cfg.versionfile_build:
            target_versionfile = os.path.join(self.build_lib, cfg.versionfile_build)
            print("UPDATING {}".format(target_versionfile))
            write_to_version_file(target_versionfile, versions)


if __name__ == "__main__":
    setup(
        # supported in setup.cfg from setuptools 54, not yet on OctoPi
        entry_points={"console_scripts": ["octoprint = octoprint:main"]},
        # supported in setup.cfg from setuptools 51, not yet on OctoPi
        cmdclass={"build_py": custom_build_py},
    )

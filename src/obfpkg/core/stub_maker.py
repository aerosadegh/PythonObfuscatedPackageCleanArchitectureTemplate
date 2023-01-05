import shutil
from os import listdir, rename
from pathlib import Path
from subprocess import PIPE, Popen

from utils import remove_intersection_path

STUBS_PACKAGE_DIR_NAME = "stubs-pkg"


class Stubs:
    """Generate the stubs project files from the source project."""

    def __init__(
        self, src_path: Path, build_path: Path, package_name: str, verbose: bool = False
    ):
        self.src_path = src_path.resolve()
        self.build_path = build_path.resolve()
        self.package_name = package_name
        self.verbose = verbose

        self.clean_up()

    def _rename(self):
        for i in range(3, 0, -1):
            try:
                rename(
                    self.build_path / self.package_name,
                    self.build_path / f"{self.package_name}-stubs",
                )
                print("###  The stubs project generated successfully!")
                break
            except FileExistsError as ex:
                print(f"Error while renaming: {ex}")
                print(f"try to remove exist path... {i}")
                shutil.rmtree(
                    self.build_path / f"{self.package_name}-stubs",
                    ignore_errors=True,
                )
            except Exception as ex:
                print(f"Error while renaming: {ex}")
                print(f"Retrying... {i}")

    def generate(self):
        process = Popen(
            [
                "stubgen",
                "-o",
                self.build_path,
                "-p",
                f"{self.package_name}",
            ],
            cwd=f"{self.src_path}",
            stdout=PIPE,
            stderr=PIPE,
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(
                f"Error while generating stubs: {stderr.decode('utf-8')}\n\nSTDOUT:\n{stdout.decode('utf-8')}"
            )
        try:
            overwrited_pyi_files = self.overwrite_stubs_from_src()
            if overwrited_pyi_files and self.verbose:
                for item in overwrited_pyi_files:
                    print(f"The {item!r} overwrited from source project to stubs ")
        except NotImplementedError:
            print("WARNNING: `overwrite_stubs_from_src` NOT IMPLEMENTED YET!")
            pass
        self._rename()

        return stdout, stderr

    def overwrite_stubs_from_src(self):
        pyi_files = self.src_path.glob("*/*.pyi")
        pure_pypi_paths = [remove_intersection_path(self.src_path, item) for item in pyi_files]

        for item in pure_pypi_paths:
            shutil.copy(self.src_path / item, self.build_path / item)
        return pure_pypi_paths

    def clean_up(self):
        build_abspath = self.build_path.resolve().absolute()
        dirs = {
            build_abspath / x
            for x in listdir(build_abspath)
            if (build_abspath / x).is_dir()
        }

        for x in dirs:
            shutil.rmtree(x)

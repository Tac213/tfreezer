# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

import os
import re
import subprocess
import importlib
import sys

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

# Convert distutils Windows platform specifiers to CMake -A arguments
PLAT_TO_CMAKE = {
    "win32": "Win32",
    "win-amd64": "x64",
    "win-arm32": "ARM",
    "win-arm64": "ARM64",
}


# A CMakeExtension needs a sourcedir instead of a file list.
# The name must be the _single_ output extension from the CMake build.
# If you need multiple extensions, see scikit-build.
class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        # type: (str, str) -> None
        super(CMakeExtension, self).__init__(name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def build_extension(self, ext):
        # type: (CMakeExtension) -> None
        # Must be in this form due to bug in .resolve() only fixed in Python 3.10+
        ext_fullpath = os.path.abspath(self.get_ext_fullpath(ext.name))
        extdir = os.path.dirname(ext_fullpath)
        if not os.path.isdir(extdir):
            os.makedirs(extdir)

        # Using this requires trailing slash for auto-detection & inclusion of
        # auxiliary "native" libs

        debug = int(os.environ.get("DEBUG", 0)) if self.debug is None else self.debug
        cfg = "Debug" if debug else "Release"

        # CMake lets you override the generator - we need to check this.
        # Can be set with Conda-Build, for example.
        cmake_generator = os.environ.get("CMAKE_GENERATOR", "")

        # Set Python_EXECUTABLE instead if you use PYBIND11_FINDPYTHON
        # EXAMPLE_VERSION_INFO shows you how to pass a value into the C++ code
        # from Python.
        cmake_args = [
            "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={}{}".format(extdir, os.sep),
            "-DPYTHON_EXECUTABLE={}".format(sys.executable),
            "-DCMAKE_BUILD_TYPE={}".format(cfg),  # not used on MSVC, but no harm
        ]  # type: list[str]
        build_args = []  # type: list[str]
        # Adding CMake arguments set as environment variable
        # (needed e.g. to build for ARM OSx on conda-forge)
        if "CMAKE_ARGS" in os.environ:
            cmake_args += [item for item in os.environ["CMAKE_ARGS"].split(" ") if item]

        if self.compiler.compiler_type != "msvc":
            # Using Ninja-build since it a) is available as a wheel and b)
            # multithreads automatically. MSVC would require all variables be
            # exported for Ninja to pick it up, which is a little tricky to do.
            # Users can override the generator with CMAKE_GENERATOR in CMake
            # 3.15+.
            if not cmake_generator or cmake_generator == "Ninja":
                try:
                    ninja = importlib.import_module("ninja")

                    ninja_executable_path = os.path.join(ninja.BIN_DIR, "ninja")
                    cmake_args += [
                        "-GNinja",
                        "-DCMAKE_MAKE_PROGRAM:FILEPATH={}".format(ninja_executable_path),
                    ]
                except ImportError:
                    pass

        else:
            # Single config generators are handled "normally"
            single_config = any(x in cmake_generator for x in {"NMake", "Ninja"})

            # CMake allows an arch-in-generator style for backward compatibility
            contains_arch = any(x in cmake_generator for x in {"ARM", "Win64"})

            # Specify the arch if using MSVC generator, but only if it doesn't
            # contain a backward-compatibility arch spec already in the
            # generator name.
            if not single_config and not contains_arch:
                cmake_args += ["-A", PLAT_TO_CMAKE[self.plat_name]]

            # Multi-config generators have a different way to specify configs
            if not single_config:
                cmake_args += ["-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}".format(cfg.upper(), extdir)]
                build_args += ["--config", cfg]

        if sys.platform.startswith("darwin"):
            # Cross-compile support for macOS - respect ARCHFLAGS if set
            archs = re.findall(r"-arch (\S+)", os.environ.get("ARCHFLAGS", ""))
            if archs:
                cmake_args += ["-DCMAKE_OSX_ARCHITECTURES={}".format(";".join(archs))]

        # Set CMAKE_BUILD_PARALLEL_LEVEL to control the parallel build level
        # across all generators.
        if "CMAKE_BUILD_PARALLEL_LEVEL" not in os.environ:
            # self.parallel is a Python 3 only way to set parallel jobs by hand
            # using -j in the build_ext call, not supported by pip or PyPA-build.
            if hasattr(self, "parallel") and self.parallel:
                # CMake 3.12+ only.
                build_args += ["-j{}".format(self.parallel)]

        build_temp = os.path.join(self.build_temp, ext.name)
        if not os.path.exists(build_temp):
            os.makedirs(build_temp)

        cmake_configure_args = ["cmake", ext.sourcedir]  # type: list[str]
        cmake_configure_args.extend(cmake_args)
        p = subprocess.Popen(cmake_configure_args, cwd=build_temp)
        stdout, stderr = p.communicate()
        retcode = p.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, p.args, output=stdout, stderr=stderr)
        cmake_build_args = ["cmake", "--build", "."]
        cmake_build_args.extend(build_args)
        p = subprocess.Popen(cmake_build_args, cwd=build_temp)
        stdout, stderr = p.communicate()
        retcode = p.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, p.args, output=stdout, stderr=stderr)


def _get_data_files():
    # type: () -> list[tuple[str, list[str]]]
    if sys.platform.startswith("win"):
        site_packages_dir = "lib/site-packages/tfloader"
    elif sys.platform.startswith("linux"):
        site_packages_dir = "lib/python{}.{}/site-packages/tfloader".format(*sys.version_info[:2])
    elif sys.platform.startswith("darwin"):
        site_packages_dir = "lib/python{}.{}/site-packages/tfloader".format(*sys.version_info[:2])
    else:
        return []
    return [(site_packages_dir, ["stubs/tfloader/__init__.pyi"])]


# The information here can also be placed in setup.cfg - better separation of
# logic and declaration, and simpler if you include description/version in a file.
setup(
    name="tfloader",
    version="1.0.0",
    author="Tac Uchiha",
    author_email="cookiezhx@163.com",
    description="A package to load extension frozen packages frozen by tfreezer.",
    long_description="",
    packages=["tfloader_importer"],
    package_dir={"": "src"},
    ext_modules=[CMakeExtension("tfloader")],
    cmdclass={"build_ext": CMakeBuild},
    zip_safe=False,
    extras_require={},
    python_requires=">=3.11",
    data_files=_get_data_files(),
)

# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import typing as _t
import sys
import os
import argparse
import multiprocessing

from tfreezer import paths, log, config, utils


class _ArgumentNamespace(argparse.Namespace):
    approot: str
    appversion: str
    appname: str
    appicon: str
    variant: str
    distpath: str
    workpath: str
    entry_module: str
    hidden_imports: _t.Optional[list[str]]
    excludes: _t.Optional[list[str]]
    config_file: _t.Optional[str]


def get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approot", type=str, default=os.getcwd())
    parser.add_argument("--appversion", type=str, default="1.0.0")
    parser.add_argument("--appname", type=str, default="")
    parser.add_argument("--appicon", type=str, default="")
    parser.add_argument("--variant", type=str, choices=["debug", "release"], default="release")
    parser.add_argument("--distpath", type=str, default="")
    parser.add_argument("--workpath", type=str, default="")
    parser.add_argument("--entry-module", type=str, default="")
    parser.add_argument("--hidden-imports", type=str, nargs="+")
    parser.add_argument("--excludes", type=str, nargs="+")
    parser.add_argument("config_file", type=str, nargs="?")
    return parser


def _setup_paths(args: _ArgumentNamespace) -> None:
    paths.APP_ROOT = os.path.abspath(args.approot)
    if os.path.isabs(args.distpath) and not os.path.isfile(args.distpath):
        paths.DEPLOY_DIR = args.distpath
    elif args.distpath:
        candidate = os.path.join(args.approot, args.distpath)
        if not os.path.isfile(candidate):
            paths.DEPLOY_DIR = candidate
        else:
            paths.DEPLOY_DIR = os.path.join(args.approot, "dist")
    else:
        paths.DEPLOY_DIR = os.path.join(args.approot, "dist")
    if os.path.isabs(args.workpath) and not os.path.isfile(args.workpath):
        paths.BUILD_DIR = args.workpath
    elif args.workpath:
        candidate = os.path.join(args.approot, args.workpath)
        if not os.path.isfile(candidate):
            paths.BUILD_DIR = candidate
        else:
            paths.BUILD_DIR = os.path.join(args.approot, "build")
    else:
        paths.BUILD_DIR = os.path.join(args.approot, "build")
    paths.GENERATED_HEADERS_DIR = os.path.join(paths.BUILD_DIR, "generated")
    paths.FROZEN_MODULE_DIR = os.path.join(paths.GENERATED_HEADERS_DIR, "frozen_modules")
    paths.FROZEN_MODULES_HEADER = os.path.join(paths.FROZEN_MODULE_DIR, "frozen_modules.h")
    paths.dump_paths()


def _cmake_configure(args: _ArgumentNamespace) -> None:
    if not paths.CMAKE_EXE:
        log.logger.error("CMake is not installed in your computer.")
        sys.exit(1)
    if not paths.APP_ROOT:
        log.logger.error("approot is not set. Please set it through --approot.")
        sys.exit(1)
    debug = args.variant == "debug"
    freeze_config = config.dump_freeze_config(
        entry_module=args.entry_module, hidden_imports=args.hidden_imports, excludes=args.excludes, config_file=args.config_file
    )
    config.dump_python_path()
    app_name = args.appname
    if not app_name:
        app_name = os.path.basename(freeze_config.entry_module)
        app_name, _ = os.path.splitext(app_name)
    python_exe = paths.PYTHON_EXE.replace("\\", "/")
    app_root = paths.APP_ROOT.replace("\\", "/")
    build_dir = paths.BUILD_DIR.replace("\\", "/")
    deploy_dir = paths.DEPLOY_DIR.replace("\\", "/")
    generated_headers_dir = paths.GENERATED_HEADERS_DIR.replace("\\", "/")
    cmake_args = [
        paths.CMAKE_EXE,
        "-B",
        paths.BUILD_DIR,
        "-S",
        paths.CPP_SRC,
        "-G",
        "Visual Studio 17 2022",
        f"-DNEED_CONSOLE={'ON' if debug else 'OFF'}",
        "-DFREEZE_APPLICATION=ON",
        f"-DPYTHON_EXECUTABLE={python_exe}",
        f"-DTF_APPROOT_DIR={app_root}",
        f"-DTF_BUILD_DIR={build_dir}",
        f"-DTF_DEPLOY_DIR={deploy_dir}",
        f"-DTF_GENERATED_HEADERS_DIR={generated_headers_dir}",
        f"-DTF_APP_NAME={app_name}",
        f"-DPROJECT_VERSION={args.appversion}",
        f"-DPROJECT_ICON={args.appicon}",
    ]
    cmake_cache = os.path.join(paths.BUILD_DIR, "CMakeCache.txt")
    if os.path.isfile(cmake_cache):
        log.logger.debug("CMakeCache.txt exists, pending to remove it.")
        os.remove(cmake_cache)
    log.logger.info("CMake: Configure")
    returncode = utils.call_subprocess(cmake_args, cwd=paths.APP_ROOT)
    if returncode:
        sys.exit(returncode)


def _cmake_build(args: _ArgumentNamespace) -> None:
    if not paths.CMAKE_EXE:
        log.logger.error("CMake is not installed in your computer.")
        sys.exit(1)
    if not paths.APP_ROOT:
        log.logger.error("approot is not set. Please set it through --approot.")
        sys.exit(1)
    cmake_args = [
        paths.CMAKE_EXE,
        "--build",
        paths.BUILD_DIR,
        "--config",
        "Release",
        "--",
        f"-maxCpuCount:{multiprocessing.cpu_count()}",
    ]
    log.logger.info("CMake: Build")
    returncode = utils.call_subprocess(cmake_args, cwd=paths.APP_ROOT)
    if returncode:
        sys.exit(returncode)


def main() -> int:
    try:
        parser = get_argument_parser()
        namespace = _ArgumentNamespace()
        args = parser.parse_args(sys.argv[1:], namespace)

        # set app paths
        _setup_paths(args)

        _cmake_configure(args)
        _cmake_build(args)
        return 0
    except KeyboardInterrupt:
        log.logger.info("Keyboard Interrupt.")
        utils.close_all_log_pipe()
        return 1


if __name__ == "__main__":
    sys.exit(main())

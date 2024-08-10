# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import sys
import os
import shutil
from importlib import resources

from tfreezer import log, utils


APP_ROOT = ""
BUILD_DIR = ""
DEPLOY_DIR = ""
CPP_SRC = str(resources.files("tfreezer").joinpath("cppsrc"))

GENERATED_HEADERS_DIR = ""  # Will be added to `target_include_directories` in cmake
FROZEN_MODULE_DIR = ""  # ${GENERATED_HEADERS_DIR}/frozen_modules
FROZEN_MODULES_HEADER = ""  # ${FROZEN_MODULES_HEADER}/frozen_modules.h

PYTHON_EXE = sys.executable
CMAKE_EXE = shutil.which("cmake")


def dump_paths() -> None:
    if not BUILD_DIR:
        log.logger.error("Failed to dump paths. BUILD_DIR needs to be set.")
        return
    content = f"""\
APP_ROOT = r"{APP_ROOT}"
BUILD_DIR = r"{BUILD_DIR}"
DEPLOY_DIR = r"{DEPLOY_DIR}"
CPP_SRC = r"{CPP_SRC}"
GENERATED_HEADERS_DIR = r"{GENERATED_HEADERS_DIR}"
FROZEN_MODULE_DIR = r"{FROZEN_MODULE_DIR}"
FROZEN_MODULES_HEADER = r"{FROZEN_MODULES_HEADER}"
PYTHON_EXE = r"{PYTHON_EXE}"
CMAKE_EXE = r"{CMAKE_EXE}"
"""
    paths_file = os.path.join(BUILD_DIR, "paths")
    if not os.path.isdir(BUILD_DIR):
        os.makedirs(BUILD_DIR)
    with open(paths_file, "w", encoding="utf-8") as fp:
        fp.write(content)


def load_paths(build_dir: str) -> None:
    global APP_ROOT, BUILD_DIR, DEPLOY_DIR, GENERATED_HEADERS_DIR, FROZEN_MODULE_DIR, FROZEN_MODULES_HEADER
    build_dir = os.path.abspath(build_dir)
    if not os.path.isdir(build_dir):
        log.logger.error("Failed to load paths. '%s' is not a directory.", build_dir)
        sys.exit(1)
    paths_file = os.path.join(build_dir, "paths")
    if not os.path.isfile(paths_file):
        log.logger.error("Failed to load paths. '%s' is not a file.", paths_file)
        sys.exit(1)
    fullname = "tfreezer.dump_paths"
    module = utils.load_signle_module(fullname, paths_file)
    APP_ROOT = module.APP_ROOT
    BUILD_DIR = module.BUILD_DIR
    DEPLOY_DIR = module.DEPLOY_DIR
    GENERATED_HEADERS_DIR = module.GENERATED_HEADERS_DIR
    FROZEN_MODULE_DIR = module.FROZEN_MODULE_DIR
    FROZEN_MODULES_HEADER = module.FROZEN_MODULES_HEADER

# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import typing as _t
import types
import os
import threading
import subprocess
from importlib import machinery, util

from tfreezer import log


def iterate_all_modules(source_dir: str) -> _t.Generator[str, None, None]:
    validate_suffixes = tuple(machinery.SOURCE_SUFFIXES + machinery.EXTENSION_SUFFIXES)
    for root, _, file_names in os.walk(source_dir):
        for file_name in file_names:
            if not file_name.endswith(validate_suffixes):
                continue
            file_path = os.path.join(root, file_name)
            module_name = os.path.splitext(os.path.relpath(file_path, os.path.dirname(source_dir)))[0].replace(os.path.sep, ".")
            if module_name.endswith("__init__"):
                module_name = module_name.rpartition(".")[0]
            yield module_name


class LogPipe(threading.Thread):
    def __init__(self, log_function: _t.Callable[[str], None]) -> None:
        super().__init__()
        self.daemon = False
        self.fd_read, self.fd_write = os.pipe()
        self.pipe_reader = os.fdopen(self.fd_read)
        self._log_function = log_function
        self.start()

    def fileno(self) -> int:
        """
        Return the write file descriptor of the pipe
        """
        return self.fd_write

    def run(self) -> None:
        """
        Run the thread, logging everything.
        """
        for line in iter(self.pipe_reader.readline, ""):
            self._log_function(line.strip("\n"))
        self.pipe_reader.close()

    def close(self) -> None:
        """
        Close the write end of the pipe.
        """
        os.close(self.fd_write)


_log_pipes: list[LogPipe] = []


def close_all_log_pipe() -> None:
    for log_pipe in _log_pipes:
        log_pipe.close()


def call_subprocess(args: list[str], *, cwd: str) -> int:
    log.logger.info("Pending to run: %s\ncwd: %s", " ".join(args), cwd)
    stdout = LogPipe(log.logger.info)
    _log_pipes.append(stdout)
    stderr = LogPipe(log.logger.error)
    _log_pipes.append(stderr)
    with subprocess.Popen(
        args,
        stdout=stdout,
        stderr=stderr,
        cwd=cwd,
    ) as p:
        p.wait()
    stdout.close()
    if stdout in _log_pipes:
        _log_pipes.remove(stdout)
    stderr.close()
    if stderr in _log_pipes:
        _log_pipes.remove(stderr)
    return p.returncode


def load_signle_module(name: str, path: str) -> types.MethodType:
    loader = machinery.SourceFileLoader(name, path)
    spec = util.spec_from_file_location(name, path, loader=loader)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

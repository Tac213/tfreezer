# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import sys


def install() -> None:
    """
    Hook to support multiprocessing
    """
    try:
        from multiprocessing import spawn  # pylint: disable=import-outside-toplevel
    except ImportError:
        # multiprocessing is not used in frozen application
        return

    def is_forking(argv: list[str]) -> bool:
        return getattr(sys, "tf_multiprocessing_fork", False)

    spawn.is_forking = is_forking

    if getattr(sys, "tf_multiprocessing_fork", False):
        # Back up
        if len(sys.argv) == 0:
            sys.argv.extend(["-c", "--multiprocessing-fork"])
        elif len(sys.argv) == 1:
            sys.argv.append("--multiprocessing-fork")
        else:
            sys.argv[1] = "--multiprocessing-fork"

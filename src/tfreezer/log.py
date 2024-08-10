# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

__all__ = ["logger"]

import logging

logging.basicConfig(format="%(relativeCreated)d %(levelname)s: %(message)s", level=logging.DEBUG)
logger = logging.getLogger("tfreezer")
logger.setLevel(logging.DEBUG)

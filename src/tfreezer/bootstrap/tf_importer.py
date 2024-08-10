# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import sys
import _frozen_importlib
import pathlib


class TfFrozenImporter(_frozen_importlib.FrozenImporter):
    """
    Implement get_resource_reader to support resources loading
    """

    @classmethod
    def get_resource_reader(cls, fullname: str) -> "TfFrozenResourceReader":
        return TfFrozenResourceReader(cls, fullname)


class TfFrozenResourceReader:

    def __init__(self, loader: type[TfFrozenImporter], name: str) -> None:
        self.loader = loader
        self.path = pathlib.Path(sys._stdlib_dir).joinpath(*name.split("."))

    def open_resource(self, resource):
        return self.files().joinpath(resource).open("rb")

    def resource_path(self, resource):
        return str(self.path.joinpath(resource))

    def is_resource(self, path):
        return self.files().joinpath(path).is_file()

    def contents(self):
        return (item.name for item in self.files().iterdir())

    def files(self):
        return self.path


def install() -> None:
    """
    Install TfFrozenImporter to sys.meta_path
    """
    original_frozen_importer_index = 0
    for index, importer in enumerate(sys.meta_path):
        if importer is _frozen_importlib.FrozenImporter:
            original_frozen_importer_index = index
    sys.meta_path.insert(original_frozen_importer_index, TfFrozenImporter)

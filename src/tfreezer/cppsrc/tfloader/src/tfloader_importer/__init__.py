# -*- coding: utf-8 -*-
# author: Tac
# contact: cookiezhx@163.com

import sys
import tfloader

try:
    from typing import TYPE_CHECKING
except ImportError:
    TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Optional
    import types
    from importlib.machinery import ModuleSpec


class TfpackageFrozenImporter(object):
    """
    Meta path import for tfpackage frozen modules.

    All methods are either class or static methods to avoid the need to
    instantiate the class.
    """

    _ORIGIN = "tfpackage-frozen"  # pylint: disable=invalid-name

    @classmethod
    def _fix_up_module(cls, module):
        # type: (types.ModuleType) -> None
        if not hasattr(module, "__spec__"):
            origname = vars(module).pop("__origname__", None)
            assert origname, "see PyImport_ImportFrozenModuleObject()"
            ispkg = hasattr(module, "__path__")
            assert tfloader.is_tfpackage_frozen_package(module.__name__) == ispkg, ispkg
            filename, pkgdir = cls._resolve_filename(origname, module.__name__, ispkg)
            assert not hasattr(module, "__file__"), module.__file__
            if filename:
                try:
                    module.__file__ = filename
                except AttributeError:
                    pass
            if ispkg:
                if pkgdir:
                    assert module.__path__ == [], module.__path__
                    module.__path__.insert(0, pkgdir)
            return
        spec = module.__spec__
        state = spec.loader_state
        if state is None:
            # The module is missing FrozenImporter-specific values.

            # Fix up the spec attrs.
            origname = vars(module).pop("__origname__", None)
            assert origname, "see PyImport_ImportFrozenModuleObject()"
            ispkg = hasattr(module, "__path__")
            assert tfloader.is_tfpackage_frozen_package(module.__name__) == ispkg, ispkg
            filename, pkgdir = cls._resolve_filename(origname, spec.name, ispkg)
            spec.loader_state = type(sys.implementation)(
                filename=filename,
                origname=origname,
            )
            __path__ = spec.submodule_search_locations
            if ispkg:
                assert __path__ == [], __path__
                if pkgdir:
                    spec.submodule_search_locations.insert(0, pkgdir)
            else:
                assert __path__ is None, __path__

            # Fix up the module attrs (the bare minimum).
            assert not hasattr(module, "__file__"), module.__file__
            if filename:
                try:
                    module.__file__ = filename
                except AttributeError:
                    pass
            if ispkg:
                if module.__path__ != __path__:
                    assert module.__path__ == [], module.__path__
                    module.__path__.extend(__path__)
        else:
            # These checks ensure that _fix_up_module() is only called
            # in the right places.
            __path__ = spec.submodule_search_locations
            ispkg = __path__ is not None
            # Check the loader state.
            assert sorted(vars(state)) == ["filename", "origname"], state
            if state.origname:
                # The only frozen modules with "origname" set are stdlib modules.
                (
                    __file__,
                    pkgdir,
                ) = cls._resolve_filename(state.origname, spec.name, ispkg)
                assert state.filename == __file__, (state.filename, __file__)
                if pkgdir:
                    assert __path__ == [pkgdir], (__path__, pkgdir)
                else:
                    assert __path__ == ([] if ispkg else None), __path__
            else:
                __file__ = None
                assert state.filename is None, state.filename
                assert __path__ == ([] if ispkg else None), __path__
            # Check the file attrs.
            if __file__:
                assert hasattr(module, "__file__")
                assert module.__file__ == __file__, (module.__file__, __file__)
            else:
                assert not hasattr(module, "__file__"), module.__file__
            if ispkg:
                assert hasattr(module, "__path__")
                assert module.__path__ == __path__, (module.__path__, __path__)
            else:
                assert not hasattr(module, "__path__"), module.__path__
        assert not spec.has_location

    @classmethod
    def _resolve_filename(cls, fullname, alias=None, ispkg=False):
        # type: (str, Optional[str], bool) -> tuple[Optional[str], Optional[str]]
        if not fullname or not getattr(sys, "_stdlib_dir", None):
            return None, None
        try:
            sep = cls._SEP
        except AttributeError:
            sep = cls._SEP = "\\" if sys.platform == "win32" else "/"

        if fullname != alias:
            if fullname.startswith("<"):
                fullname = fullname[1:]
                if not ispkg:
                    fullname = "{}.__init__".format(fullname)
            else:
                ispkg = False
        relfile = fullname.replace(".", sep)
        if ispkg:
            pkgdir = "{}{}{}".format(sys._stdlib_dir, sep, relfile)  # pylint: disable=protected-access
            filename = "{}{}__init__.py".format(pkgdir, sep)
        else:
            pkgdir = None
            filename = "{}{}{}.py".format(sys._stdlib_dir, sep, relfile)  # pylint: disable=protected-access
        return filename, pkgdir

    @classmethod
    def module_repr(cls, m):
        # type: (types.Moduletype) -> str
        """Return repr for the module.

        The method is deprecated.  The import machinery does the job itself.

        """
        return "<module {!r} ({})>".format(m.__name__, cls._ORIGIN)

    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        # type: (str, Optional[list[str]], Optional[types.ModuleType]) -> Optional[ModuleSpec]
        from importlib._bootstrap import spec_from_loader  # pylint: disable=import-outside-toplevel

        info = tfloader.find_tfpackage_frozen(fullname)
        if info is None:
            return None
        ispkg, origname = info  # pylint: disable=unpacking-non-sequence
        spec = spec_from_loader(fullname, cls, origin=cls._ORIGIN, is_package=ispkg)
        filename, pkgdir = cls._resolve_filename(origname, fullname, ispkg)
        spec.loader_state = type(sys.implementation)(
            filename=filename,
            origname=origname,
        )
        if pkgdir:
            spec.submodule_search_locations.insert(0, pkgdir)
        return spec

    @classmethod
    def find_module(cls, fullname, path=None):
        # type: (str, Optional[list[str]]) -> Optional[type[TfpackageFrozenImporter]]
        """Find a frozen module.

        This method is deprecated.  Use find_spec() instead.

        """
        return cls if tfloader.is_tfpackage_frozen(fullname) else None

    @classmethod
    def create_module(cls, spec):
        # type: (ModuleSpec) -> types.ModuleType
        """Set __file__, if able."""
        module = type(sys)(spec.name)
        try:
            filename = spec.loader_state.filename
        except AttributeError:
            pass
        else:
            if filename:
                module.__file__ = filename
        return module

    @classmethod
    def exec_module(cls, module):
        # type: (types.ModuleType) -> None
        spec = module.__spec__
        name = spec.name
        code = tfloader.get_tfpackage_frozen_object(name)
        exec(code, module.__dict__)  # pylint: disable=exec-used

    @classmethod
    def load_module(cls, fullname):
        # type: (str) -> types.ModuleType
        """Load a frozen module.

        This method is deprecated.  Use exec_module() instead.

        """
        try:
            from importlib._bootstrap import _load_module_shim  # pylint: disable=import-outside-toplevel
        except ImportError:
            _load_module_shim = None
        try:
            import imp  # type: ignore  # pylint: disable=import-outside-toplevel,deprecated-module,import-error
        except ImportError:
            imp = None

        if _load_module_shim:
            module = _load_module_shim(cls, fullname)
        else:
            if imp:
                module = imp.new_module(fullname)
            else:
                module = type(sys)(fullname)
            sys.modules[fullname] = module
            if getattr(module, "__loader__", None) is None:
                try:
                    module.__loader__ = cls
                except AttributeError:
                    pass
            if getattr(module, "__package__", None) is None:
                try:
                    module.__package__ = module.__name__
                    if not tfloader.is_tfpackage_frozen_package(fullname):
                        module.__package__ = fullname.rpartition(".")[0]
                except AttributeError:
                    pass
            code = tfloader.get_tfpackage_frozen_object(fullname)
            exec(code, module.__dict__)  # pylint: disable=exec-used

        info = tfloader.find_tfpackage_frozen(fullname)
        assert info is not None
        ispkg, origname = info  # pylint: disable=unpacking-non-sequence
        module.__origname__ = origname
        vars(module).pop("__file__", None)
        if ispkg:
            module.__path__ = []
        cls._fix_up_module(module)
        return module

    @classmethod
    def get_code(cls, fullname):
        # type: (str) -> types.CodeType
        """Return the code object for the tfpackage frozen module."""
        if not tfloader.is_tfpackage_frozen(fullname):
            raise ImportError("{!r} is not a tfpackage frozen module".format(fullname), name=fullname)
        return tfloader.get_tfpackage_frozen_object(fullname)

    @classmethod
    def get_source(cls, fullname):
        # type: (str) -> Optional[str]
        """Return None as tfpackage frozen modules do not have source code."""
        if not tfloader.is_tfpackage_frozen(fullname):
            raise ImportError("{!r} is not a tfpackage frozen module".format(fullname), name=fullname)
        return None

    @classmethod
    def is_package(cls, fullname):
        # type: (str) -> bool
        """Return True if the frozen module is a package."""
        if not tfloader.is_tfpackage_frozen(fullname):
            raise ImportError("{!r} is not a tfpackage frozen module".format(fullname), name=fullname)
        return tfloader.is_tfpackage_frozen_package(fullname)


def install():
    # () -> None
    """
    Install TfpackageFrozenImporter to sys.meta_path
    """
    if is_installed():
        return
    sys.meta_path.append(TfpackageFrozenImporter)


def is_installed():
    # () -> bool
    return any(meta_finder is TfpackageFrozenImporter for meta_finder in sys.meta_path)

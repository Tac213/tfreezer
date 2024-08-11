import typing
import win32api
import win32com.client
import win32gui
from win32com.shell import shell, shellcon
from win32com.server.policy import DesignatedWrapPolicy
import pythoncom
import pywintypes


class FileOperationProgressSink(DesignatedWrapPolicy):
    _com_interfaces_ = [shell.IID_IFileOperationProgressSink]
    _public_methods_ = [
        "StartOperations",
        "FinishOperations",
        "PreRenameItem",
        "PostRenameItem",
        "PreMoveItem",
        "PostMoveItem",
        "PreCopyItem",
        "PostCopyItem",
        "PreDeleteItem",
        "PostDeleteItem",
        "PreNewItem",
        "PostNewItem",
        "UpdateProgress",
        "ResetTimer",
        "PauseTimer",
        "ResumeTimer",
    ]

    def __init__(self):
        self._wrap_(self)
        self.newItem = None

    def PreDeleteItem(self, flags, item):
        # Can detect cases where to stop via flags and condition below, however the operation
        # does not actual stop, we can resort to raising an exception as that does stop things
        # but that may need some additional considerations before implementing.
        return 0 if flags & shellcon.TSF_DELETE_RECYCLE_IF_POSSIBLE else 0x80004005  # S_OK, or E_FAIL

    def PostDeleteItem(self, flags, item, hr_delete, newly_created):
        if newly_created:
            self.newItem = newly_created.GetDisplayName(shellcon.SHGDN_FORPARSING)


def create_sink():
    return pythoncom.WrapObject(FileOperationProgressSink(), shell.IID_IFileOperationProgressSink)


def send2trash(paths: typing.Iterable[str]) -> None:
    # Need to initialize the com before using
    pythoncom.CoInitialize()
    # create instance of file operation object
    fileop = pythoncom.CoCreateInstance(
        shell.CLSID_FileOperation,
        None,
        pythoncom.CLSCTX_ALL,
        shell.IID_IFileOperation,
    )
    # default flags to use
    flags = shellcon.FOF_NOCONFIRMATION | shellcon.FOF_NOERRORUI | shellcon.FOF_SILENT | shellcon.FOFX_EARLYFAILURE
    # determine rest of the flags based on OS version
    # use newer recommended flags if available
    flags |= 0x20000000 | 0x00080000  # FOFX_ADDUNDORECORD win 8+  # FOFX_RECYCLEONDELETE win 8+
    # set the flags
    fileop.SetOperationFlags(flags)
    # actually try to perform the operation, this section may throw a
    # pywintypes.com_error which does not seem to create as nice of an
    # error as OSError so wrapping with try to convert
    sink = create_sink()
    try:
        for path in paths:
            item = shell.SHCreateItemFromParsingName(path, None, shell.IID_IShellItem)
            fileop.DeleteItem(item, sink)
        result = fileop.PerformOperations()
        aborted = fileop.GetAnyOperationsAborted()
        # if non-zero result or aborted throw an exception
        if result or aborted:
            raise OSError(None, None, paths, result)
    except pywintypes.com_error as error:
        # convert to standard OS error, allows other code to get a
        # normal errno
        raise OSError(None, error.strerror, path, error.hresult)
    finally:
        # Need to make sure we call this once fore every init
        pythoncom.CoUninitialize()


win32api.MessageBox(0, "Hello,pywin32!", "pywin32")
calc = win32com.client.Dispatch("WScript.Shell")
calc.Run("calc.exe")

hwnd = None
while hwnd is None:
    hwnd = win32gui.FindWindow(None, "Calculator")

calc_hwnd = hwnd

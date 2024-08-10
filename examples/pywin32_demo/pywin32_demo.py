import win32api
import win32com.client
import win32gui

win32api.MessageBox(0, "Hello,pywin32!", "pywin32")
calc = win32com.client.Dispatch("WScript.Shell")
calc.Run("calc.exe")

hwnd = None
while hwnd is None:
    hwnd = win32gui.FindWindow(None, "Calculator")

calc_hwnd = hwnd

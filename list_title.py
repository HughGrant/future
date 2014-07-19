# coding:utf-8
import ctypes

find_window = ctypes.windll.user32.FindWindowW
set_foreground_window = ctypes.windll.user32.SetForegroundWindow
open_clipboard = ctypes.windll.user32.OpenClipboard
empty_clipboard = ctypes.windll.user32.EmptyClipboard
set_clipboard_data = ctypes.windll.user32.SetClipboardData
get_last_error = ctypes.windll.kernel32.GetLastError
# EnumWindows = ctypes.windll.user32.EnumWindows
# EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
# GetWindowText = ctypes.windll.user32.GetWindowTextW
# GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
# IsWindowVisible = ctypes.windll.user32.IsWindowVisible
# SendMessageA = ctypes.windll.user32.SendMessageA
# FindWindowA = ctypes.windll.user32.FindWindowA

# titles = []
# def foreach_window(hwnd, lParam):
# 	if IsWindowVisible(hwnd):
# 		length = GetWindowTextLength(hwnd)
# 		buff = ctypes.create_unicode_buffer(length + 1)
# 		GetWindowText(hwnd, buff, length + 1)
# 		titles.append(buff.value)
# 		if u'test.txt' in buff.value:
# 			SendMessageA(hwnd, 45, 0, 0)
# 		return True
# EnumWindows(EnumWindowsProc(foreach_window), 0)

# print titles

# 打开 u'\u6253\u5f00':
# title = 'test.txt - \u8bb0\u4e8b\u672c'
title = u'test.txt - 记事本'
hwnd = find_window(0, title)
set_foreground_window(hwnd)
open_clipboard(0)
empty_clipboard()
ctypes.windll.user32.CloseClipboard()
get_last_error()
# ctypes.windll.user32.SendMessageW(hwnd, 0, 0, 0)
# print hwnd
# print title
# hwnd = FindWindowA(0, title)
# print hwnd

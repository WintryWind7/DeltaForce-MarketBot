# distutils: language = c++
# distutils: libraries = user32 gdi32

from libc.stdint cimport uintptr_t
from cpython cimport PyObject, Py_INCREF
from libc.stdlib cimport malloc, free

# Define wchar_t type
cdef extern from *:
    ctypedef unsigned short wchar_t

# Standard C headers
cdef extern from "wchar.h":
    pass
cdef extern from "stdlib.h":
    pass

# Windows API types and constants
cdef extern from "windows.h":
    ctypedef void* HWND
    ctypedef void* HANDLE
    ctypedef void* HMODULE
    ctypedef unsigned long DWORD
    ctypedef long LPARAM
    ctypedef int BOOL
    ctypedef wchar_t* LPWSTR
    ctypedef DWORD* LPDWORD
    
    cdef enum:
        FALSE = 0
        TRUE = 1
        MAX_PATH = 260
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
    
    ctypedef struct RECT:
        long left
        long top
        long right
        long bottom

    HWND GetForegroundWindow()
    HWND FindWindowW(const wchar_t* lpClassName, const wchar_t* lpWindowName)
    int GetWindowRect(HWND hWnd, RECT* lpRect)
    int GetClientRect(HWND hWnd, RECT* lpRect)
    int GetSystemMetrics(int nIndex)
    int GetWindowTextLengthW(HWND hWnd)
    int GetWindowTextW(HWND hWnd, LPWSTR lpString, int nMaxCount)
    DWORD GetWindowThreadProcessId(HWND hWnd, LPDWORD lpdwProcessId)
    HANDLE OpenProcess(DWORD dwDesiredAccess, BOOL bInheritHandle, DWORD dwProcessId)
    BOOL CloseHandle(HANDLE hObject)
    ctypedef BOOL (*WNDENUMPROC)(HWND, LPARAM)
    BOOL EnumWindows(WNDENUMPROC lpEnumFunc, LPARAM lParam)
    BOOL IsWindowVisible(HWND hWnd)
    wchar_t* wcsrchr(const wchar_t* str, wchar_t ch)
    HWND FindWindowEx(HWND hWndParent, HWND hWndChildAfter, const wchar_t* lpszClass, const wchar_t* lpszWindow)

    # Constants for GetSystemMetrics
    int SM_CXSCREEN
    int SM_CYSCREEN



cdef extern from "psapi.h":
    DWORD GetModuleFileNameExW(HANDLE hProcess, HANDLE hModule, LPWSTR lpFilename, DWORD nSize)

# Python C API functions
cdef extern from "Python.h":
    object PyLong_FromVoidPtr(void* ptr)
    wchar_t* PyUnicode_AsWideCharString(object, Py_ssize_t*)
    object PyUnicode_FromWideChar(const wchar_t*, Py_ssize_t)
    void PyMem_Free(void *ptr)

def get_foreground_window():
    """获取当前前台窗口的句柄"""
    cdef HWND hwnd = GetForegroundWindow()
    return PyLong_FromVoidPtr(<void*>hwnd)

def get_window_info(window_handle):
    """获取指定窗口的信息(位置、大小等)
    
    参数:
        window_handle: 窗口句柄
        
    返回:
        dict: 包含窗口位置和尺寸信息的字典
    """
    cdef RECT rect
    cdef HWND hwnd = <HWND><uintptr_t>window_handle
    
    if not GetWindowRect(hwnd, &rect):
        raise WindowsError("无法获取窗口矩形")
    
    # 直接返回物理坐标，不进行 DPI 缩放
    return {
        'left': rect.left,
        'top': rect.top,
        'right': rect.right,
        'bottom': rect.bottom,
        'width': rect.right - rect.left,
        'height': rect.bottom - rect.top
    }



def get_screen_resolution():
    """获取当前主显示器的屏幕分辨率
    
    返回:
        tuple: (width, height) 屏幕分辨率
    """
    cdef int width = GetSystemMetrics(SM_CXSCREEN)
    cdef int height = GetSystemMetrics(SM_CYSCREEN)
    return (width, height)

def find_window_by_name(class_name=None, window_name=None):
    """通过类名和/或窗口名查找窗口
    
    参数:
        class_name (str): 窗口类名(可选)
        window_name (str): 窗口标题(可选)
        
    返回:
        窗口句柄或None(如果未找到)
    """
    cdef HWND hwnd = <HWND>0
    cdef wchar_t* w_class_name = <wchar_t*>0
    cdef wchar_t* w_window_name = <wchar_t*>0
    cdef Py_ssize_t length
    
    try:
        if class_name is not None:
            w_class_name = PyUnicode_AsWideCharString(class_name, &length)
        if window_name is not None:
            w_window_name = PyUnicode_AsWideCharString(window_name, &length)
        
        hwnd = FindWindowW(w_class_name, w_window_name)
        if hwnd == <HWND>0:
            return None
        
        return PyLong_FromVoidPtr(<void*>hwnd)
    finally:
        if w_class_name != <wchar_t*>0:
            PyMem_Free(<void*>w_class_name)
        if w_window_name != <wchar_t*>0:
            PyMem_Free(<void*>w_window_name)

def get_window_title(window_handle):
    """获取窗口标题
    
    参数:
        window_handle: 窗口句柄
        
    返回:
        str: 窗口标题
    """
    cdef HWND hwnd = <HWND><uintptr_t>window_handle
    cdef int length = GetWindowTextLengthW(hwnd) + 1
    cdef wchar_t* buffer = <wchar_t*>malloc(length * sizeof(wchar_t))
    
    if not buffer:
        raise MemoryError("无法分配内存")
    
    try:
        GetWindowTextW(hwnd, buffer, length)
        title = PyUnicode_FromWideChar(buffer, length-1)
        return title
    finally:
        free(buffer)

def get_process_name(window_handle):
    """获取窗口所属进程名
    
    参数:
        window_handle: 窗口句柄
        
    返回:
        str: 进程名
    """
    cdef HWND hwnd = <HWND><uintptr_t>window_handle
    cdef DWORD pid
    GetWindowThreadProcessId(hwnd, &pid)
    
    cdef HANDLE hProcess = OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
        FALSE,
        pid
    )
    
    if hProcess == <HANDLE>0:
        return ""
    
    cdef wchar_t buffer[MAX_PATH]
    cdef DWORD size = GetModuleFileNameExW(
        hProcess,
        <HMODULE>0,
        buffer,
        <DWORD>MAX_PATH
    )
    
    CloseHandle(hProcess)
    
    if size == 0:
        return ""
    
    # 提取文件名部分
    cdef wchar_t* last_slash = wcsrchr(buffer, ord('\\'))
    if last_slash:
        process_name = PyUnicode_FromWideChar(last_slash + 1, -1)
    else:
        process_name = PyUnicode_FromWideChar(buffer, -1)
    return process_name

# 全局变量用于存储枚举结果
cdef list g_windows_list = []

cdef BOOL enum_windows_callback(HWND hwnd, LPARAM lParam) noexcept:
    """窗口枚举回调函数"""
    if IsWindowVisible(hwnd):
        py_hwnd = PyLong_FromVoidPtr(<void*>hwnd)
        title = get_window_title(py_hwnd)
        if title:  # 只显示有标题的窗口
            process = get_process_name(py_hwnd)
            g_windows_list.append((py_hwnd, title, process))
    return TRUE

def enum_windows():
    """枚举所有可见窗口
    
    返回:
        list: 包含(窗口句柄, 窗口标题, 进程名)的元组列表
    """
    global g_windows_list
    g_windows_list = []  # 清空之前的结果
    
    EnumWindows(enum_windows_callback, <LPARAM>0)
    return g_windows_list.copy()

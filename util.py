import math
import re

import time
from typing import Callable, Any

import functools

from colorama import Fore


def async_timed():
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            print(f'starting {func} with args {args} {kwargs}')
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                end = time.time()
                total = end - start
                print(f'finished {func} in {total:.4f} second(s)')

        return wrapped

    return wrapper


def getFileSize(headers):
    """
    extracts content-length from the headers of request
    """
    # TODO: should we check for lower-case 'content-length' also?
    if 'Content-Length' in headers:
        return int(headers['Content-Length'])
    return -1


def getFileName(headers, url: str):
    """
    get file name by first checking the headers in request and if not avlbl, check the url
    :param url: location of file
    :param headers: pass the headers from get request
    """
    # TODO: should we check for lower-case 'content-disposition' also?
    filename = ''
    if "Content-Disposition" in headers:
        filename = re.findall("filename=(.+)", headers["Content-Disposition"])[0]
        if filename.startswith("\"") and filename.endswith("\""):
            filename = filename[1:len(filename) - 1]
        if filename.startswith("\'") and filename.endswith("\'"):
            filename = filename[1:len(filename) - 1]
    else:
        filename = url.split("/")[-1]

    return filename


def isDownloadable(headers):
    """
    Does the url contain a downloadable resource
    """
    content_type = headers.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True


def readable_file_size(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.2f}{suffix}"


def print_progress(chunks, file_size, chunk_size, fetched_size: list, extra_text=""):
    if file_size <= 0:
        _print_progress_no_file_size(chunks, fetched_size, extra_text)
        return

    progress_bar = ""

    BAR_LENGTH = 50
    CHUNK_LENGTH = math.ceil(BAR_LENGTH / chunks)
    LAST_CHUNK_LENGTH = BAR_LENGTH - CHUNK_LENGTH * (chunks - 1)

    last_chunk_size = file_size - chunk_size * (chunks - 1)

    for i in range(chunks - 1):
        chunk_bars = CHUNK_LENGTH * fetched_size[i] // chunk_size
        chunk_str = ("#" * chunk_bars) + Fore.LIGHTBLACK_EX + "#" * (CHUNK_LENGTH - chunk_bars) + Fore.BLACK
        progress_bar += chunk_str

    chunk_bars = math.ceil(LAST_CHUNK_LENGTH * fetched_size[-1] / last_chunk_size)
    chunk_str = ("#" * chunk_bars) + Fore.LIGHTBLACK_EX + ("#" * (LAST_CHUNK_LENGTH - chunk_bars)) + Fore.BLACK
    progress_bar += chunk_str

    progress_bar += f" {extra_text}"
    # clear previously written line:
    print("                                                                      ", end="\r")
    print(progress_bar, end='\r')


def _print_progress_no_file_size(chunks, fetched_size: list, extra_text=""):
    progress_bar = f" {readable_file_size(sum(fetched_size))} {extra_text}"
    # clear previously written line:
    print("                                                                      ", end="\r")
    print(progress_bar, end='\r')

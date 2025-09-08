"""
Common utils
"""
import os
import time
import hashlib
import logging
import functools
from typing import Callable, Union

logger = logging.getLogger("timeit_decorator")


def timeit_decorator(func: Callable) -> Callable:
    """
    Decorator that prints the runtime of the function in seconds.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t_0 = time.time()
        result = func(*args, **kwargs)
        t_1 = time.time()
        call_time_msg = f"function {func.__name__} call time {t_1 - t_0:.3f}s"
        logger.info(call_time_msg)
        return result
    return wrapper


def remove_file(path: str) -> None:
    """
    Removes the file at the given path.
    """
    if os.path.exists(path):
        os.remove(path)
        logger.info("Successfully removed file: %s", path)
    else:
        logger.warning("File removal failed: %s", path)


async def cache_file_locally(file_cache_path: str, data: bytes) -> None:
    """
    Writes the given data to a file at the specified path.
    Handles exceptions for file write operations.
    """
    try:
        with open(file_cache_path, "wb") as file_ptr:
            file_ptr.write(data)
    except IOError as e:
        logger.error("Failed to write data to %s: %s", file_cache_path, e)


def get_file_md5(file: Union[str, bytes], byte_chunk: int = 8192) -> str:
    """
    Calculates the MD5 hash of a file from its path or byte contents.
    Raises NotImplementedError for unsupported file types.

    byte_chunk (int): size of bytes to read and update
    Returns: The MD5 hash of the file (str).
    """
    hash_md5 = hashlib.md5()
    if isinstance(file, str):    # if file is a filepath
        with open(file, "rb") as f_ptr:
            for chunk in iter(lambda: f_ptr.read(byte_chunk), b""):
                hash_md5.update(chunk)
    elif isinstance(file, bytes):  # if file is the file byte contents
        hash_md5.update(file)
    else:
        error_msg = f"MD5 calculation is not supported for file type {type(file)}"
        logger.error(error_msg)
        raise NotImplementedError(error_msg)
    return hash_md5.hexdigest()


def parse_num_str(string: str):
    """
    Parses a string to possibly extract a number.
    Returns: The parsed number (int or float or the original if conversion not possible).
    """
    v = string
    for conv in (int, float):
        try:
            v = conv(string)
            break
        except ValueError:
            continue
    return v

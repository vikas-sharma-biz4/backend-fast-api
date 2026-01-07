"""
File reading utilities.
Demonstrates generator pattern for reading large files line by line.
"""
from typing import Generator, Iterator
from pathlib import Path
import asyncio
from typing import AsyncGenerator


def read_large_file_line_by_line(file_path: str | Path) -> Generator[str, None, None]:
    """
    Generator function to read a large file line by line.
    This is memory-efficient as it doesn't load the entire file into memory.
    
    Example:
        for line in read_large_file_line_by_line("large_file.txt"):
            process(line)
    
    Args:
        file_path: Path to the file to read
        
    Yields:
        Each line of the file as a string
    """
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path_obj, "r", encoding="utf-8") as file:
        for line in file:
            # Yield line with trailing whitespace removed
            yield line.rstrip("\n\r")


async def read_large_file_async(
    file_path: str | Path,
    chunk_size: int = 8192,
) -> AsyncGenerator[str, None]:
    """
    Async generator to read a large file line by line.
    Uses asyncio for non-blocking I/O operations.
    
    Args:
        file_path: Path to the file to read
        chunk_size: Size of chunks to read from file
        
    Yields:
        Each line of the file as a string
    """
    file_path_obj = Path(file_path)
    
    if not file_path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    loop = asyncio.get_event_loop()
    
    def _read_file() -> Iterator[str]:
        with open(file_path_obj, "r", encoding="utf-8") as file:
            for line in file:
                yield line.rstrip("\n\r")
    
    # Run file reading in executor to avoid blocking event loop
    iterator = await loop.run_in_executor(None, lambda: iter(_read_file()))
    
    buffer = ""
    while True:
        chunk = await loop.run_in_executor(
            None,
            lambda: next(iterator, None),
        )
        
        if chunk is None:
            if buffer:
                yield buffer
            break
        
        buffer += chunk
        
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            yield line


def count_lines_in_file(file_path: str | Path) -> int:
    """
    Count lines in a file using the generator pattern.
    Memory-efficient for large files.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Number of lines in the file
    """
    count = 0
    for _ in read_large_file_line_by_line(file_path):
        count += 1
    return count


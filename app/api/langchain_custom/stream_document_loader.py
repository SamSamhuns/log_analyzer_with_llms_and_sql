import asyncio
from typing import Iterator, AsyncIterator
from io import StringIO

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document


class CustomStreamDocumentLoader(BaseLoader):
    """A document loader that reads from a file stream line by line."""

    def __init__(self, file_content: bytes, encoding: str = "utf-8") -> None:
        """Initialize the loader with file content as bytes.

        Args:
            file_content: The content of the file as bytes.
            encoding: encoding of the file content.
        """
        self.file_stream = StringIO(file_content.decode(encoding))

    def lazy_load(self) -> Iterator[Document]:
        """A lazy loader that reads from a file stream line by line synchronously."""
        line_number = 0
        line = self.file_stream.readline()
        while line:
            yield Document(
                page_content=line,
                metadata={"line_number": line_number, "source": "stream"},
            )
            line_number += 1
            line = self.file_stream.readline()
        self.file_stream.close()

    async def alazy_load(self) -> AsyncIterator[Document]:
        """
        An async lazy loader that reads from a file stream line by line asynchronously.
        WARNING; This is just simulating asynchronous behavior.
        """
        line_number = 0
        line = self.file_stream.readline()
        while line:
            await asyncio.sleep(0)  # simulate asynchronous behavior
            yield Document(
                page_content=line,
                metadata={"line_number": line_number, "source": "stream"},
            )
            line_number += 1
            line = self.file_stream.readline()
        self.file_stream.close()

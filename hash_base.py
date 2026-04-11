"""
Base class for student hash function submissions.

Students must subclass HashFunction and implement:
    - name()       -> str:   a display name
    - digest_size  -> int:   output size in bytes (must be 32 for 256-bit)
    - _compress(data: bytes) -> bytes:  the actual hash computation

Input will be arbitrary bytes. Output must be exactly digest_size bytes.
"""

from abc import ABC, abstractmethod


class HashFunction(ABC):
    """Abstract base class that all student submissions must extend."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a short display name for this hash function."""
        ...

    @property
    def digest_size(self) -> int:
        """Output size in bytes. Override if not 32 (256-bit)."""
        return 32

    @abstractmethod
    def _compress(self, data: bytes) -> bytes:
        """
        Core hash computation. Must return exactly self.digest_size bytes.
        """
        ...

    def hash(self, data: bytes) -> bytes:
        """Hash arbitrary input bytes. Do not override."""
        if not isinstance(data, bytes):
            raise TypeError(f"Input must be bytes, got {type(data).__name__}")
        result = self._compress(data)
        if len(result) != self.digest_size:
            raise ValueError(
                f"{self.name}: expected {self.digest_size} bytes output, got {len(result)}"
            )
        return result

    def hexdigest(self, data: bytes) -> str:
        """Return hex-encoded hash."""
        return self.hash(data).hex()

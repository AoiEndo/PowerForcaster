"""Compatibility shim for `imghdr` module when missing in the runtime.

Provides a minimal `what()` implementation detecting common image types
by magic bytes. This is sufficient for Streamlit's basic image handling.
"""
from typing import Optional


def what(file, h: Optional[bytes] = None) -> Optional[str]:
    """Return a string describing the image type, or None if unknown.

    Args:
        file: filename or file-like object. If `h` is provided, `file` may be ignored.
        h: optional initial bytes of the file.
    """
    head = None
    try:
        if h:
            head = h[:32]
        else:
            if isinstance(file, (bytes, bytearray)):
                head = bytes(file[:32])
            elif isinstance(file, str):
                with open(file, "rb") as f:
                    head = f.read(32)
            else:
                # file-like
                try:
                    pos = file.tell()
                except Exception:
                    pos = None
                head = file.read(32)
                try:
                    if pos is not None:
                        file.seek(pos)
                except Exception:
                    pass
    except Exception:
        return None

    if not head:
        return None

    if head.startswith(b"\xff\xd8"):
        return "jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head[:4] == b"GIF8":
        return "gif"
    if head.startswith(b"BM"):
        return "bmp"
    if head[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    # WEBP: 'RIFF'....'WEBP' at offset 8
    if head.startswith(b"RIFF") and len(head) >= 12 and head[8:12] == b"WEBP":
        return "webp"

    return None

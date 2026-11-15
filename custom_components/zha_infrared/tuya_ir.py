"""Tuya / Zosung IR timing compression and base64 encoding."""

from __future__ import annotations

import base64
import struct


def _emit_literal_blocks(out: bytearray, data: bytes) -> None:
    """Emit one or more literal blocks (max 32 bytes each)."""
    for i in range(0, len(data), 32):
        chunk = data[i : i + 32]
        out.append(len(chunk) - 1)
        out.extend(chunk)


def _emit_distance_block(out: bytearray, length: int, distance: int) -> None:
    """Emit an LZ77 distance backreference block."""
    d = distance - 1
    l = length - 2
    if l >= 7:
        out.append((7 << 5) | (d >> 8))
        out.append(l - 7)
        out.append(d & 0xFF)
    else:
        out.append((l << 5) | (d >> 8))
        out.append(d & 0xFF)


def compress_tuya_stream(data: bytes) -> bytes:
    """Compress raw little-endian uint16 timing bytes using Tuya's LZ77 format."""
    out = bytearray()
    n = len(data)
    pos = 0
    lit_start = 0

    max_dist = 1 << 13  # 8192
    max_len = 264  # 2 + 7 + 255

    while pos < n:
        best_len = 0
        best_dist = 0
        win_start = max(0, pos - max_dist)
        if pos + 3 <= n:
            target = data[pos : pos + 3]
            search_end = pos
            while True:
                idx = data.rfind(target, win_start, search_end)
                if idx == -1:
                    break
                match_len = 3
                limit = min(max_len, n - pos)
                while (
                    match_len < limit
                    and data[idx + match_len] == data[pos + match_len]
                ):
                    match_len += 1
                if match_len > best_len:
                    best_len = match_len
                    best_dist = pos - idx
                    if best_len == limit:
                        break
                search_end = idx + 2

        if best_len >= 3:
            if pos > lit_start:
                _emit_literal_blocks(out, data[lit_start:pos])
            _emit_distance_block(out, best_len, best_dist)
            pos += best_len
            lit_start = pos
        else:
            pos += 1

    if n > lit_start:
        _emit_literal_blocks(out, data[lit_start:n])

    return bytes(out)


def encode_timings(timings_us: list[int]) -> str:
    """Encode alternating high/low microsecond timings into Zosung base64."""
    raw = b"".join(
        struct.pack("<H", min(max(int(t), 0), 65535)) for t in timings_us
    )
    return base64.b64encode(compress_tuya_stream(raw)).decode("ascii")

"""Minimal, dependency-free NBT writer/reader (Java edition, big-endian, gzip).

Python values are mapped to NBT tags explicitly through small wrapper classes so
that the output is unambiguous (Minecraft is strict about Int vs Byte, etc.).
"""
import gzip
import io
import struct

TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG, TAG_FLOAT, TAG_DOUBLE = 0, 1, 2, 3, 4, 5, 6
TAG_BYTE_ARRAY, TAG_STRING, TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = 7, 8, 9, 10, 11, 12


class Tag:
    tag_id = None

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return type(self) is type(other) and self.value == other.value

    def __repr__(self):
        return f"{type(self).__name__}({self.value!r})"


class Byte(Tag): tag_id = TAG_BYTE
class Short(Tag): tag_id = TAG_SHORT
class Int(Tag): tag_id = TAG_INT
class Long(Tag): tag_id = TAG_LONG
class Float(Tag): tag_id = TAG_FLOAT
class Double(Tag): tag_id = TAG_DOUBLE
class String(Tag): tag_id = TAG_STRING
class IntArray(Tag): tag_id = TAG_INT_ARRAY


class List(Tag):
    tag_id = TAG_LIST

    def __init__(self, value, elem_type=None):
        super().__init__(list(value))
        if elem_type is None:
            elem_type = type(self.value[0]) if self.value else None
        self.elem_type = elem_type


class Compound(Tag):
    tag_id = TAG_COMPOUND

    def __init__(self, value=None):
        super().__init__(dict(value or {}))


def wrap(v):
    """Convert plain Python values to tags with sensible defaults."""
    if isinstance(v, Tag):
        return v
    if isinstance(v, bool):
        return Byte(1 if v else 0)
    if isinstance(v, int):
        return Int(v)
    if isinstance(v, float):
        return Double(v)
    if isinstance(v, str):
        return String(v)
    if isinstance(v, dict):
        return Compound({k: wrap(x) for k, x in v.items()})
    if isinstance(v, (list, tuple)):
        items = [wrap(x) for x in v]
        return List(items, type(items[0]) if items else Compound)
    raise TypeError(f"cannot convert {v!r} to NBT")


def _write_payload(out, tag):
    t = tag.tag_id
    if t == TAG_BYTE:
        out.write(struct.pack(">b", tag.value))
    elif t == TAG_SHORT:
        out.write(struct.pack(">h", tag.value))
    elif t == TAG_INT:
        out.write(struct.pack(">i", tag.value))
    elif t == TAG_LONG:
        out.write(struct.pack(">q", tag.value))
    elif t == TAG_FLOAT:
        out.write(struct.pack(">f", tag.value))
    elif t == TAG_DOUBLE:
        out.write(struct.pack(">d", tag.value))
    elif t == TAG_STRING:
        data = tag.value.encode("utf-8")
        out.write(struct.pack(">H", len(data)))
        out.write(data)
    elif t == TAG_LIST:
        elem_id = tag.elem_type.tag_id if (tag.value and tag.elem_type) else (
            tag.elem_type.tag_id if tag.elem_type else TAG_END)
        out.write(struct.pack(">bi", elem_id, len(tag.value)))
        for item in tag.value:
            if item.tag_id != elem_id:
                raise TypeError("heterogeneous NBT list")
            _write_payload(out, item)
    elif t == TAG_COMPOUND:
        for name, item in tag.value.items():
            _write_named(out, name, item)
        out.write(b"\x00")
    elif t == TAG_INT_ARRAY:
        out.write(struct.pack(">i", len(tag.value)))
        out.write(struct.pack(f">{len(tag.value)}i", *tag.value))
    else:
        raise TypeError(f"unsupported tag {t}")


def _write_named(out, name, tag):
    out.write(struct.pack(">b", tag.tag_id))
    data = name.encode("utf-8")
    out.write(struct.pack(">H", len(data)))
    out.write(data)
    _write_payload(out, tag)


def dumps(root, name=""):
    buf = io.BytesIO()
    _write_named(buf, name, wrap(root))
    raw = buf.getvalue()
    out = io.BytesIO()
    # mtime=0 keeps the output byte-for-byte reproducible
    with gzip.GzipFile(fileobj=out, mode="wb", mtime=0) as gz:
        gz.write(raw)
    return out.getvalue()


def save(path, root):
    with open(path, "wb") as f:
        f.write(dumps(root))


# ---------------------------------------------------------------- reader (tests)

def _read_payload(inp, t):
    if t == TAG_BYTE:
        return struct.unpack(">b", inp.read(1))[0]
    if t == TAG_SHORT:
        return struct.unpack(">h", inp.read(2))[0]
    if t == TAG_INT:
        return struct.unpack(">i", inp.read(4))[0]
    if t == TAG_LONG:
        return struct.unpack(">q", inp.read(8))[0]
    if t == TAG_FLOAT:
        return struct.unpack(">f", inp.read(4))[0]
    if t == TAG_DOUBLE:
        return struct.unpack(">d", inp.read(8))[0]
    if t == TAG_STRING:
        n = struct.unpack(">H", inp.read(2))[0]
        return inp.read(n).decode("utf-8")
    if t == TAG_LIST:
        et, n = struct.unpack(">bi", inp.read(5))
        return [_read_payload(inp, et) for _ in range(n)]
    if t == TAG_COMPOUND:
        d = {}
        while True:
            ct = struct.unpack(">b", inp.read(1))[0]
            if ct == TAG_END:
                return d
            n = struct.unpack(">H", inp.read(2))[0]
            key = inp.read(n).decode("utf-8")
            d[key] = _read_payload(inp, ct)
    if t == TAG_INT_ARRAY:
        n = struct.unpack(">i", inp.read(4))[0]
        return list(struct.unpack(f">{n}i", inp.read(4 * n)))
    if t == TAG_BYTE_ARRAY:
        n = struct.unpack(">i", inp.read(4))[0]
        return inp.read(n)
    if t == TAG_LONG_ARRAY:
        n = struct.unpack(">i", inp.read(4))[0]
        return list(struct.unpack(f">{n}q", inp.read(8 * n)))
    raise ValueError(f"bad tag {t}")


def load(path):
    with open(path, "rb") as f:
        return loads(f.read())


def loads(data):
    """Read gzipped NBT bytes (as written by ``dumps``) into plain Python values."""
    inp = io.BytesIO(gzip.decompress(data))
    t = struct.unpack(">b", inp.read(1))[0]
    n = struct.unpack(">H", inp.read(2))[0]
    inp.read(n)
    return _read_payload(inp, t)

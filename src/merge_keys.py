from __future__ import annotations

import argparse
from typing import TextIO


AddData = dict[tuple[str, str], str]
RemoveData = dict[tuple[str, str], bool]


def _parse_args():
    parser = argparse.ArgumentParser(description="Read and merge keys.")
    parser.add_argument("src", type=str, help="Source file to read keys from.")
    parser.add_argument("dst", type=str, help="Destination file to store keys to.")
    args = parser.parse_args()
    return args.src, args.dst


def _line_pair(line: str) -> tuple[str, str] | None:
    if line.startswith("#"):
        line = line[1:].strip()

    try:
        p1, p2 = line.split()[:2]
    except ValueError:
        return None
    return p1, p2


def read_src(src: TextIO) -> tuple[AddData, RemoveData]:
    to_add = {}
    to_remove = {}
    for line in src.readlines():
        line = line.strip()
        pair = _line_pair(line)
        if not pair:
            continue

        if line.startswith("#"):
            to_remove[pair] = True
        else:
            to_add[pair] = line
    return to_add, to_remove


def write_dst(dst: TextIO, to_add: AddData, to_remove: RemoveData):
    result = []
    # check existing lines
    for line in dst.readlines():
        line = line.strip()
        pair = _line_pair(line)
        if pair in to_add:
            # replace line with newly added
            result.append(to_add.pop(pair))
        elif pair not in to_remove:
            # leave line as is
            result.append(line)

    # add remaining lines
    for line in to_add.values():
        result.append(line)

    # write result
    dst.seek(0)
    dst.write("\n".join(result))
    dst.truncate()


def read_src_path(src_path: str):
    with open(src_path, mode="r") as src:
        return read_src(src)


def write_dst_path(dst_path: str, to_add: AddData, to_remove: RemoveData):
    with open(dst_path, mode="r+") as dst:
        write_dst(dst, to_add, to_remove)


def main():
    src_path, dst_path = _parse_args()
    to_add, to_remove = read_src_path(src_path)
    write_dst_path(dst_path, to_add, to_remove)


if __name__ == "__main__":
    main()

import argparse
from typing import TextIO


def _parse_args():
    parser = argparse.ArgumentParser(description="Read and merge keys.")
    parser.add_argument("src", type=str, help="Source file to read keys from.")
    parser.add_argument("dst", type=str, help="Destination file to store keys to.")
    args = parser.parse_args()
    return args.src, args.dst


def _line_pair(line: str) -> tuple[str, str] | None:
    try:
        p1, p2 = line.split()[:2]
    except ValueError:
        return None
    return p1, p2


def _parse_src(src: TextIO):
    to_add = {}
    to_remove = {}
    for line in src.readlines():
        line = line.strip()
        if line.startswith("#"):
            pair = _line_pair(line[1:])
            if pair:
                to_remove[pair] = True
        else:
            pair = _line_pair(line)
            if pair:
                to_add[pair] = line
    return to_add, to_remove


def _merge_keys(src: TextIO, dst: TextIO) -> list[str]:
    to_add, to_remove = _parse_src(src)
    result = []
    # check existing lines
    for line in dst.readlines():
        line = line.strip()
        if line.startswith("#"):
            pair = _line_pair(line[1:])
            if pair in to_add:
                # replace line with newly added
                result.append(to_add.pop(pair))
                continue
            elif pair in to_remove:
                # skip line
                continue
        else:
            pair = _line_pair(line)
            if pair in to_remove:
                # skip line
                continue
            elif pair in to_add:
                to_add.pop(pair)
        # leave line as is
        result.append(line)
    # add remaining lines
    for line in to_add.values():
        result.append(line)
    return result


def merge_keys(src: TextIO, dst: TextIO):
    result = _merge_keys(src, dst)
    # write result
    dst.seek(0)
    dst.write("\n".join(result))
    dst.truncate()


def main():
    src_file, dst_file = _parse_args()
    with open(src_file, mode="r") as src:
        with open(dst_file, mode="r+w") as dst:
            merge_keys(src, dst)


if __name__ == "__main__":
    main()

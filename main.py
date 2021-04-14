from pathlib import Path
from collections import namedtuple
from typing import TypeVar, Sequence, Iterable, Iterator, IO
from dataclasses import dataclass
from enum import IntEnum

import struct

T = TypeVar('T')

Distance = namedtuple('Distance', ['cost', 'prev_i', 'prev_j'])
INSERT_COST = 3
DELETE_COST = 3
REPLACE_COST = 2


class OpCode(IntEnum):
    INSERT = 0
    DELETE = 1
    REPLACE = 2


@dataclass
class Operation:
    code: OpCode
    location: int
    new_byte: int


def file_iter(file: IO[T], batch_size: int, exact_batch: bool = False) -> Iterator[bytes]:
    while b := file.read(batch_size):
        if exact_batch:
            assert len(b) == batch_size

        yield b


def levenstein_distance(s1: Sequence[T], s2: Sequence[T]) -> list[list[Distance]]:
    n = len(s1)
    m = len(s2)
    # distance[i][j] is cost of going from s1[0..i] to s2[0..j]
    distance = [[Distance(0, -1, -1) for j in range(m + 1)] for i in range(n + 1)]

    for j in range(1, m + 1):
        distance[0][j] = Distance(distance[0][j - 1].cost + INSERT_COST, 0, j - 1)

    for i in range(1, n + 1):
        distance[i][0] = Distance(distance[i - 1][0].cost + DELETE_COST, i - 1, 0)

        for j in range(1, m + 1):
            if s1[i - 1] != s2[j - 1]:
                distance[i][j] = min(Distance(distance[i - 1][j].cost + DELETE_COST, i - 1, j),
                                     Distance(distance[i][j - 1].cost + INSERT_COST, i, j - 1),
                                     Distance(distance[i - 1][j - 1].cost + REPLACE_COST, i - 1, j - 1),
                                     key=lambda d: d.cost)
            else:
                distance[i][j] = Distance(distance[i - 1][j - 1].cost, i - 1, j - 1)

    return distance


def edit_path(s1: Sequence[T], s2: Sequence[T]) -> Iterable[Operation]:
    distance = levenstein_distance(s1, s2)
    i = len(s1)
    j = len(s2)
    path = []

    while (i, j) != (-1, -1):
        prev_i = distance[i][j].prev_i
        prev_j = distance[i][j].prev_j

        if prev_i == i - 1 and prev_j == j:
            path.append(Operation(OpCode.DELETE, prev_i, 0))
        elif prev_i == i and prev_j == j - 1:
            path.append(Operation(OpCode.INSERT, prev_i, s2[prev_j]))
        elif prev_i == i - 1 and prev_j == j - 1:
            if s1[prev_i] != s2[prev_j]:
                path.append(Operation(OpCode.REPLACE, prev_i, s2[j - 1]))

        i, j = prev_i, prev_j

    return reversed(path)


def calculate_diff(old_filename: Path, new_filename: Path, diff_filename: Path):
    with open(old_filename, 'rb') as f:
        old_data = f.read()

    with open(new_filename, 'rb') as f:
        new_data = f.read()

    with open(diff_filename, 'wb') as f:
        for edit in edit_path(old_data, new_data):
            f.write(bytes([edit.code, *struct.pack('I', edit.location), edit.new_byte]))


def apply_patch(old_filename: Path, patch_filename: Path, out_filename: Path):
    with open(old_filename, 'rb') as old_file, open(patch_filename, 'rb') as patch_file, \
            open(out_filename, 'wb') as out_file:
        edits = [Operation(OpCode(edit_bytes[0]), struct.unpack('I', edit_bytes[1:5])[0], edit_bytes[5]) for edit_bytes
                 in file_iter(patch_file, 6, True)]

        for e in edits:
            print(e)

        old_data = old_file.read()
        data_i = 0
        edit_i = 0

        while data_i < len(old_data) or edit_i < len(edits):
            if edit_i < len(edits) and edits[edit_i].location == data_i:
                edit = edits[edit_i]
                if edit.code == OpCode.REPLACE:
                    out_file.write(bytes([edit.new_byte]))
                    data_i += 1
                elif edit.code == OpCode.INSERT:
                    out_file.write(bytes([edit.new_byte]))
                elif edit.code == OpCode.DELETE:
                    data_i += 1

                edit_i += 1
            elif data_i < len(old_data):
                out_file.write(bytes([old_data[data_i]]))
                data_i += 1


old_f = Path('test1.txt')
new_f = Path('test2.txt')
diff_f = Path('diff.txt')
out_f = Path('out.txt')
calculate_diff(old_f, new_f, diff_f)
apply_patch(old_f, diff_f, out_f)

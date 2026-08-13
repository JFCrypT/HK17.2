import hashlib
import json
from pathlib import Path

from vector_core import recompute_from_vector

VECTOR_FILES = (
    'test_vector_p13.json',
    'test_vector_p251.json',
    'test_vector_p65521.json',
    'test_vector_p4294967279.json',
    'test_vector_p18446744073709551557.json',
)


def first_difference(expected, actual, path='expected'):
    if type(expected) is not type(actual):
        return f'{path}: type mismatch {type(expected).__name__} != {type(actual).__name__}'

    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            return f'{path}: dictionary keys differ'
        for key in expected:
            difference = first_difference(expected[key], actual[key], f'{path}.{key}')
            if difference is not None:
                return difference
        return None

    if isinstance(expected, list):
        if len(expected) != len(actual):
            return f'{path}: length mismatch {len(expected)} != {len(actual)}'
        for index, (e_item, a_item) in enumerate(zip(expected, actual)):
            difference = first_difference(e_item, a_item, f'{path}[{index}]')
            if difference is not None:
                return difference
        return None

    if expected != actual:
        return f'{path}: {expected!r} != {actual!r}'
    return None


def load_checksums(base):
    checksums = {}
    for line in (base / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        digest, filename = line.split(maxsplit=1)
        checksums[filename.strip()] = digest
    return checksums


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    base = Path(__file__).resolve().parent
    checksums = load_checksums(base)
    failures = 0

    print('=' * 100)
    print('HK17.2 CANONICAL TEST VECTOR VALIDATION')
    print('=' * 100)

    for filename in VECTOR_FILES:
        path = base / filename
        expected_hash = checksums.get(filename)
        actual_hash = sha256(path)

        if expected_hash is None or expected_hash != actual_hash:
            failures += 1
            print(f'[FAIL] {filename} (SHA-256 mismatch)')
            continue

        vector = json.loads(path.read_text(encoding='utf-8'))
        calculated = recompute_from_vector(vector)
        expected = vector['expected']
        difference = first_difference(expected, calculated)

        if difference is None:
            print(f'[PASS] {filename}')
        else:
            failures += 1
            print(f'[FAIL] {filename}')
            print('       ' + difference)

    print('=' * 100)
    if failures == 0:
        print('SUCCESS: all five HK17.2 canonical test vectors are intact and reproduce their canonical expected values.')
        return 0

    print(f'FAILURE: {failures} vector(s) failed validation.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())

"""Check write/read/delete permissions on common user folders.

Usage:
    python scripts/check_permissions.py        # test common folders
    python scripts/check_permissions.py --all  # test all top-level folders in the user profile (skips AppData)
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

COMMON = [
    Path.home() / 'Desktop',
    Path.home() / 'Documents',
    Path.home() / 'Downloads',
    Path.home() / 'Pictures',
    Path.home() / 'Music',
    Path.home() / 'Videos',
]

TEST_PREFIX = 'rex_permission_test_' + datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')


def try_write(path: Path) -> tuple[bool, str]:
    path = path.expanduser()
    if not path.exists():
        return False, 'Not found'
    if not path.is_dir():
        return False, 'Not a directory'
    test_file = path / (TEST_PREFIX + '.txt')
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('REX permission test\n')
        # try read
        with open(test_file, 'r', encoding='utf-8') as f:
            _ = f.read()
        # cleanup
        try:
            test_file.unlink()
        except Exception:
            pass
        return True, 'OK'
    except PermissionError:
        return False, 'PermissionError'
    except Exception as e:
        return False, str(e)


def main(all_dirs: bool = False):
    results = []
    targets = []
    if all_dirs:
        # list top-level dirs in user profile, skip AppData
        for p in Path.home().iterdir():
            if p.is_dir() and p.name.lower() != 'appdata':
                targets.append(p)
    else:
        targets = COMMON

    for t in targets:
        ok, msg = try_write(t)
        results.append((str(t), ok, msg))

    ok_count = sum(1 for r in results if r[1])
    print('Permission check results:')
    for path, ok, msg in results:
        status = '✅' if ok else '❌'
        print(f' {status} {path} — {msg}')

    print(f'\nSummary: {ok_count}/{len(results)} writable')
    if ok_count == len(results):
        return 0
    return 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true', help='Test all top-level folders under user profile (skips AppData)')
    args = parser.parse_args()
    rc = main(all_dirs=args.all)
    sys.exit(rc)


def run_check(all_dirs: bool = False) -> str:
    """Run the permission checks and return a textual report."""
    results = []
    targets = []
    if all_dirs:
        for p in Path.home().iterdir():
            if p.is_dir() and p.name.lower() != 'appdata':
                targets.append(p)
    else:
        targets = COMMON

    for t in targets:
        ok, msg = try_write(t)
        results.append((str(t), ok, msg))

    lines = ['Permission check results:']
    ok_count = 0
    for path, ok, msg in results:
        status = 'OK' if ok else 'FAIL'
        lines.append(f'{status} {path} — {msg}')
        if ok:
            ok_count += 1

    lines.append(f'\nSummary: {ok_count}/{len(results)} writable')
    return "\n".join(lines)

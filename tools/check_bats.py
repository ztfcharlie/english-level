# -*- coding: utf-8 -*-
"""Guard the .bat files against LF-only line endings.

cmd.exe mis-parses a batch file saved with bare LF: it drops a character at the
start of the following line, the error compounds down the file, and what you get
is nonsense like `'hich' is not recognized` (from `which`) and `rem`/`echo`
lines fused together. The batch then dies partway with no useful message.

Any editor or tool that rewrites these files as Unix text will reintroduce it,
so this is worth re-running after touching them.

    python check_bats.py          # report
    python check_bats.py --fix    # rewrite as CRLF
"""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bats():
    return sorted(f for f in os.listdir(ROOT) if f.lower().endswith(".bat"))


def main():
    fix = "--fix" in sys.argv
    bad = []
    for name in bats():
        path = os.path.join(ROOT, name)
        blob = io.open(path, "rb").read()
        crlf = blob.count(b"\r\n")
        bare = blob.count(b"\n") - crlf
        if bare:
            bad.append(name)
            if fix:
                # Normalise, then write back so every newline is CRLF.
                fixed = blob.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
                io.open(path, "wb").write(fixed)
                print("FIXED  %-18s %d bare LF -> CRLF" % (name, bare))
            else:
                print("BROKEN %-18s %d bare LF (cmd will mis-parse this)" % (name, bare))
        else:
            print("ok     %-18s %d CRLF" % (name, crlf))

    if bad and not fix:
        print("\n%d file(s) would break under cmd. Re-run with --fix." % len(bad))
        sys.exit(1)
    if not bad:
        print("\nall %d .bat file(s) are CRLF." % len(bats()))


if __name__ == "__main__":
    main()

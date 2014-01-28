#!/usr/bin/env python
import os
import sys

try:
    import pydevd
    pydevd.patch_django_autoreload()
    print >> sys.stderr, "Loaded pydevd for Eclipse autoreload"
except:
    pass

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quiz.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

#!/usr/bin/env python
import os
import sys
reload(sys)
sys.setdefaultencoding("utf8")

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xp.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

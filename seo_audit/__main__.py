# Lets the tool run as `python3 tools/seo_audit <mode> ...` from the repo root.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seo_audit.cli import main  # noqa: E402

sys.exit(main())

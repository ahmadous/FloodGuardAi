from __future__ import annotations

import sys
from pathlib import Path

# Allow running `python app.py` when current working dir is the
# `flood_api/` package folder (common during local development)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flood_api.gateway.app import gateway_app as app


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

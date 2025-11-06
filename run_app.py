#!/usr/bin/env python
"""
AutoSpendTracker - Command line entry point.
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Use absolute import to directly specify the package path
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        # Import the main module from the package
        from autospendtracker.main import main as run_main_application

        # Run the application's main function (main() handles its own logging setup)
        run_main_application()
    except ImportError as e:
        # Provide more detailed error information
        logger.error(f"Error importing autospendtracker package: {e}")
        logger.error(
            "Ensure the package is installed (e.g., 'uv pip install -e .') "
            "and the 'src' directory is correctly structured."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running AutoSpendTracker: {e}", exc_info=True)
        sys.exit(1)

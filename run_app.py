#!/usr/bin/env python
"""
AutoSpendTracker - Command line entry point.
"""

import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting AutoSpendTracker from command line")
    
    try:
        # Use absolute import to directly specify the package path
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

        # More detailed error logging for debugging
        logger.info(f"Python path: {sys.path}")
        logger.info(f"Looking for module in: {os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))}")

        # Import the main module from the package
        from autospendtracker.main import main as run_main_application

        # Run the application's main function (main() handles its own logging setup)
        run_main_application()

        logger.info("AutoSpendTracker command line execution completed")
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

"""
Test speed/ETA display by processing a single file and monitoring logs.
"""

import sys
import logging

# Enable DEBUG logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("Starting app with DEBUG logging enabled...")
print("Watch for 'Progress update:' and 'Speed calculation:' messages")
print("=" * 80)

# Import and run the app
from main import main
sys.exit(main())

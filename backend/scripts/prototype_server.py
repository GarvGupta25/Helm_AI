"""Normal isolated preview: configured real delivery; never force console mode."""
import runpy
import sys
from pathlib import Path

if __name__=='__main__':
    sys.argv.append('--allow-configured-sandbox')
    runpy.run_path(str(Path(__file__).with_name('uk_test_server.py')),run_name='__main__')

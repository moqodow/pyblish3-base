import os
import sys

# Expose Pyblish to PYTHONPATH
path = os.path.dirname(__file__)
sys.path.insert(0, path)

import nose2

if __name__ == '__main__':
    argv = sys.argv[:]
    argv.extend(['-c', 'nose2.cfg'])
    nose2.main(argv=argv)

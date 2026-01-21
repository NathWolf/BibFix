#!/usr/bin/env python3
import sys
import os

# Add the current directory to python path so we can import bibfixer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bibfixer.cli import main

if __name__ == "__main__":
    main()

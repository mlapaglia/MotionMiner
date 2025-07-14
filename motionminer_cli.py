#!/usr/bin/env python3
"""
MotionMiner CLI Entry Point

This script serves as the entry point for the MotionMiner command-line interface.
It can be used directly or as a console script when the package is installed.
"""

import sys
from motionminer.main import MotionPhotoProcessor

def main():
    """Main entry point for the CLI"""
    processor = MotionPhotoProcessor()
    exit_code = processor.run()
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 
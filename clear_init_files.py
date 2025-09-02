#!/usr/bin/env python3
"""Script to clear all __init__.py files in the src directory."""

import os
from pathlib import Path


def clear_init_files():
    """Clear the content of all __init__.py files in the src directory."""
    src_dir = Path("src")
    
    if not src_dir.exists():
        print("src directory not found!")
        return
    
    init_files = list(src_dir.rglob("__init__.py"))
    print(f"Found {len(init_files)} __init__.py files")
    
    cleared_count = 0
    for init_file in init_files:
        try:
            # Clear the file content
            init_file.write_text("")
            cleared_count += 1
            print(f"Cleared: {init_file}")
        except Exception as e:
            print(f"Error clearing {init_file}: {e}")
    
    print(f"\nSuccessfully cleared {cleared_count} __init__.py files")


if __name__ == "__main__":
    clear_init_files()

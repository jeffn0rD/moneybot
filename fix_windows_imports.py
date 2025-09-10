#!/usr/bin/env python3
"""
Fix Windows import issues by updating all Python files with proper path handling.
"""

import os
import re
import sys
from pathlib import Path

def fix_imports(file_path):
    """Add proper path handling to Python files."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add path handling if not already present
    if 'sys.path.insert' not in content:
        path_fix = '''import sys
import os
from pathlib import Path

# Add the project root to Python path for cross-platform compatibility
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

'''
        
        # Find the first import and insert after it
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                lines.insert(i, path_fix)
                break
        
        new_content = '\n'.join(lines)
        
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Fixed imports in {file_path}")

# Files to fix
files_to_fix = [
    'libs/models/train_meta.py',
    'backtester/engine.py',
    'apps/orchestrator/main.py'
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        fix_imports(file_path)

print("✅ Windows compatibility fixes applied!")
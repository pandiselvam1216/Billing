import sys
import os

# Add the parent directory to the path so it can find 'app.py'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

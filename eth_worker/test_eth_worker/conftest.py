import os, sys
# Add config
source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(source_path)

# Add src
source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
sys.path.append(source_path)

# Add helpers directory - pytest doesn't recommend packages in test dir
source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./helpers"))
sys.path.append(source_path)
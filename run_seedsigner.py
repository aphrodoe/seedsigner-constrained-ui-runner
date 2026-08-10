#!/usr/bin/env python3
import sys
import os

print("Starting SeedSigner Constrained UI Runner...")

# 1. Add upstream SeedSigner src directory to Python path
# This allows 'import seedsigner' to resolve correctly
upstream_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vendor', 'seedsigner', 'src')
if not os.path.exists(upstream_src):
    print(f"Error: Upstream SeedSigner not found at {upstream_src}")
    print("Please run ./setup.sh first to clone the git submodule.")
    sys.exit(1)

sys.path.insert(0, upstream_src)

# 2. Initialize our custom UI interceptor
# This monkeypatches the SeedSigner Screen/View layer and physical inputs
# BEFORE the upstream controller starts.
try:
    import src.constrained_text_screens
    
    # Inject our module into sys.modules so upstream LVGL imports resolve to us
    sys.modules['seedsigner_lvgl_screens'] = src.constrained_text_screens
    sys.modules['seedsigner_lvgl'] = src.constrained_text_screens
    
    src.constrained_text_screens.init()
except Exception as e:
    print(f"Failed to initialize Constrained UI Runner: {e}")
    sys.exit(1)

# 3. Start the upstream SeedSigner OS
try:
    import main
    print("Handing over to upstream SeedSigner Controller...")
    main.main()
except KeyboardInterrupt:
    print("\nShutting down SeedSigner.")
    sys.exit(0)

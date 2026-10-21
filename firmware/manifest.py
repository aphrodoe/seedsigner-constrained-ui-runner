# Frozen into the firmware: MicroPython's defaults, Keith's two shims that extend
# hashlib/hmac with the native SHA-512 primitives, embit, and -- when staged -- the
# SeedSigner app. Mirrors the P4 boards' manifest in seedsigner-micropython-builder.
#
# Frozen rather than copied to the filesystem so the bytecode lives in flash and
# costs no RAM: the configuration a signing firmware ships, and the one memory
# measurements need to reflect.
#
# Relative paths resolve against this file. ponytail: the sources come from the
# sibling seedsigner-micropython-builder checkout, same as crypto.cmake.
include("$(PORT_DIR)/boards/manifest.py")

_B = "../../seedsigner-micropython-builder"

require("logging")
module("hashlib.py", base_path=_B + "/deps/third-party")
module("hmac.py", base_path=_B + "/deps/third-party")
# urtypes pulls PSBTs out of UR-encoded QR data; frozen for parity with Keith's
# firmware, since the app imports it.
package("urtypes", base_path=_B + "/deps/third-party")
package("embit", base_path=_B + "/deps/embit/src")

# This repo's text renderer and the bridge SeedSigner's Views talk to. The
# Pillow/smbus2 renderers inside it are only imported lazily, by
# DisplayManager.create_renderer(), so freezing the whole package is safe.
# ponytail: frozen as top-level "src"; give it a real package name before D1 ships.
package("src", base_path="..")

# The SeedSigner app, staged by Keith's stager into <builder>/frozen_app/:
#   cd seedsigner-micropython-builder
#   SS_APP_DIR=$PWD/deps/seedsigner SS_EMBIT_DIR=$PWD/deps/embit \
#     python3 tools/stage_frozen_app.py --board SEEDSIGNER_S3_DEVKIT
# Unstaged, package() raises; build without the app rather than fail, as the P4
# manifest does.
try:
    package("seedsigner", base_path=_B + "/frozen_app")
    module("seedsigner_frozen_build.py", base_path=_B + "/frozen_app")
except OSError:
    pass

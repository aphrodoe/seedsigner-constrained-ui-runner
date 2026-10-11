# Frozen into the firmware: MicroPython's defaults, Keith's two shims that extend
# hashlib/hmac with the native SHA-512 primitives, and embit.
#
# embit is frozen rather than copied to the filesystem so its bytecode lives in
# flash and costs no RAM -- the configuration a real signing firmware ships, and
# the one the SRAM measurements need to reflect.
#
# Relative paths resolve against this file. ponytail: the sources come from the
# sibling seedsigner-micropython-builder checkout, same as crypto.cmake.
include("$(PORT_DIR)/boards/manifest.py")

module("hashlib.py", base_path="../../seedsigner-micropython-builder/deps/third-party")
module("hmac.py", base_path="../../seedsigner-micropython-builder/deps/third-party")
package("embit", base_path="../../seedsigner-micropython-builder/deps/embit/src")

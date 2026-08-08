# Airgapped MicroSD Workflow Guide

For hardware devices utilizing the Constrained UI Runner (such as the Raspberry Pi Zero without a camera module), SeedSigner's standard QR-code based data ingestion is impossible. 

To solve this, this runner natively intercepts the SeedSigner OS camera and QR-display hardware calls, securely routing all data ingress (reading PSBTs) and data egress (writing XPUBs and signed PSBTs) through an attached SPI MicroSD card.

This document outlines the exact hardware configuration, environment setup, and testing scripts required to validate the end-to-end airgapped workflow.

## 1. Hardware & System Configuration

### SPI Clock Speed & Kernel Overlays
Due to the constraints of breadboard jumper wires and the standard Arduino-style SD reader modules, running the SPI bus at high frequencies (like 20MHz) will cause kernel `Directory bread` filesystem errors. The SPI bus frequency must be reduced to 5MHz.

Ensure your Pi Zero's `/boot/firmware/config.txt` contains the following overlay configuration:
```text
dtparam=spi=on
dtoverlay=spi0-1cs
dtoverlay=mmc-spi,spi0-0,brm=5000000
```
*(Reboot required after changes).*

### Sudoers I/O Permissions
Because the `seedsigner-constrained-ui-runner` executes within the context of the standard `pi` user (not root), the python script requires passwordless `sudo` privileges to mount and unmount the FAT32 MicroSD filesystem.

Create the file `/etc/sudoers.d/010_seedsigner-sd` on the Pi:
```bash
pi ALL=(root) NOPASSWD: /usr/bin/mount -t vfat -o uid=1000\,gid=1000 /dev/mmcblk2p1 /mnt/sd
pi ALL=(root) NOPASSWD: /usr/bin/umount /mnt/sd
pi ALL=(root) NOPASSWD: /usr/bin/tee /mnt/sd/*
pi ALL=(root) NOPASSWD: /usr/bin/mkdir -p /mnt/sd
pi ALL=(root) NOPASSWD: /usr/bin/mv /mnt/sd/* /mnt/sd/*
```

## 2. Environment Fixes

When running standard SeedSigner OS on a Raspberry Pi using CPython, two critical upstream libraries must be manually installed into your virtual environment (`venv`).

1. **embit**: Used heavily by SeedSigner for Bitcoin cryptographic operations.
2. **urtypes**: SeedSigner's QR encoder natively defaults to the Animated UR format. Even though our runner bypasses the physical display, the upstream `UrPsbtQrEncoder` object will crash upon instantiation if this module is missing.

**Run this in your Pi's SSH terminal:**
```bash
pip install embit
pip install urtypes==1.0.1
```

*Note: The constrained runner automatically monkeypatches `UrPsbtQrEncoder` to avoid crashes caused by the missing `uUR` C-extension, but the python package itself must still be present.*

## 3. End-to-End Workflow Testing

### Scenario D: Exporting an XPUB
To test MicroSD data egress, generate a random 12-word seed in SeedSigner and export the XPUB to the SD card.
1. Insert a FAT32 formatted MicroSD card into the SPI module.
2. Navigate to **Seeds -> [Select your Seed] -> Export Xpub -> Single Sig -> Native Segwit**.
3. Select any QR format (Animated or Static).
4. The screen will instantly display `"Success: XPUB saved to SD Card!"`.
5. Plug the SD card into your laptop to verify that `xpub.txt` exists.

### Generating a Valid Dummy PSBT
Because SeedSigner verifies the cryptographic validity of a PSBT before signing it, you cannot use a randomized dummy file to test the signing workflow. The PSBT's input `bip32_derivations` must contain the exact **Master Fingerprint** of the seed you enter into the device.

To safely test the signing workflow on your laptop without using real funds, run this Python script on your laptop. It uses `embit` to automatically generate a valid 12-word seed and a corresponding perfectly-formatted test PSBT.

**`create_fake_psbt.py`**:
```python
import os
from embit import bip39, bip32, psbt, script, networks, ec, hashes
from embit.transaction import Transaction, TransactionInput, TransactionOutput

# 1. Generate a dummy seed
entropy = os.urandom(16)
mnemonic = bip39.mnemonic_from_bytes(entropy)
print(f"Mnemonic to enter in SeedSigner:\n\n{mnemonic}\n")

# 2. Derive a Native Segwit (P2WPKH) key at m/84'/0'/0'/0/0
seed = bip39.mnemonic_to_seed(mnemonic)
root = bip32.HDKey.from_seed(seed, version=networks.NETWORKS["main"]["xprv"])
xprv = root.derive("m/84'/0'/0'")

child_key = xprv.derive("m/0/0")
pubkey = child_key.sec()
sc = script.Script(b"\x00\x14" + hashes.hash160(pubkey))

# 3. Create a fake previous transaction (UTXO)
prev_tx = Transaction(
    version=2,
    vin=[TransactionInput(b'\x00'*32, 0xFFFFFFFF)],
    vout=[TransactionOutput(100000, sc)]
)
prev_tx.hash() 

# 4. Create the spending transaction
spending_tx = Transaction(
    version=2,
    vin=[TransactionInput(prev_tx.txid(), 0, sequence=0xFFFFFFFF)],
    vout=[TransactionOutput(50000, script.Script(b"\x00\x14" + b"\x22" * 20))]
)

# 5. Build the PSBT
tx = psbt.PSBT(spending_tx)
tx.inputs[0].witness_utxo = prev_tx.vout[0]
# VERY IMPORTANT: Ensure the root master fingerprint is passed here, not the child's!
tx.inputs[0].bip32_derivations = {
    ec.PublicKey.parse(pubkey): psbt.DerivationPath(root.my_fingerprint, [84 + 0x80000000, 0x80000000, 0x80000000, 0, 0])
}

# 6. Save to file
with open('test_tx_valid.psbt', 'wb') as f:
    f.write(tx.serialize())
    
print("Saved valid binary PSBT to test_tx_valid.psbt!")
```

### Scenario B & C: Loading and Signing the PSBT
1. Run the script above on your laptop.
2. Copy the resulting `test_tx_valid.psbt` onto your MicroSD card.
3. Plug the MicroSD card into the Pi Zero.
4. On the SeedSigner UI, navigate to **Seeds -> Enter 12-word seed** and enter the exact 12 words the python script printed to your terminal.
5. Go to **Scan**. The runner will detect the binary `psbt\xff` format on the SD card, encode it into Base64 in-memory, and route it to the decoder.
6. Approve the math screens and click **Sign Transaction**.
7. Because the Seed matches the PSBT's master fingerprint, it will successfully sign the transaction and instantly display `"Success: Signed PSBT saved to SD Card!"`.

You can now plug the MicroSD card back into your laptop and verify that `signed_tx.psbt` exists and contains a valid ECDSA signature!

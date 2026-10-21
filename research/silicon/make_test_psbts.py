"""Generate deterministic test PSBTs for on-device signing benchmarks.

Every input is owned by the fixed BIP39 test mnemonic below, so the device can
actually sign them; a PSBT the seed can't match measures parsing only. Runs on
the host (CPython) against embit.

    PYTHONPATH=<embit>/src python make_test_psbts.py
"""
from embit import bip32, bip39, ec, hashes, psbt, script
from embit.transaction import Transaction, TransactionInput, TransactionOutput

# Standard BIP39 test vector. Never use for real funds.
MNEMONIC = "abandon " * 11 + "about"
H = 0x80000000  # hardened offset


def p2wpkh(pub):
    return script.Script(b"\x00\x14" + hashes.hash160(pub.sec()))


def build(n_inputs):
    root = bip32.HDKey.from_seed(bip39.mnemonic_to_seed(MNEMONIC))
    fpr = root.my_fingerprint
    acct = root.derive("m/84h/0h/0h")

    recv = [acct.derive([0, i]).key.get_public_key() for i in range(n_inputs)]
    change = acct.derive([1, 0]).key.get_public_key()

    # One funding tx paying each receive address 100k sats.
    funding = Transaction(
        version=2,
        vin=[TransactionInput(b"\x00" * 32, 0xFFFFFFFF)],
        vout=[TransactionOutput(100_000, p2wpkh(pk)) for pk in recv],
    )
    txid = funding.txid()

    total = 100_000 * n_inputs
    spend = Transaction(
        version=2,
        vin=[TransactionInput(txid, i, sequence=0xFFFFFFFD) for i in range(n_inputs)],
        vout=[
            TransactionOutput(total // 2, script.Script(b"\x00\x14" + b"\x22" * 20)),
            TransactionOutput(total // 2 - 1_000 * n_inputs, p2wpkh(change)),
        ],
    )

    tx = psbt.PSBT(spend)
    for i, pk in enumerate(recv):
        tx.inputs[i].witness_utxo = funding.vout[i]
        tx.inputs[i].bip32_derivations = {
            pk: psbt.DerivationPath(fpr, [84 + H, 0 + H, 0 + H, 0, i])
        }
    # Change output carries its derivation so the signer can verify it's ours.
    tx.outputs[1].bip32_derivations = {
        change: psbt.DerivationPath(fpr, [84 + H, 0 + H, 0 + H, 1, 0])
    }

    # Sanity: the host can sign every input.
    check = psbt.PSBT.parse(tx.serialize())
    assert check.sign_with(root) == n_inputs, "host could not sign every input"
    return tx.serialize()


if __name__ == "__main__":
    for n in (1, 10):
        raw = build(n)
        name = "psbt_%din.psbt" % n
        with open(name, "wb") as f:
            f.write(raw)
        print("%s  %d bytes" % (name, len(raw)))

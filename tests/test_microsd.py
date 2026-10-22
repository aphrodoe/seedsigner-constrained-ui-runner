"""MicroSD access on the Pi: src/hardware/microsd.py.

The card is how PSBTs cross the air gap, so it gets pulled and swapped between
the device and a laptop. What these pin:

- reading never modifies the card: list/read mount it read-only and never fsck;
- writing is the only read-write mount, and keeps the pre-write fsck repair;
- every operation unmounts afterwards, even on error, so the card is never
  mounted when it's pulled (a read-write mount left in place marks the FAT dirty
  and goes stale across a swap);
- everything else as before: SPI rescan when no card node exists, device probe
  order, sorted/filtered listing, atomic temp-file write, sudo fallbacks.

No hardware: subprocess is recorded, mount/umount flip a fake mount state, and
the mount point is a temp directory standing in for the card.
"""
import os
import subprocess

import pytest

from src.hardware.microsd import MicroSDManager


class FakeSystem:
    def __init__(self, card, devices=("/dev/mmcblk1p1",)):
        self.card = str(card)
        self.devices = set(devices)
        self.mounted = False
        self.mount_opts = None
        self.cmds = []
        self.fail_mount = False
        self.fail_umount = False

    def run(self, cmd, *args, **kwargs):
        self.cmds.append(cmd)
        if isinstance(cmd, list) and cmd[:2] == ["sudo", "mount"]:
            if self.fail_mount:
                raise subprocess.CalledProcessError(32, cmd)
            self.mounted = True
            self.mount_opts = cmd[cmd.index("-o") + 1].split(",")
        elif isinstance(cmd, list) and cmd[:2] == ["sudo", "umount"]:
            if self.fail_umount:
                raise subprocess.CalledProcessError(32, cmd)
            self.mounted = False
        return subprocess.CompletedProcess(cmd, 0)

    def ismount(self, path):
        return path == self.card and self.mounted

    def names(self, prefix):
        """The commands run, as strings, that start with `prefix` (a list)."""
        return [" ".join(c) for c in self.cmds if isinstance(c, list) and c[: len(prefix)] == prefix]


@pytest.fixture
def sd(tmp_path, monkeypatch):
    card = tmp_path / "card"
    card.mkdir()
    fake = FakeSystem(card)
    real_exists = os.path.exists
    monkeypatch.setattr(MicroSDManager, "MOUNT_POINT", str(card))
    monkeypatch.setattr(subprocess, "run", fake.run)
    monkeypatch.setattr(os.path, "ismount", fake.ismount)
    monkeypatch.setattr(os.path, "exists",
                        lambda p: p in fake.devices if p.startswith("/dev/") else real_exists(p))
    monkeypatch.setattr(MicroSDManager, "_rescan_bus", classmethod(lambda cls: fake.cmds.append("rescan")))
    return fake


# --- reading never touches the card -------------------------------------------

def test_list_mounts_read_only_and_never_fscks(sd):
    MicroSDManager.list_files()
    assert "ro" in sd.mount_opts and "rw" not in sd.mount_opts
    assert sd.names(["sudo", "fsck.fat"]) == []


def test_read_mounts_read_only_and_never_fscks(sd):
    open(os.path.join(sd.card, "tx.psbt"), "wb").write(b"psbt\xff")
    assert MicroSDManager.read_file("tx.psbt") == b"psbt\xff"
    assert "ro" in sd.mount_opts
    assert sd.names(["sudo", "fsck.fat"]) == []


# --- writing is the one read-write mount ---------------------------------------

def test_write_mounts_read_write_after_repair(sd):
    MicroSDManager.write_file("signed_tx.psbt", b"signed")
    assert "rw" in sd.mount_opts
    fsck = sd.names(["sudo", "fsck.fat"])
    assert fsck == ["sudo fsck.fat -a -w /dev/mmcblk1p1"]
    assert sd.cmds.index(["sudo", "fsck.fat", "-a", "-w", "/dev/mmcblk1p1"]) < \
        next(i for i, c in enumerate(sd.cmds) if isinstance(c, list) and c[:2] == ["sudo", "mount"])


def test_write_is_atomic_and_synced(sd):
    MicroSDManager.write_file("signed_tx.psbt", b"signed")
    assert open(os.path.join(sd.card, "signed_tx.psbt"), "rb").read() == b"signed"
    assert not os.path.exists(os.path.join(sd.card, "signed_tx.psbt.tmp"))
    assert ["sync"] in sd.cmds


def test_write_text_mode(sd):
    MicroSDManager.write_file("xpub.txt", "xpub6...", binary=False)
    assert open(os.path.join(sd.card, "xpub.txt")).read() == "xpub6..."


def test_write_raises_when_card_wont_mount(sd):
    sd.fail_mount = True
    with pytest.raises(IOError):
        MicroSDManager.write_file("signed_tx.psbt", b"signed")


# --- never left mounted --------------------------------------------------------

@pytest.mark.parametrize("op", [
    lambda: MicroSDManager.list_files(),
    lambda: MicroSDManager.read_file("tx.psbt"),
    lambda: MicroSDManager.write_file("signed_tx.psbt", b"signed"),
], ids=["list", "read", "write"])
def test_unmounted_after_every_operation(sd, op):
    open(os.path.join(sd.card, "tx.psbt"), "wb").write(b"psbt\xff")
    op()
    assert not sd.mounted


def test_unmounted_even_when_read_fails(sd):
    with pytest.raises(OSError):
        MicroSDManager.read_file("missing.psbt")
    assert not sd.mounted


def test_stale_mount_is_replaced_not_reused(sd):
    """A mount left from before (a crash, an older build) may be of a card that's
    since been swapped out. Never reuse it: unmount, then mount fresh."""
    sd.mounted, sd.mount_opts = True, ["rw"]
    MicroSDManager.list_files()
    assert sd.names(["sudo", "umount"])[0] == f"sudo umount {sd.card}"
    assert "ro" in sd.mount_opts


def test_stale_mount_that_wont_unmount_is_never_used(sd):
    sd.mounted, sd.mount_opts, sd.fail_umount = True, ["rw"], True
    with pytest.raises(OSError):
        MicroSDManager.read_file("tx.psbt")
    assert MicroSDManager.list_files() == []
    assert sd.names(["sudo", "mount"]) == []


# --- unchanged behaviour -------------------------------------------------------

def test_list_filters_sorts_and_hides_dotfiles(sd):
    for name in ["b.psbt", "a.PSBT", "notes.txt", "x.json", ".hidden.psbt", "photo.jpg"]:
        open(os.path.join(sd.card, name), "w").close()
    assert MicroSDManager.list_files() == ["a.PSBT", "b.psbt", "notes.txt", "x.json"]


def test_list_returns_empty_when_card_wont_mount(sd):
    sd.fail_mount = True
    assert MicroSDManager.list_files() == []


def test_rescans_spi_bus_only_when_no_card_node_exists(sd):
    MicroSDManager.list_files()
    assert "rescan" not in sd.cmds
    sd.devices = set()
    MicroSDManager.list_files()
    assert "rescan" in sd.cmds


def test_probes_devices_in_order(sd):
    sd.devices = {"/dev/mmcblk1", "/dev/mmcblk2p1"}
    MicroSDManager.list_files()
    assert sd.names(["sudo", "mount"])[0].endswith(f"/dev/mmcblk1 {sd.card}")


def test_keeps_uid_gid_so_the_app_can_write_without_root(sd):
    MicroSDManager.write_file("signed_tx.psbt", b"signed")
    assert {"uid=1000", "gid=1000"} <= set(sd.mount_opts)

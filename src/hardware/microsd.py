import os
import subprocess
import shutil
import time

class MicroSDManager:
    MOUNT_POINT = "/mnt/sd"
    
    @classmethod
    def _rescan_bus(cls):
        """
        SPI SD modules often lack a Card-Detect pin, meaning the kernel won't notice
        if you hot-swap the card (e.g. taking it out to load a PSBT on a laptop).
        This forcefully unbinds and rebinds the spi0.0 device to the mmc_spi driver
        to trigger a kernel re-probe.
        """
        try:
            # Unbind
            subprocess.run("echo spi0.0 | sudo tee /sys/bus/spi/drivers/mmc_spi/unbind", 
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.1)
            # Bind
            subprocess.run("echo spi0.0 | sudo tee /sys/bus/spi/drivers/mmc_spi/bind", 
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5) # Give kernel time to create /dev/mmcblk1
        except Exception:
            pass

    @classmethod
    def is_mounted(cls):
        return os.path.ismount(cls.MOUNT_POINT)
        
    @classmethod
    def mount(cls):
        if cls.is_mounted():
            return True
        if not os.path.exists(cls.MOUNT_POINT):
            try:
                os.makedirs(cls.MOUNT_POINT, exist_ok=True)
            except PermissionError:
                subprocess.run(["sudo", "mkdir", "-p", cls.MOUNT_POINT], check=True)
            
        try:
            # Try once
            devices_to_try = ["/dev/sda1", "/dev/sda", "/dev/mmcblk1p1", "/dev/mmcblk1", "/dev/mmcblk2p1", "/dev/mmcblk2"]
            
            # If none exist, force a kernel rescan of the SPI bus (hot-plug support)
            if not any(os.path.exists(d) for d in devices_to_try):
                cls._rescan_bus()
                
            for dev in devices_to_try:
                if os.path.exists(dev):
                    subprocess.run(["sudo", "mount", dev, cls.MOUNT_POINT], check=True, capture_output=True)
                    if cls.is_mounted():
                        return True
            return False
        except subprocess.CalledProcessError:
            return False
            
    @classmethod
    def unmount(cls):
        if not cls.is_mounted():
            return True
        try:
            # Sync to ensure data is written
            subprocess.run(["sync"], check=True)
            subprocess.run(["sudo", "umount", cls.MOUNT_POINT], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
            
    @classmethod
    def list_files(cls, extensions=(".psbt", ".json", ".txt")):
        if not cls.is_mounted():
            if not cls.mount():
                return [] # Failed to mount
                
        valid_files = []
        try:
            for filename in os.listdir(cls.MOUNT_POINT):
                if not filename.startswith(".") and filename.lower().endswith(extensions):
                    valid_files.append(filename)
        except OSError:
            pass
        return sorted(valid_files)
        
    @classmethod
    def read_file(cls, filename):
        if not cls.is_mounted():
            cls.mount()
            
        filepath = os.path.join(cls.MOUNT_POINT, filename)
        with open(filepath, "rb") as f:
            return f.read()
            
    @classmethod
    def write_file(cls, filename, data, binary=True):
        if not cls.is_mounted():
            if not cls.mount():
                raise IOError("Failed to mount MicroSD card")
                
        filepath = os.path.join(cls.MOUNT_POINT, filename)
        mode = "wb" if binary else "w"
        
        # Write to temporary file then move for atomicity
        temp_filepath = filepath + ".tmp"
        
        # We might need sudo to write if mount is root-owned. Let's try regular write first.
        try:
            with open(temp_filepath, mode) as f:
                f.write(data)
            shutil.move(temp_filepath, filepath)
        except PermissionError:
            # Fallback to sudo tee
            if binary:
                p = subprocess.Popen(["sudo", "tee", temp_filepath], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
                p.communicate(input=data)
            else:
                p = subprocess.Popen(["sudo", "tee", temp_filepath], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
                p.communicate(input=data)
            subprocess.run(["sudo", "mv", temp_filepath, filepath], check=True)
            
        # Ensure it's flushed to disk
        subprocess.run(["sync"], check=True)

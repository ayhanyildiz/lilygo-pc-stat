"""PlatformIO target: python -m platformio run --target package."""
from pathlib import Path
import hashlib
import subprocess

Import("env")


def package_firmware(source, target, env):
    project = Path(env.subst("$PROJECT_DIR"))
    build = Path(env.subst("$BUILD_DIR"))
    framework = Path(env.PioPlatform().get_package_dir("framework-arduinoespressif32"))
    esptool = Path(env.PioPlatform().get_package_dir("tool-esptoolpy")) / "esptool.py"
    destination = project / "firmware" / "tdongle-s3-pc-stat.bin"
    destination.parent.mkdir(exist_ok=True)
    subprocess.run([
        env.subst("$PYTHONEXE"), str(esptool), "--chip", "esp32s3", "merge_bin",
        "--flash_mode", "dio", "--flash_freq", "80m", "--flash_size", "16MB",
        "-o", str(destination),
        "0x0", str(build / "bootloader.bin"),
        "0x8000", str(build / "partitions.bin"),
        "0xe000", str(framework / "tools" / "partitions" / "boot_app0.bin"),
        "0x10000", str(build / "firmware.bin"),
    ], check=True)
    checksum = hashlib.sha256(destination.read_bytes()).hexdigest()
    (destination.parent / "SHA256SUMS").write_text(
        f"{checksum}  {destination.name}\n", encoding="utf-8")
    print(f"Browser firmware ready: {destination}")


env.AddCustomTarget(
    name="package",
    dependencies=["$BUILD_DIR/bootloader.bin", "$BUILD_DIR/partitions.bin",
                  "$BUILD_DIR/${PROGNAME}.bin"],
    actions=[package_firmware],
    title="Package browser firmware",
    description="Merge bootloader, partition table, OTA data and app at address 0x0.",
)

# IMPORTS #
import json
import os
import shutil
import sys
import requests

# CONSTANTS #
vexos_base_url = "https://content.vexrobotics.com/vexos/public/V5/"
vexos_catalog_url = vexos_base_url + "catalog.txt"

# DOWNLOADER FUNCTIONS #
def download_vexos(vexos_version):
    """
    Downloads the VEXos firmware file from the VEX website.

    Args:
        vexos_version (str): The version of VEXos to download.
        path (str): The path to download the file to.
    """
    # Get Download URL
    vexos_download_url = vexos_base_url + vexos_version + ".vexos"

    # Download File
    try:
        vexos_package = requests.get(vexos_download_url)
    except requests.exceptions.ConnectionError:
        raise "ERROR: Failed to download ${vexos_version}. Please check your internet connection."

    # Save File
    try:
        with open("vexos.vexos", "wb") as vexos_file:
            vexos_file.write(vexos_package.content)
    except IOError:
        raise "ERROR: Failed to save ${vexos_version} to file. Please check your permissions."

def extract_vexos():
    """
    Extracts the VEXos firmware file from the VEX website.

    Args:
        path (str): The path to extract the file to.
    """
    # Delete Old Files
    try:
        shutil.rmtree("vexos")
    except IOError:
        pass

    # Extract File
    try:
        shutil.unpack_archive("vexos.vexos", "vexos", "zip")
    except IOError:
        raise "ERROR: Failed to extract VexOS. Please check your permissions."

    # Move contents of extracted folder to vexos folder
    vexos_subfolder = os.listdir("vexos")[0]
    vexos_subfolder_path = os.path.join("vexos", vexos_subfolder)
    for file in os.listdir(vexos_subfolder_path):
        shutil.move(os.path.join(vexos_subfolder_path, file), "vexos")
    shutil.rmtree(vexos_subfolder_path)

    

def get_latest_version():
    """
    Downloads the VEXos catalog file from the VEX website.
    """
    # Download File
    try:
        catalog = requests.get(vexos_catalog_url)
    except requests.exceptions.ConnectionError:
        raise "ERROR: Failed to download catalog. Please check your internet connection."

    # Check if format is valid
    if not catalog.text.startswith("VEXOS_V5_"):
        raise "ERROR: Failed to parse catalog. Please check your internet connection."
    else:
        return catalog.text

# VERSIONING FUNCTIONS #
def vexos_to_semver(version):
    """
    Converts a VEXos version to a SemVer version.
    """
    # Split Version
    version_split = version.split("_")

    # Check if format is valid
    if len(version_split) != 6:
        raise "ERROR: Failed to parse VEXos version. Please try again later."
    if version_split[0] != "VEXOS":
        raise "ERROR: Failed to parse VEXos version. Please try again later."
    if version_split[1] != "V5":
        raise "ERROR: Failed to parse VEXos version. Please try again later."
    
    # Convert to SemVer
    return version_split[2] + "." + version_split[3] + "." + version_split[4] + "." + version_split[5]

def is_outdated(current, latest):
    """
    Checks if a VEXos version is outdated.

    Args:
        current (str): The current VEXos version (semver - manifest).
        latest (str): The latest VEXos version (vexos - catalog).
    """
    current_semver = current.split(".")
    latest_semver = vexos_to_semver(latest).split(".")

    # Check if outdated
    if current_semver[0] > latest_semver[0]:
        return False
    elif current_semver[0] < latest_semver[0]:
        return True

    # Compare minor versions
    if current_semver[1] > latest_semver[1]:
        return False
    elif current_semver[1] < latest_semver[1]:
        return True

    # Compare patch versions
    if current_semver[2] > latest_semver[2]:
        return False
    elif current_semver[2] < latest_semver[2]:
        return True

    # Compare build versions
    if current_semver[3] > latest_semver[3]:
        return False
    elif current_semver[3] < latest_semver[3]:
        return True

    # If all parts are equal, the versions are equal
    return False

def get_installed_version():
    """
    Gets the currently installed VEXos version.
    """
    # Get Installed Version
    try:
        with open("vexos/manifest.json", "r") as manifest_file:
            manifest = manifest_file.read()
    except IOError:
        raise IOError("ERROR: Failed to read manifest.json. Please check your permissions.")

    # Parse JSON
    try:
        manifest = json.loads(manifest)
    except json.JSONDecodeError:
        raise "ERROR: Failed to parse manifest.json. Please check if the file is valid."

    # Get VEXos Version
    try:
        vexos_version = manifest["version"]
    except KeyError:
        raise "ERROR: Failed to parse manifest.json. Please check if the file is valid."

    # Return VEXos Version
    return vexos_version

# Conflict Checker Functions #
def package_already_downloaded():
    """
    Checks if the VEXos package has already been downloaded.
    """
    # Check if File Exists
    try:
        with open("vexos.vexos", "rb") as vexos_file:
            return True
    except IOError:
        return False

def resolve_conflicts():
    """
    Resolves any installation conflicts by deleting the old files.
    """
    # Delete Old Files
    try:
        os.remove("vexos.vexos")
    except IOError:
        pass
    try:
        shutil.rmtree("vexos")
    except IOError:
        pass
    

# INSTALLER FUNCTIONS #
def install_vexos(force, version):
    """
    Installs VEXos.

    Args:
        force (bool): Whether to force the installation of VEXos.
        version (str): The version of VEXos to install.
    """
    # Get Latest Version If Not Specified
    if version == None:
        print("Getting Latest Version...")
        version = get_latest_version()
        print("Latest Version: " + vexos_to_semver(version))
    else:
        print("Version Specified: " + version)
    
    # Get Installed Version
    try:
        installed_version = get_installed_version()
    except IOError:
        installed_version = None
    
    # Check if Outdated (if installed)
    if installed_version != None:
        if not is_outdated(installed_version, version) and not force:
            print("Your VexOS installation is up to date.")
            return
        elif not is_outdated(installed_version, version) and force:
            print("Your VexOS installation is up to date, but continuing anyway.")
        else:
            print("An update is available (currently installed: " + installed_version + ").")
    else:
        print("No VexOS installation found.")
        print("Fresh installation will be performed.")
    
    # Check for conflicts
    conflict = False
    print("Checking for conflicts...")
    if package_already_downloaded():
        print("VexOS package already downloaded.")
        if not force:
            print("Please delete the file and try again.")
            return
        print("Conflicts found. Deleting old files...")
        resolve_conflicts()
    
    # Download VexOS
    print("Downloading VexOS...")
    download_vexos(version)
    print("Downloaded VexOS.")

    # Extract VexOS
    print("Extracting VexOS...")
    extract_vexos()
    print("Extracted VexOS.")

    # Delete VexOS Package
    print("Cleaning up...")
    os.remove("vexos.vexos")
    print("Cleaned up.")

    # Summary
    print("VexOS successfully installed.")
    if installed_version != None:
        print("OLD VERSION: " + installed_version)
    else:
        print("OLD VERSION: None")
    print("NEW VERSION: " + vexos_to_semver(version))    

# MISC FUNCTIONS #
def print_help():
    print("VexOS Downloader (by ThinkAlex)")
    print("Usage: vexos_dl.py [arguments]")
    print("Arguments:")
    print("  -f, --force: Forces the installation of VEXos (even if there are conflicts or no available updates).")
    print("  -v, --version: Installs a specific version of VEXos (format: \"VEXOS_V5_X_X_X_X\").")
    print("  -h, --help: Prints this help message.")
    exit(0)

def main():
    # Parse Arguments
    force_enabled = False
    version = None
    for arg in sys.argv[1:]:
        if arg == "-f" or arg == "--force":
            force_enabled = True
        elif arg == "-v" or arg == "--version":
            version = sys.argv[sys.argv.index(arg) + 1]
            force_enabled = True
        elif arg == "-h" or arg == "--help":
            print_help()
    
    # Install VexOS
    install_vexos(force_enabled, version)

if __name__ == "__main__":
    main()


    

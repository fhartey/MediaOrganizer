import os
import sys
import re
import subprocess

def get_video_resolution(file_path):
    """Extracts video resolution using MediaInfo CLI."""
    try:
        result = subprocess.run(
            ["mediainfo", "--Inform=Video;%Height%", file_path],
            capture_output=True, text=True, check=True
        )
        resolution = result.stdout.strip()
        return int(resolution) if resolution.isdigit() else 0
    except Exception as e:
        print(f"Error getting resolution for {file_path}: {e}")
        return 0  # Return 0 if resolution cannot be determined

def extract_episode_info(filename):
    """Extracts season and episode number (SxxEyyX if present) from filename."""
    match = re.search(r"(S\d{2}E\d{2}[a-z]?)", filename, re.IGNORECASE)
    return match.group(1) if match else None

def find_lower_quality_files(folder_path):
    """Finds lower-quality duplicate videos based on episode number."""
    episode_files = {}
    delete_list = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.wmv')):
                full_path = os.path.join(root, file)
                episode_id = extract_episode_info(file)

                if episode_id:
                    resolution = get_video_resolution(full_path)

                    # Keep highest-resolution file
                    if episode_id not in episode_files or resolution > episode_files[episode_id][1]:
                        if episode_id in episode_files:
                            delete_list.append(episode_files[episode_id][0])
                        episode_files[episode_id] = (full_path, resolution)
                    else:
                        delete_list.append(full_path)

    return delete_list

def remove_episode_letters(folder_path):
    """Renames files to remove any letter after episode numbers (SxxEyyX -> SxxEyy)."""
    renamed_files = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            match = re.search(r"(S\d{2}E\d{2})([a-z])", file, re.IGNORECASE)
            if match:
                new_filename = file.replace(match.group(0), match.group(1))  # Remove the extra letter
                old_path = os.path.join(root, file)
                new_path = os.path.join(root, new_filename)

                # Convert to absolute paths
                old_path = os.path.abspath(old_path)
                new_path = os.path.abspath(new_path)

                # Only rename if the new name does not already exist
                if not os.path.exists(new_path):
                    renamed_files.append((old_path, new_path))

    return renamed_files

def prompt_and_delete(files_to_delete):
    """Displays files to be deleted and asks for user confirmation."""
    if not files_to_delete:
        print("No lower-quality files found for deletion.")
        return

    print("\nThe following lower-quality files will be deleted:\n")
    for file in files_to_delete:
        print(f" - {file}")

    confirm = input("\nDo you want to proceed? (Y/N): ").strip().lower()
    
    if confirm == 'y':
        for file in files_to_delete:
            os.remove(file)
            print(f"Deleted: {file}")
        print("\nDeletion complete.")
    else:
        print("\nOperation canceled. No files were deleted.")

def prompt_and_rename(files_to_rename):
    """Displays files to be renamed and asks for user confirmation."""
    if not files_to_rename:
        print("No files found that need renaming.")
        return

    print("\nThe following files will be renamed:\n")
    for old, new in files_to_rename:
        print(f" - {old} -> {new}")

    confirm = input("\nDo you want to proceed? (Y/N): ").strip().lower()

    if confirm == 'y':
        for old, new in files_to_rename:
            os.rename(old, new)
            print(f"Renamed: {old} -> {new}")
        print("\nRenaming complete.")
    else:
        print("\nOperation canceled. No files were renamed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py /path/to/videos")
        sys.exit(1)

    folder_path = sys.argv[1]
    if not os.path.exists(folder_path):
        print("Error: Path does not exist.")
        sys.exit(1)

    print("\nChoose an option:")
    print("1 - Remove duplicate lower-quality episodes")
    print("2 - Remove any letter next to episode numbers (e.g., S05E03c -> S05E03)")
    choice = input("\nEnter your choice (1 or 2): ").strip()

    if choice == "1":
        files_to_delete = find_lower_quality_files(folder_path)
        prompt_and_delete(files_to_delete)
    elif choice == "2":
        files_to_rename = remove_episode_letters(folder_path)
        prompt_and_rename(files_to_rename)
    else:
        print("\nInvalid choice. Exiting.")

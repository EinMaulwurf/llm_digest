#!/usr/bin/env python3
import os
import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, TextIO, Optional, Callable  # Added Callable for type hints

# Define common text file extensions
DEFAULT_EXTENSIONS = [
    ".txt",
    ".md",
    ".py",
    ".js",
    ".html",
    ".css",
    ".tex",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".sh",
    ".bash",
]
SEPARATOR = "=" * 80  # Noticeable break line


def get_sort_key_function(sort_by: str) -> Callable[[Path], any]:
    """Gets the appropriate key function for sorting Path objects."""
    if sort_by == "ctime":
        # Creation time (or metadata change time on Linux)
        print("Sorting by creation time (st_ctime).")
        return lambda p: p.stat().st_ctime
    elif sort_by == "mtime":
        # Last modification time
        print("Sorting by modification time (st_mtime).")
        return lambda p: p.stat().st_mtime
    elif sort_by == "name":
        # Default: sort by full path string
        print("Sorting by name (full path).")
        return lambda p: str(p)
    else:
        # Fallback, should not happen with argparse choices
        print(
            f"Warning: Unknown sort key '{sort_by}'. Defaulting to sort by name.",
            file=sys.stderr,
        )
        return lambda p: str(p)


def find_text_files(
    directory: Path, extensions: List[str], sort_by: str, reverse: bool
) -> List[Path]:
    """
    Finds all files within a directory and its subdirectories matching the
    given extensions, sorts them based on the specified criteria.

    Args:
        directory: The root directory Path object to search within.
        extensions: A list of lowercase file extensions (e.g., ['.txt', '.md']).
        sort_by: The key to sort by ('name', 'ctime', 'mtime').
        reverse: If True, sort in descending order.

    Returns:
        A sorted list of Path objects for the found files.
    """
    found_files: List[Path] = []
    print(f"Scanning directory: {directory}")
    print(f"Looking for file extensions: {', '.join(extensions)}")
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = Path(root) / filename
            # Check against lowercase filename and extension list
            if file_path.suffix.lower() in extensions:
                # Check if it's actually a file (and not a broken symlink, etc.)
                # and handle potential permission errors early
                try:
                    if file_path.is_file():
                        # Attempt stat to catch permission errors early for sorting keys
                        file_path.stat()
                        found_files.append(file_path)
                    else:
                        print(f"Skipping non-file entry: {file_path}", file=sys.stderr)
                except OSError as e:
                    print(
                        f"Warning: Could not access or stat file {file_path}, skipping: {e}",
                        file=sys.stderr,
                    )
                except Exception as e:  # Catch other potential issues
                    print(
                        f"Warning: Unexpected error checking file {file_path}, skipping: {e}",
                        file=sys.stderr,
                    )

    print(f"Found {len(found_files)} files matching criteria.")

    if not found_files:
        return []

    # Get the sorting key function
    sort_key_func = get_sort_key_function(sort_by)

    # Sort the list
    try:
        found_files.sort(key=sort_key_func, reverse=reverse)
        sort_order = "descending" if reverse else "ascending"
        print(f"Files sorted by '{sort_by}' ({sort_order}).")
    except Exception as e:
        # Catch potential errors during sorting (e.g., stat fails unexpectedly)
        print(
            f"Error during sorting: {e}. Files may be in an unsorted order.",
            file=sys.stderr,
        )
        # Return the list as is, or maybe sort by name as a fallback?
        # Let's try sorting by name as a fallback.
        try:
            print("Falling back to sorting by name.")
            found_files.sort(key=lambda p: str(p), reverse=reverse)
        except Exception as fallback_e:
            print(f"Fallback sort by name also failed: {fallback_e}", file=sys.stderr)

    return found_files


def get_tree_output(directory: Path) -> str:
    """
    Generates the directory tree structure using the 'tree' command.

    Args:
        directory: The directory Path object for which to generate the tree.

    Returns:
        A string containing the tree output, or an error message if
        the 'tree' command fails or is not found.
    """
    try:
        tree_process = subprocess.run(
            ["tree", "."],
            cwd=str(directory),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if tree_process.returncode == 0:
            # Using directory.name might be misleading if '.' is passed
            # Use '.' for relative or the absolute path for clarity
            display_root = "." if str(directory) == "." else str(directory)
            # Ensure tree output starts correctly relative to display_root
            tree_lines = tree_process.stdout.strip().split("\n")
            if tree_lines and tree_lines[0] == ".":
                tree_lines = tree_lines[
                    1:
                ]  # Remove the redundant '.' line from tree itself
            return f"{display_root}\n{os.linesep.join(tree_lines)}"

        else:
            error_msg = f"[Could not generate tree view. 'tree' command failed.]\n[Error: {tree_process.stderr.strip()}]"
            print(
                f"Warning: 'tree' command failed. Ensure it's installed ('brew install tree') and works in '{directory}'.",
                file=sys.stderr,
            )
            print(f"Tree command error output:\n{tree_process.stderr}", file=sys.stderr)
            return error_msg

    except FileNotFoundError:
        error_msg = "[Could not generate tree view. 'tree' command not found. Install with 'brew install tree'.]"
        print(error_msg, file=sys.stderr)
        return error_msg
    except Exception as e:
        error_msg = f"[An unexpected error occurred while running 'tree': {e}]"
        print(f"Warning: {error_msg}", file=sys.stderr)
        return error_msg


def get_digest_info(extensions: List[str], sort_by: str, reverse: bool) -> str:
    """
    Add a line to display infromation on included extensions and sorting.

    Args:
        extensions: A list of lowercase file extensions (e.g., ['.txt', '.md']).
        sort_by: The key to sort by ('name', 'ctime', 'mtime').
        reverse: If True, sort in descending order.

    Returns:
        A sorted list of Path objects for the found files.
    """
    info_text = ""
    info_text += f"Included extensions: {', '.join(extensions)}\n"
    if reverse:
        info_text += f"Output below is sorted in reverse by "
    else:
        info_text += f"Output below is sorted by "

    if sort_by == "name":
        info_text += "filename."
    elif sort_by == "ctime":
        info_text += "creation time."
    elif sort_by == "mtime":
        info_text += "time last modified."

    return info_text


def write_file_contents(outfile: TextIO, files: List[Path], base_dir: Path):
    """
    Writes the content of each file to the output file, preceded by a
    separator and header.

    Args:
        outfile: The open file handle to write to.
        files: A list of Path objects for the files to include.
        base_dir: The root directory Path object, used for relative paths.
    """
    for filepath in files:
        try:
            relative_path = filepath.relative_to(base_dir)
            display_path = f"/{relative_path}"  # Keep consistent prefix

            outfile.write(f"{SEPARATOR}\n")
            outfile.write(f"File: {display_path}\n")
            outfile.write(f"{SEPARATOR}\n")

            try:
                with open(
                    filepath, "r", encoding="utf-8", errors="replace"
                ) as infile:  # Use errors='replace'
                    content = infile.read()
                    outfile.write(content)
                    if content and not content.endswith("\n"):
                        outfile.write("\n")
                    outfile.write("\n")  # Add an extra newline for spacing

            except UnicodeDecodeError:
                # Should be handled by errors='replace' now, but keep as fallback
                outfile.write(
                    f"[Error: Could not decode file {display_path} as UTF-8. Content might be garbled or replaced.]\n\n"
                )
                print(
                    f"Warning: Problem decoding file {filepath} as UTF-8.",
                    file=sys.stderr,
                )
            except IOError as e:
                outfile.write(f"[Error: Could not read file {display_path}: {e}]\n\n")
                print(f"Warning: Could not read file {filepath}: {e}", file=sys.stderr)
            except Exception as e:
                outfile.write(
                    f"[Error: An unexpected error occurred reading file {display_path}: {e}]\n\n"
                )
                print(
                    f"Warning: An unexpected error occurred reading file {filepath}: {e}",
                    file=sys.stderr,
                )

        except Exception as e:
            print(f"Error processing file entry for {filepath}: {e}", file=sys.stderr)


def create_digest(
    directory: str, output_file: str, extensions: List[str], sort_by: str, reverse: bool
):
    """
    Main function to orchestrate the creation of the digest file.
    """
    target_dir = Path(directory).resolve()
    output_path = Path(output_file).resolve()

    if not target_dir.is_dir():
        print(
            f"Error: Input directory not found or is not a directory: {target_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(
            f"Error: Could not create output directory {output_path.parent}: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 1. Find and sort files according to parameters
    found_files = find_text_files(target_dir, extensions, sort_by, reverse)

    print(f"Writing digest to: {output_path}")

    try:
        with open(output_path, "w", encoding="utf-8") as outfile:
            # 2. Generate and write directory structure
            outfile.write("Directory structure:\n")
            tree_structure = get_tree_output(target_dir)
            outfile.write(tree_structure)
            outfile.write("\n")

            # 3. Add digest info
            digest_info = get_digest_info(extensions, sort_by, reverse)
            outfile.write(digest_info)
            outfile.write("\n\n")  # Add space before content

            # 4. Write file contents if any were found
            if found_files:
                write_file_contents(outfile, found_files, target_dir)
            else:
                outfile.write(f"{SEPARATOR}\n")
                outfile.write(
                    "No files matching the specified extensions were found.\n"
                )
                outfile.write(f"{SEPARATOR}\n")

    except IOError as e:
        print(
            f"Error: Could not write to output file {output_path}: {e}", file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        print(
            f"An unexpected error occurred during digest creation: {e}", file=sys.stderr
        )
        sys.exit(1)

    print("Digest file created successfully.")


def main():
    """
    Parses command line arguments and initiates the digest creation process.
    """
    parser = argparse.ArgumentParser(
        description="Concatenate text files from a directory and its subdirectories into a single file, "
        "prefixed with a directory tree.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,  # Shows defaults in help
    )
    parser.add_argument("directory", help="The root directory to scan for text files.")
    parser.add_argument(
        "-o", "--output", default="digest.txt", help="The name of the output file."
    )
    parser.add_argument(
        "-e",
        "--extensions",
        nargs="+",
        default=DEFAULT_EXTENSIONS,
        help="List of file extensions to include (case-insensitive). "
        "Example: --extensions .txt .md .py",
    )
    parser.add_argument(
        "--sort-by",
        choices=["name", "ctime", "mtime"],
        default="name",
        help="Sort files by 'name' (alphanumeric path), 'ctime' (creation/change time), or 'mtime' (modification time)."
        " Note: 'ctime' behavior can vary between OS (creation on Win/Mac, metadata change on Linux).",
    )
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",  # Makes it a flag, stores True if present
        default=False,
        help="Reverse the sort order (e.g., Z-A, newest first).",
    )

    args = parser.parse_args()

    # Ensure extensions start with a dot and are lowercase
    normalized_extensions = [f".{ext.lstrip('.').lower()}" for ext in args.extensions]

    try:
        # Pass the sorting arguments to create_digest
        create_digest(
            args.directory,
            args.output,
            normalized_extensions,
            args.sort_by,
            args.reverse,  # Pass the boolean flag directly
        )
    except SystemExit:
        raise
    except Exception as e:
        print(f"Fatal error: An unexpected issue occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

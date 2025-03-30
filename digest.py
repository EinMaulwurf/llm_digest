#!/usr/bin/env python3
import os
import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, TextIO, Optional # Added for type hints

# Define common text file extensions
DEFAULT_EXTENSIONS = ['.txt', '.md', '.py', '.js', '.html', '.css', '.tex', '.rst', '.json', '.yaml', '.yml', '.xml', '.sh', '.bash']
SEPARATOR = "=" * 80  # Noticeable break line

def find_text_files(directory: Path, extensions: List[str]) -> List[Path]:
    """
    Finds all files within a directory and its subdirectories matching the
    given extensions, sorted alphabetically by full path.

    Args:
        directory: The root directory Path object to search within.
        extensions: A list of lowercase file extensions (e.g., ['.txt', '.md']).

    Returns:
        A sorted list of Path objects for the found files.
    """
    found_files = []
    print(f"Scanning directory: {directory}")
    print(f"Looking for file extensions: {', '.join(extensions)}")
    for root, _, files in os.walk(directory):
        for filename in files:
            # Check against lowercase filename and extension list
            if Path(filename).suffix.lower() in extensions:
                found_files.append(Path(root) / filename)

    found_files.sort() # Sort alphabetically by full path
    print(f"Found {len(found_files)} files to include.")
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
        # Run the tree command relative to the target directory
        # This provides a cleaner output starting from '.'
        tree_process = subprocess.run(
            ['tree', '.'], # Run tree relative to the target dir
            cwd=str(directory), # Set the working directory for the command
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=False # Don't raise exception if tree fails
        )
        if tree_process.returncode == 0:
            # Prepend the root directory marker for clarity as in the example
            return f"└── {directory.name}/\n{tree_process.stdout.strip()}"
        else:
            error_msg = f"[Could not generate tree view. 'tree' command failed.]\n[Error: {tree_process.stderr.strip()}]"
            print(f"Warning: 'tree' command failed. Ensure it's installed ('brew install tree') and works in '{directory}'.", file=sys.stderr)
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
            # Get path relative to the original target directory for display
            relative_path = filepath.relative_to(base_dir)
            # Format path similar to user example (leading slash)
            display_path = f"/{relative_path}"

            outfile.write(f"\n{SEPARATOR}\n")
            outfile.write(f"File: {display_path}\n")
            outfile.write(f"{SEPARATOR}\n\n")

            try:
                with open(filepath, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    # Ensure a newline exists before the next separator
                    if content and not content.endswith('\n'):
                        outfile.write('\n')
                    outfile.write('\n') # Add an extra newline for spacing

            except UnicodeDecodeError:
                outfile.write(f"[Error: Could not decode file {display_path} as UTF-8. Skipping content.]\n\n")
                print(f"Warning: Could not decode file {filepath} as UTF-8.", file=sys.stderr)
            except IOError as e:
                outfile.write(f"[Error: Could not read file {display_path}: {e}]\n\n")
                print(f"Warning: Could not read file {filepath}: {e}", file=sys.stderr)
            except Exception as e:
                 outfile.write(f"[Error: An unexpected error occurred reading file {display_path}: {e}]\n\n")
                 print(f"Warning: An unexpected error occurred reading file {filepath}: {e}", file=sys.stderr)

        except Exception as e:
            # Catch errors related to path manipulation or writing separators
            print(f"Error processing file entry for {filepath}: {e}", file=sys.stderr)
            # Attempt to continue with the next file

def create_digest(directory: str, output_file: str, extensions: List[str]):
    """
    Main function to orchestrate the creation of the digest file.
    """
    target_dir = Path(directory).resolve()
    output_path = Path(output_file).resolve()

    if not target_dir.is_dir():
        print(f"Error: Input directory not found or is not a directory: {target_dir}", file=sys.stderr)
        sys.exit(1)

    # Ensure the output directory exists
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error: Could not create output directory {output_path.parent}: {e}", file=sys.stderr)
        sys.exit(1)

    # 1. Find files
    found_files = find_text_files(target_dir, extensions)

    # Optional: Check if we should proceed if no files are found
    # if not found_files:
    #     print("Warning: No files found matching the specified extensions. Exiting.", file=sys.stderr)
    #     # Create an empty file or just exit? Let's create a file with just the tree.
    #     # sys.exit(0) # Or just return

    print(f"Writing digest to: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            # 2. Generate and write directory structure
            outfile.write("Directory structure:\n")
            tree_structure = get_tree_output(target_dir)
            outfile.write(tree_structure)
            outfile.write("\n\n") # Add space before content

            # 3. Write file contents if any were found
            if found_files:
                write_file_contents(outfile, found_files, target_dir)
            else:
                 outfile.write(f"{SEPARATOR}\n")
                 outfile.write("No files matching the specified extensions were found.\n")
                 outfile.write(f"{SEPARATOR}\n")


    except IOError as e:
        print(f"Error: Could not write to output file {output_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during digest creation: {e}", file=sys.stderr)
        sys.exit(1)

    print("Digest file created successfully.")


def main():
    """
    Parses command line arguments and initiates the digest creation process.
    """
    parser = argparse.ArgumentParser(
        description="Concatenate text files from a directory and its subdirectories into a single file, "
                    "prefixed with a directory tree.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "directory",
        help="The root directory to scan for text files."
    )
    parser.add_argument(
        "-o", "--output",
        default="digest.txt",
        help="The name of the output file."
    )
    parser.add_argument(
        "-e", "--extensions",
        nargs='+',
        default=DEFAULT_EXTENSIONS,
        help="List of file extensions to include (case-insensitive). "
             "Example: --extensions .txt .md .py"
    )

    args = parser.parse_args()

    # Ensure extensions start with a dot and are lowercase
    normalized_extensions = [f".{ext.lstrip('.').lower()}" for ext in args.extensions]

    try:
        create_digest(args.directory, args.output, normalized_extensions)
    except SystemExit:
        # Catch SystemExit raised by argument parsing errors or explicit exits
        # and exit cleanly.
        raise
    except Exception as e:
        # Catch any unexpected errors during the main process
        print(f"Fatal error: An unexpected issue occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import os
import argparse
import subprocess
import sys
from pathlib import Path

# Define common text file extensions
DEFAULT_EXTENSIONS = ['.txt', '.md', '.py', '.js', '.html', '.css', '.tex', '.rst', '.json', '.yaml', '.yml', '.xml', '.sh', '.bash']

def generate_digest(directory, output_file, extensions):
    """
    Generates a digest file containing a directory tree overview and the
    concatenated content of text files found within the directory and its
    subdirectories.
    """
    target_dir = Path(directory).resolve()
    output_path = Path(output_file).resolve()

    if not target_dir.is_dir():
        print(f"Error: Directory not found or is not a directory: {directory}", file=sys.stderr)
        sys.exit(1)

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Scanning directory: {target_dir}")
    print(f"Looking for file extensions: {', '.join(extensions)}")

    # 1. Find all text files and sort them
    found_files = []
    for root, _, files in os.walk(target_dir):
        for filename in files:
            if any(filename.lower().endswith(ext) for ext in extensions):
                found_files.append(Path(root) / filename)

    found_files.sort() # Sort alphabetically by full path

    if not found_files:
        print("Warning: No files found matching the specified extensions.", file=sys.stderr)
        # Still create the output file, but it will be mostly empty
        # return # Or exit if preferred

    print(f"Found {len(found_files)} files to include.")
    print(f"Writing digest to: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            # 2. Generate Directory Structure Overview using 'tree'
            outfile.write("Directory structure:\n")
            try:
                # Run the tree command
                # Note: This tree shows the *entire* structure, not just matched files.
                # Filtering tree output precisely is complex, this gives context.
                tree_process = subprocess.run(
                    ['tree', str(target_dir)],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    check=False # Don't raise exception if tree fails
                )
                if tree_process.returncode == 0:
                    outfile.write(tree_process.stdout)
                else:
                    outfile.write(f"[Could not generate tree view. 'tree' command failed or not found.]\n")
                    outfile.write(f"[Error: {tree_process.stderr}]\n")
                    print("Warning: 'tree' command failed or not found. Install with 'brew install tree'.", file=sys.stderr)

            except FileNotFoundError:
                outfile.write("[Could not generate tree view. 'tree' command not found.]\n")
                print("Warning: 'tree' command not found. Install with 'brew install tree'.", file=sys.stderr)
            except Exception as e:
                outfile.write(f"[An unexpected error occurred while running 'tree': {e}]\n")
                print(f"Warning: An unexpected error occurred while running 'tree': {e}", file=sys.stderr)

            outfile.write("\n\n") # Add space before content

            # 3. Concatenate file contents
            separator = "=" * 80 # Noticeable break line

            for filepath in found_files:
                try:
                    # Get path relative to the original target directory for display
                    relative_path = filepath.relative_to(target_dir)
                    # Format path similar to user example (leading slash)
                    display_path = f"/{relative_path}"

                    outfile.write(f"\n\n{separator}\n")
                    outfile.write(f"File: {display_path}\n")
                    outfile.write(f"{separator}\n\n")

                    try:
                        with open(filepath, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            outfile.write(content)
                            # Ensure a newline exists before the next separator
                            if not content.endswith('\n'):
                                outfile.write('\n')
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
                    print(f"Error processing file {filepath}: {e}", file=sys.stderr)
                    # Attempt to continue with the next file

    except IOError as e:
        print(f"Error: Could not write to output file {output_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    print("Digest file created successfully.")


if __name__ == "__main__":
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

    generate_digest(args.directory, args.output, normalized_extensions)

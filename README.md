
# Directory Digest Creator (`digest.py`)

A Python script that recursively scans a specified directory for text-based files and concatenates their contents into a single output file (a "digest"). It optionally includes a directory tree structure at the beginning for context and allows sorting files by name, creation time, or modification time.

This project is inspired by [Gitingest](https://github.com/cyclotruc/gitingest/). I needed a functionality to sort the output by filename, which Gitingest does not do. Thats how this project was born.

## Features

- Scans directories recursively.
- Includes a directory tree structure at the start of the output (requires the `tree` command).
- Filters files based on a customizable list of extensions (defaults provided for common text files).
- Concatenates the content of found files into a single output file.
- Adds clear separators and file path headers between file contents.
- Allows sorting of included files by:
    - Full path name (`name`, default)
    - Creation time / metadata change time (`ctime`)
    - Last modification time (`mtime`)
- Supports reversing the sort order.
- Customizable output file name.
- Basic error handling for file access and encoding issues.

## Requirements

- Python 3.x
- The `tree` command-line utility.
- On macOS: `brew install tree`
- On Debian/Ubuntu: `sudo apt update && sudo apt install tree`
- On Fedora/CentOS/RHEL: `sudo yum install tree` or `sudo dnf install tree`

## Installation and Setup

1. **Download the script:** Save the script code as `digest.py` (or your preferred name) on your system.
2. **Make it executable:**

```bash
chmod +x digest.py
```

3. **(Optional but Recommended) Add to PATH:** To run the script from any directory without specifying its full path, add it to a directory included in your system's `PATH` environment variable. A common place for user scripts is `~/.local/bin`.

- **Ensure `~/.local/bin` exists and is in your PATH:**
- Create the directory if it doesn't exist: `mkdir -p ~/.local/bin`
- Check if it's in your PATH: `echo $PATH | grep "$HOME/.local/bin"`
- If it's not listed, add the following line to your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`, `~/.profile`, or `~/.bash_profile`) and restart your shell or run `source ~/.your_config_file`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

- **Option A: Copy the script:**

```bash
cp digest.py ~/.local/bin/
```

*(If you update the script later, you'll need to copy the new version again.)*

- **Option B: Create a symbolic link (symlink):** This is often preferred as updates to the original script file are automatically reflected when you run the command. Navigate to your `~/.local/bin` directory and create the link (replace `/path/to/your/script/digest.py` with the actual path):

```bash
cd ~/.local/bin
ln -s /path/to/your/script/digest.py digest_maker

# Now you can run 'digest_maker' instead of 'digest.py' if you prefer
cd - # Go back to previous directory
```

Now you should be able to run `digest.py` (or just `digest_maker` if you symlinked with that name) from anywhere in your terminal.

## Usage

```bash
./digest.py [OPTIONS] <directory>
```

Or if added to PATH:

```bash
digest.py [OPTIONS] <directory>
```

**Arguments:**

- `directory`: The path to the root directory you want to scan.

**Options:**

- `-o OUTPUT`, `--output OUTPUT`: Specify the output file name (default: `digest.txt`).
- `-e EXTENSIONS [EXTENSIONS ...]`, `--extensions EXTENSIONS [EXTENSIONS ...]`: List of file extensions to include (e.g., `.py .js .html`). Defaults to common text file types.
- `--sort-by {name,ctime,mtime}`: Sort files by name (path), creation/change time, or modification time (default: `name`).
- `-r`, `--reverse`: Reverse the sort order (e.g., newest first if sorting by time).
- `-h`, `--help`: Show the help message and exit.

**Examples:**

1. **Basic usage (scan current directory, output to `digest.txt`):**

```bash
digest.py .
```

2. **Scan a specific project directory, output to `project_digest.md`:**

```bash
digest.py /path/to/my/project -o project_digest.md
```

3. **Scan for only Python and Markdown files:**

```bash
digest.py . -e ".py .md"
```

4. **Scan and sort by modification time (newest first), output to `latest_changes.txt`:**

```bash
digest.py /path/to/src --sort-by mtime -r -o latest_changes.txt
```

## License

This project is licensed under the MIT License.

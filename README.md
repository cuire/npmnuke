# npmnuke 💥

> A simple script to remove all node_modules folders in a directory

## Description

My PC had a lot of old web projects that I didn't use anymore, but they were taking up a lot of space. Manually deleting all the node_modules folders was a pain, so I wrote this script to do it for me. 

By defaul script will ignore folders that start with a dot (.git, .vscode, etc.) and folders that contain a .npmnukeignore file. You can also specify your own ignore file with the `--ignore-file` option or modify `.nmpnukeignore` in your home directory.

## Future plans

- [ ] Add new UI using https://github.com/Textualize/textual
- [ ] Somehow make it detect monorepos and combine search results for them
- [ ] Add last modified date to search results
- [ ] Add option to open search results in file manager


## Installation

```bash
pip install npmnuke
```

## Usage

```bash
npmnuke [directory] (options)
```

## Options

- `--dry-run` - Show which folders would be deleted without actually deleting them
- `--ignore-file` - Path to the ignore file, by default .npmnukeignore in home directory is used
- `--disable-ignore` - Do not use the .npmnukeignore file when scanning for node_modules folders.
- `--ignore-dot [true | false]` - Ignore dot folders (.vscode/ .git/ etc.), by default True
- `--verbose` - Show verbose output
- `--help` - Show help


from pathlib import Path
from typing import List, Callable, Optional, Pattern
import asyncio
import collections
import os
import re


async def watch(
    folders: List[str],
    on_change: Callable[[str, float, bool], None],
    sleep_time: float = 0.5,
    pattern: Optional[Pattern] = None,
) -> None:

    pattern = re.compile(pattern) if pattern else None
    watched = collections.defaultdict(lambda: -1)

    async def walk_directory(folder_path: Path) -> List[str]:
        """Walk through directory and return list of files."""
        walked_files = []

        try:
            entries = await asyncio.to_thread(os.scandir, str(folder_path))

            for entry in entries:
                if not entry.is_file():
                    continue

                if pattern and not pattern.search(entry.name):
                    continue

                try:
                    stat = await asyncio.to_thread(os.stat, entry.path)
                    path = str(entry.path)
                    new_time = stat.st_mtime

                    if path in watched and new_time > watched[path] > 0:
                        await on_change(path, new_time, False)

                    watched[path] = new_time
                    walked_files.append(path)

                except FileNotFoundError:
                    continue

        except FileNotFoundError:
            # print(f"Error walking directory {folder_path}: {e}")
            pass

        return walked_files

    async def watch_loop():
        while True:
            walked = []

            # Walk each folder
            for folder in folders:
                folder_path = Path(folder)
                walked.extend(await walk_directory(folder_path))

            # Handle deleted files
            for w in [x for x in watched.keys() if x not in walked]:
                del watched[w]
                await on_change(w, -1, True)

            await asyncio.sleep(sleep_time)

    return await watch_loop()

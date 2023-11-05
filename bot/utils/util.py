import inspect
import os
import json

from pathlib import Path

__all__ = ("fix_doc", "get_absolute_name_from_path")


def fix_doc(*doc: str):
    """
    Clean up indentation from docstrings.
    Any whitespace that can be uniformly removed from the second line
    onwards is removed.

    Parameters:
    -----------
    *doc: list[`str`]
        A doc that needs to be formatted.
    """
    return inspect.cleandoc("\n".join(doc))


def get_absolute_name_from_path(
    path: str | Path,
    base_path: str | Path | None = None,
) -> str:
    """
    Converts absolute paths to relative positions.

    Parameters:
    -----------
    path: `str` | `Path`
        The absolute path that needs to be converted.
    base_path: `str` | `Path` | None
        The primary path of the relative path.
    """
    if not base_path:
        from bot import __config_path__

        base_path = __config_path__

    paths = [(p := Path(path).resolve()).stem]

    while not Path(base_path).samefile(p := p.parent):
        paths.append(p.stem)

    return ".".join(reversed(paths))


def load_guild_params(guild_id, param_id):
    guild_config_path = "./config/guild_config.json"
    default_config_path = "./config/config.json"
    if guild_id == "default_guild" or not os.path.exists(guild_config_path):
        with open(default_config_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data[guild_id][param_id]
    else:
        with open(guild_config_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data[guild_id][param_id]

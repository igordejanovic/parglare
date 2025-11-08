from pathlib import Path
from typing import Union


def output_cmp(file_path: Union[Path, str], file_content: str):
    """
    Compares the given file_content to the content of file_path.

    If file_path doesn't exist it will be created with the content of file_content.
    If the file exists it will be loaded and compared to the content of file_content
    with assert.
    """
    this_dir = str(Path(__file__).parent)
    file_content = str(file_content).replace(str(this_dir), '')

    if not Path(file_path).exists():
        with open(file_path, 'w') as f:
            f.write(file_content)
    else:
        with open(file_path) as f:
            existing_content = f.read()
        assert existing_content == file_content, f"Content mismatch in {file_path}"

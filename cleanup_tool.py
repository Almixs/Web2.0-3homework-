import re
import argparse
from pathlib import Path
import shutil
import concurrent.futures

CYRILLIC_SYMBOLS = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ'
TRANSLATION = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u", "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "u", "ja", "je", "ji", "g")
TRANS = {ord(c): l for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION)}

IMAGE_EXTENSIONS = ['JPEG', 'JPG', 'PNG', 'SVG']
MEDIA_EXTENSIONS = ['MP3', 'AVI', 'MP4', 'MOV', 'MKV']
DOCUMENT_EXTENSIONS = ['DOC', 'DOCX', 'TXT', 'PDF', 'XLSX', 'PPTX']
ARCHIVE_EXTENSIONS = ['ZIP', 'GZ', 'TAR']

JPEG_IMAGES, JPG_IMAGES, PNG_IMAGES, SVG_IMAGES = [], [], [], []
MP3_AUDIO, MY_OTHER, ARCHIVES, FOLDERS = [], [], [], []
EXTENSION, UNKNOWN = set(), set()

REGISTER_EXTENSION = {
    ext: globals().get(f"{ext}_IMAGES", MY_OTHER) for ext in
    set(IMAGE_EXTENSIONS + MEDIA_EXTENSIONS + DOCUMENT_EXTENSIONS + ARCHIVE_EXTENSIONS)
}

def normalize(name: str) -> str:
    t_name = name.translate(TRANS)
    t_name = re.sub(r'\W', '_', t_name)
    return t_name

def handle_media(filename: Path, target_folder: Path) -> None:
    target_folder.mkdir(exist_ok=True, parents=True)
    new_name = normalize(filename.stem) + filename.suffix
    target_file = target_folder / new_name
    shutil.copyfile(str(filename), str(target_file))

def handle_other(filename: Path, target_folder: Path) -> None:
    target_folder.mkdir(exist_ok=True, parents=True)
    new_name = normalize(filename.stem) + filename.suffix
    target_file = target_folder / new_name
    shutil.copyfile(str(filename), str(target_file))

def handle_archive(filename: Path, target_folder: Path) -> None:
    target_folder.mkdir(exist_ok=True, parents=True)
    folder_for_file = target_folder / normalize(filename.stem)
    folder_for_file.mkdir(exist_ok=True)
    try:
        shutil.unpack_archive(str(filename), str(folder_for_file))
    except shutil.ReadError:
        print('It is not an archive')
        folder_for_file.rmdir()

def get_extension(filename: str) -> str:
    return Path(filename).suffix[1:].upper()

def scan(folder: Path) -> None:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for item in folder.iterdir():
            if item.is_dir():
                if item.name not in ('archives', 'video', 'audio', 'documents', 'images', 'MY_OTHER'):
                    futures.append(executor.submit(scan, item))
                continue
            ext = get_extension(item.name)
            fullname = folder / item.name
            if not ext:
                MY_OTHER.append(fullname)
            else:
                try:
                    container = REGISTER_EXTENSION.get(ext, MY_OTHER)
                    EXTENSION.add(ext)
                    container.append(fullname)
                    futures.append(executor.submit(copy_file_async, fullname, folder / 'MY_OTHER'))
                except KeyError:
                    UNKNOWN.add(ext)
                    MY_OTHER.append(fullname)

def read_folder(path: Path, output_folder: Path) -> None:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for el in path.iterdir():
            if el.is_dir():
                futures.append(executor.submit(read_folder, el, output_folder))
            else:
                futures.append(executor.submit(copy_file_async, el, output_folder))

def copy_file_async(file: Path, output_folder: Path) -> None:
    ext = file.suffix
    new_path = output_folder / ext
    new_path.mkdir(exist_ok=True, parents=True)
    shutil.copyfile(str(file), str(new_path / file.name))

def delete_folder(folder: Path, base_folder: Path) -> None:
    try:
        folder.rmdir()
    except OSError:
        print(f"Can't delete folder: {base_folder}")

def main():
    parser = argparse.ArgumentParser(description='Sorting folder')
    parser.add_argument('--source', '-s', required=True, help='Source folder')
    parser.add_argument('--output', '-o', default='dist', help='Output folder')
    args = parser.parse_args()
    source = args.source
    output = args.output

    output_folder = Path(output)
    folder_for_scan = Path(source)
    read_folder(folder_for_scan, output_folder)

    print(f'Start in folder: {folder_for_scan.resolve()}')

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for file in JPEG_IMAGES:
            futures.append(executor.submit(handle_media, file, folder_for_scan / 'images' / 'JPEG'))
        for file in JPG_IMAGES:
            futures.append(executor.submit(handle_media, file, folder_for_scan / 'images' / 'JPG'))
        for file in PNG_IMAGES:
            futures.append(executor.submit(handle_media, file, folder_for_scan / 'images' / 'PNG'))
        for file in SVG_IMAGES:
            futures.append(executor.submit(handle_media, file, folder_for_scan / 'images' / 'SVG'))
        for file in MP3_AUDIO:
            futures.append(executor.submit(handle_media, file, folder_for_scan / 'audio' / 'MP3'))
        for file in MY_OTHER:
            futures.append(executor.submit(handle_other, file, folder_for_scan / 'MY_OTHER'))
        for file in ARCHIVES:
            futures.append(executor.submit(handle_archive, file, folder_for_scan / 'ARCHIVES'))
        for folder in FOLDERS[::-1]:
            futures.append(executor.submit(delete_folder, folder, folder_for_scan))

        concurrent.futures.wait(futures)

if __name__ == "__main__":
    main()

"""Utiliites for fetching and formatting source for the Knowledge Network (KN)
that has been updated.

Classes:

Functions:
    download(version_dict) -> str: takes a dictionary object version_dict and
        determines if the described alias needs to be downloaded. If so,
        downloads the files. In either case, it returns the filename of the
        path to the file.

Variables:
    ARCHIVES: list of supported archive formats.
    CHUNK_SZ: the max size (number of lines) for file chunks
    DIR: the relative path to raw_download/source/alias/ from location of
        script execution
"""

import urllib.request
import json
import shutil
import tarfile
import zipfile
import gzip
import os
import sys
import math
import hashlib

ARCHIVES = ['.zip', '.tar', '.gz']
CHUNK_SZ = float(500000)
DIR = '.'

def download(version_dict):
    """Returns the standardized path to the local file after downloading it
    from the source and unarchiving if needed.

    This returns the standardized path (path/source.alias.txt) for the
    source alias described in version_dict. If a download is needed
    (as determined by the check step), the remote file will be downloaded.

    Args:
        version_dict (dict): A dictionary describing the attributes of the
        alias for a source.

    Returns:
        str: The relative path to the newly downloaded file.
    """
    
    ret_file = version_dict['source'] + '.' + version_dict['alias'] + '.txt'
    ret_file = os.path.join(DIR, ret_file)
    #check if remote file must be downloaded
    if not version_dict['fetch_needed'] and version_dict['local_file_exists']:
        return os.path.relpath(ret_file)

    #download remote file
    url = version_dict['remote_url']
    if url[-1] == '/':
        url = url[:-1]
    filename = os.path.join(DIR, version_dict['local_file_name'])
    with urllib.request.urlopen(url) as response:
        with open(filename, 'wb') as outfile:
            shutil.copyfileobj(response, outfile)
    os.utime(filename, (0,version_dict['remote_date']))

    #unzip remote file
    while os.path.splitext(filename)[1] in ARCHIVES:
        if tarfile.is_tarfile(filename):
            with tarfile.open(filename) as tar:
                tar.extractall(path=DIR)
                file_list = tar.getnames()
        elif zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename) as zfile:
                zfile.extractall(path=DIR)
                file_list = zfile.namelist()
        elif os.path.splitext(filename)[1] == '.gz':
            with gzip.open(filename) as gzfile:
                with open(filename[:-3], 'wb') as outfile:
                    shutil.copyfileobj(gzfile, outfile)
                file_list = [filename[:-3]]
        else:
            print('Error extracting file: ' + filename)
            exit()
        if len(file_list) == 1:
            filename = file_list[0]
        else:
            if('remote_file' in version_dict and
               version_dict['remote_file'] in file_list):
                idx = file_list.index(version_dict['remote_file'])
                filename = file_list[idx]
            else:
                print("Remote file is a directory but version_dict"
                      "['remote_file'] was not found")
                exit()
    #move the downloaded file to source.alias.txt
    shutil.copy2(os.path.join(DIR, filename), ret_file)
    return os.path.relpath(ret_file)

def chunk(filename, total_lines):
    """Splits the provided file into equal chunks with
    ceiling(num_lines/CHUNK_SZ) lines each.

    This takes the path to a file and reads through the file, splitting it
    into equal chunks with each of size ceiling(num_lines/CHUNK_SZ). It
    then returns the number of chunks and sets up the raw_lines table in the
    format: (file, line num, line_chksum, rawline)


    Args:
        filename: the file to split into chunks
        total_lines: the number of lines in the file at filename

    Returns:
        int: the number of chunks filename was split into
    """
    #determine number of chunks
    num_chunks = math.ceil(total_lines/CHUNK_SZ)
    num_lines = int(total_lines/num_chunks)

    #determine file output information
    path, file = os.path.split(filename)
    chunk_dir = os.path.join(path, 'chunks')
    os.makedirs(chunk_dir, exist_ok=True)
    source_alias, ext = os.path.splitext(file)
    chunk_file = os.path.join(chunk_dir, source_alias + '.rawline.')

    #divide file into chunks
    line_count = 0
    with open(filename, 'rb') as infile:
        for i in range(1, num_chunks + 1):
            with open(chunk_file + str(i) + ext, 'wb') as out:
                for j in range(0, num_lines):
                    line = infile.readline()
                    hasher = hashlib.md5()
                    hasher.update(line)
                    md5 = hasher.hexdigest()
                    line_count += 1
                    src = os.path.splitext(filename)[0]
                    outline = '\t'.join((src, str(line_count), md5, ''))
                    out.write(outline.encode())
                    out.write(line)
                if i == num_chunks:
                    for line in infile:
                        out.write(line)
    return num_chunks

def raw_line(filename):
    """Creates the raw_line table from the provided file and returns the
       path to the output file.

    This takes the path to a file and reads through the file, adding three tab
    separated columns to the beginning, saving to disk, and then returning the
    output file path. Output looks like:
    raw_lines table (file, line num, line_chksum, rawline)

    Args:
        filename: the file to convert to raw_line table format

    Returns:
        str: the path to the output file
    """
    #determine file output information
    path, file = os.path.split(filename)
    source_alias, ext = os.path.splitext(file)
    rawline = os.path.join(path, source_alias + '.raw_line' + ext)

    #convert the file to raw_line format
    line_count = 0
    with open(filename, 'rb') as infile:
        with open(rawline, 'wb') as outfile:
            for line in infile:
                hasher = hashlib.md5()
                hasher.update(line)
                md5 = hasher.hexdigest()
                line_count += 1
                outline = '\t'.join([source_alias, str(line_count), md5, ''])
                outfile.write(outline.encode())
                outfile.write(line)
    return rawline

def get_md5_hash(filename):
    """Returns the md5 hash of the file at filename.

    This takes the path to a file and reads through the file line by line,
    producing both the md5 hash and a count of the number of lines.

    Args:
        filename: the file to split into chunks

    Returns:
        str: the md5 hash of the file at filename
        int: the number of lines in the file at int
    """
    with open(filename, 'rb') as file:
        line_count = 0
        md5 = hashlib.md5()
        for line in file:
            md5.update(line)
            line_count += 1
    return md5.hexdigest(), line_count

def get_line_count(filename):
    """Returns the number of lines in the file at filename.

    This takes the path to a file and reads through the file line by line,
    producing a count of the number of lines.

    Args:
        filename: the file to split into chunks

    Returns:
        int: the number of lines in the file at int
    """
    with open(filename, 'rb') as infile:
        line_count = 0
        for _ in infile:
            line_count += 1
    return line_count

def main(version_json):
    """Fetches and chunks the source:alias described by version_json.

    This takes the path to a version_json (source.alias.json) and runs fetch
    (see fetch). If the alias is a data file, it then runs raw_line (see
    raw_line) and then runs chunk (see chunk) on the output. If the alias is a
    mapping file, it runs create_mapping_dict (see create_mapping_dict in
    SRC.py). It also updates version_json to include the total lines in and
    md5 checksum of the fetched file. It then saves the updated version_json to
    file.

    Args:
        version_json (str): path to a json file describing the source:alias

    Returns:
    """
    with open(version_json, 'r') as infile:
        version_dict = json.load(infile)
    newfile = download(version_dict)
    md5hash, line_count = get_md5_hash(newfile)
    src_module = __import__(version_dict['source'])
    SrcClass = src_module.get_SrcClass()
    if version_dict['is_map']:
        num_chunks = 0
        map_dict = SrcClass.create_mapping_dict(newfile)
        map_file = os.path.splitext(newfile)[0] + '.json'
        with open(map_file, 'w') as outfile:
            json.dump(map_dict, outfile, indent=4, sort_keys=True)
    else:
        #rawline = raw_line(newfile)
        num_chunks = chunk(newfile, line_count)
    #update version_dict
    version_dict['checksum'] = md5hash
    version_dict['line_count'] = line_count
    version_dict['num_chunks'] = num_chunks
    with open(version_json, 'w') as outfile:
        json.dump(version_dict, outfile, indent=4, sort_keys=True)

if __name__ == "__main__":
    main(sys.argv[1])

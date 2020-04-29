"""
stuff
TODO settings class, maybe utilise fbx IO settings?

"""
import os
from maya import mel

def split_file_path(file_path):

    head, tail = os.path.split(file_path)

    file_path_toks = [head, tail]

    while True:
        head, tail = os.path.split(file_path)

        if head == file_path:
            return file_path_toks
        else:
            file_path_toks.insert(0, tail)

def convert_file_path_to_maya(file_path):

    file_path_toks = file_path.split(r"\\\\")
    print file_path_toks
    file_path = r"//".join(file_path_toks)
    return file_path

def import_fbx_file(file_path):
    """stuff
    """

    # file_path = convert_file_path_to_maya(file_path)
    file_path = file_path.replace("\\", "/")
    print "Importing fbx file: {}".format(file_path)


    mel_cmd = """
    FBXImportMode -v add;
    FBXImportShapes -v true;
    FBXImport -f "{file_path}";
    """.format(
        file_path=file_path
    )

    mel.eval(mel_cmd)

    return True

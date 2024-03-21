# References
# https://docs.microsoft.com/en-us/windows/win32/direct3ddds/dds-header
# https://docs.microsoft.com/en-us/windows/win32/direct3ddds/dds-header-dxt10
# https://docs.microsoft.com/en-us/windows/win32/direct3ddds/dds-pixelformat
# https://docs.microsoft.com/en-us/windows/win32/api/dxgiformat/ne-dxgiformat-dxgi_format

# System Imports
import os, re
from pathlib import Path
from struct import pack, unpack

# PIP Imports
import click

# Global variables
FORMATS = { # FourCC, RGBBitCount, PixelFormat
    "DXT1": (827611204, 0), # BC1_UNORM
    "DXT5": (894720068, 8) # BC3_UNORM
}

# Struct Functions
def unpackChar(fh):
    return unpack("<B", fh.read(1))[0]

def unpackShort(fh):
    return unpack("<H", fh.read(2))[0]

def unpackLong(fh):
    return unpack("<L", fh.read(4))[0]

def unpackString(fh, length):
    string = ""
    for _ in range(length):
        for char in unpack("<c", fh.read(1)):
            if ord(char) == 0: break
            string += char.decode("utf-8")
    return string

def packChar(i):
    return pack("<B", i)

def packShort(i):
    return pack("<H", i)

def packLong(i):
    return pack("<L", i)

class PCD9:
    format = None
    size = None
    width = None
    height = None
    flags = None
    mipCount = None
    type = None
    data = None
    
    def __init__(self):
        pass
    
    def readPCD9(self, path):
        with open(path, "rb") as fh:
            fh.seek(24)
            magic = unpackString(fh, 4)
            if magic != "PCD9": # Return if input is not of expected type
                return print(f"Input does not contain expected magic!")
            self.format = unpackString(fh, 4)
            if self.format not in FORMATS: # Return if input is not of expected type
                return print(f"Input encoding not supported!")
            self.size = unpackLong(fh)
            fh.seek(4, 1)
            self.width = unpackShort(fh)
            self.height = unpackShort(fh)
            self.flags = unpackChar(fh)
            self.mipCount = unpackChar(fh)
            self.type = unpackShort(fh)
            self.data = fh.read(size)
    
    def readDDS(self, path):
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell() - 128
            fh.seek(84)
            self.format = unpackString(fh, 4)
            fh.seek(12)
            self.height = unpackLong(fh)
            self.width = unpackLong(fh)
            fh.seek(8, 1)
            self.mipCount = unpackLong(fh)
            fh.seek(128)
            self.data = fh.read(size)
        self.flags = 3
    
    def writePCD9(self, path):
        id = int(re.findall("[0-9]+_([0-9a-f]+)", str(path))[-1], 16)
        print(id)
        with open(path, "wb") as fh:
            fh.write(b"SECT")
            fh.seek(4, 1)
            fh.write(packChar(5))
            fh.seek(3, 1)
            fh.write(packLong(10))
            fh.write(packLong(id))
            fh.write(b"\xFF\xFF\xFF\xFF")
            fh.write(b"PCD9")
            fh.write(self.format.encode("utf-8"))
            fh.seek(8, 1)
            fh.write(packShort(self.width))
            fh.write(packShort(self.height))
            fh.seek(1, 1)
            fh.write(packChar(self.mipCount))
            fh.write(packShort(3))
            fh.write(self.data)
            size = fh.tell()
            fh.seek(4)
            fh.write(packLong(size - 24))
            fh.seek(32)
            fh.write(packLong(size - 48))

class DDS:
    size = None
    format = None
    height = None
    width = None
    length = None
    mipCount = None
    data = None
    
    def __init__(self):
        pass
    
    def readDDS(self, path):
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell() - 128
            fh.seek(84)
            self.format = unpackString(fh, 4)
            fh.seek(12)
            self.height = unpackLong(fh)
            self.width = unpackLong(fh)
            self.length = self.width * self.height * FORMATS[self.format][1] // 8
            fh.seek(8, 1)
            self.mipCount = unpackLong(fh)
            fh.seek(96, 1)
            self.data = fh.read(size)
    
    def readPCD9(self, path):
        with open(path, "rb") as fh:
            fh.seek(24)
            magic = unpackString(fh, 4)
            if magic != "PCD9": # Return if input is not of expected type
                return print(f"Input does not contain expected magic!")
            self.format = unpackString(fh, 4)
            if self.format not in FORMATS: # Return if input is not of expected type
                return print(f"Input encoding not supported!")
            self.size = unpackLong(fh)
            fh.seek(4, 1)
            self.width = unpackShort(fh)
            self.height = unpackShort(fh)
            self.length = self.width * self.height * FORMATS[self.format][1] // 8
            fh.seek(1, 1)
            self.mipCount = unpackChar(fh)
            fh.seek(2, 1)
            self.data = fh.read(self.size)
    
    def writeDDS(self, path):
        with open(path, "wb") as fh:
            fh.write(packLong(542327876)) # Magic
            fh.write(packLong(124)) # Structure size
            fh.write(packLong(659463)) # Flags
            fh.write(packLong(self.height)) # Height
            fh.write(packLong(self.width)) # Width
            fh.write(packLong(self.length)) # First mip length
            fh.write(packLong(0)) # Depth
            fh.write(packLong(self.mipCount)) # Mips
            fh.seek(44, 1) # Skip to DDS_PIXELFORMAT
            fh.write(packLong(32)) # Structure size
            fh.write(packLong(4)) # Flags
            fh.write(packLong(FORMATS[self.format][0])) # FourCC
            fh.seek(20, 1)
            fh.write(packLong(4198408))
            fh.seek(16, 1)
            fh.write(self.data)

@click.group()
def cli():
    pass

@cli.command()
@click.argument("path")
def convert(path):
    """ Convert PCD9 to DDS, or DDS to PCD9."""
    print(f"Processing {path}")
    
    inpath = Path(path)
    extension = inpath.suffix
    
    match extension:
        case ".tr8pcd9":
            outpath = Path(f"{inpath.stem}.dds")
            
            out = DDS()
            out.readPCD9(inpath)
            out.writeDDS(outpath)
        
        case ".dds":
            outpath = Path(f"{inpath.stem}.tr8pcd9")
            
            if outpath.exists():
                outpath = Path(f"{inpath.stem}_new.tr8pcd9")
            
            out = PCD9()
            out.readDDS(inpath)
            out.writePCD9(outpath)
        
        case default:
            print("Input does not have a known extension!")

if __name__ == "__main__":
    cli()

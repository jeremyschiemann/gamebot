import zlib
import base64

def calc_crc32_checksum(data_bytes: bytes) -> str:
    crc32_val = zlib.crc32(data_bytes) & 0xFFFFFFFF
    crc32_bytes = crc32_val.to_bytes(4, byteorder='big')
    return base64.b64encode(crc32_bytes).decode('utf-8')

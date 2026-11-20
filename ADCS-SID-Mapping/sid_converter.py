import base64
import struct
import sys

def decode_sid(encoded_sid):
    sid = base64.b64decode(encoded_sid)
    revision = sid[0]
    subauth_count = sid[1]
    identifier_authority = int.from_bytes(sid[2:8], byteorder="big")
    subauthorities = struct.unpack(
        "<" + "I" * subauth_count,
        sid[8:8 + 4 * subauth_count]
    )
    components = [revision, identifier_authority, *subauthorities]
    return "S-" + "-".join(map(str, components))

print(decode_sid(sys.argv[1]))


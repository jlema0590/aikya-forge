"""Build terminal presentation data from the unchanged first-party RGB PNG."""
import base64
import hashlib
import json
from pathlib import Path
import struct
import zlib

ROOT=Path(__file__).resolve().parents[2]


def rgb_png(raw):
    if len(raw)>2000000 or raw[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Invalid bounded logo PNG')
    offset=8;compressed=bytearray();width=height=None
    while offset<len(raw):
        size=struct.unpack('>I',raw[offset:offset+4])[0];kind=raw[offset+4:offset+8];value=raw[offset+8:offset+8+size]
        if len(value)!=size or offset+12+size>len(raw):raise ValueError('Truncated PNG')
        if zlib.crc32(kind+value)&0xffffffff!=struct.unpack('>I',raw[offset+8+size:offset+12+size])[0]:raise ValueError('Logo CRC differs')
        if kind==b'IHDR':
            width,height,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',value)
            if not 1<=width<=2048 or not 1<=height<=2048 or (depth,color,compression,filtering,interlace)!=(8,2,0,0,0):raise ValueError('Expected bounded RGB8 PNG')
        if kind==b'IDAT':compressed.extend(value)
        offset+=12+size
        if kind==b'IEND':break
    if width is None:raise ValueError('Missing logo dimensions')
    expected=(width*3+1)*height;decoder=zlib.decompressobj();scan=decoder.decompress(compressed,expected+1)
    if len(scan)!=expected or not decoder.eof or decoder.unused_data:raise ValueError('Invalid logo pixel data')
    rows=[];previous=bytearray(width*3)
    for y in range(height):
        mode=scan[y*(width*3+1)];row=bytearray(scan[y*(width*3+1)+1:(y+1)*(width*3+1)])
        if mode not in range(5):raise ValueError('Invalid PNG filter')
        for i in range(len(row)):
            a=row[i-3] if i>=3 else 0;b=previous[i];c=previous[i-3] if i>=3 else 0
            p=a+b-c;distances=(abs(p-a),abs(p-b),abs(p-c));paeth=(a,b,c)[distances.index(min(distances))]
            row[i]=(row[i]+(0,a,b,(a+b)//2,paeth)[mode])&255
        rows.append(row);previous=row
    return width,height,rows


def main():
    source=ROOT/'docs/images/aikya-harness.png';raw=source.read_bytes();width,height,rows=rgb_png(raw)
    left=width;right=0;top=height;bottom=0
    for y,row in enumerate(rows):
        for x in range(width):
            color=row[x*3:x*3+3]
            if max(color)-min(color)>30 or max(color)<200:
                left=min(left,x);right=max(right,x+1);top=min(top,y);bottom=max(bottom,y+1)
    if left>=right or top>=bottom:raise ValueError('No logo content')
    content_bounds=[left,top,right,bottom]
    # The original connected mark occupies this source viewport. The complete
    # original wordmark PNG is retained byte-for-byte; terminal type stays legible.
    right=509;columns=22;pixel_rows=20;pixels=bytearray()
    for y in range(pixel_rows):
        sy=min(bottom-1,top+int((y+.5)*(bottom-top)/pixel_rows))
        for x in range(columns):
            sx=min(right-1,left+int((x+.5)*(right-left)/columns));pixels.extend(rows[sy][sx*3:sx*3+3])
    swatches={name:'#'+bytes(rows[y][x*3:x*3+3]).hex() for name,x,y in [('cyan',160,650),('turquoise',408,583),('navy',646,506)]}
    record=dict(schema=1,source='docs/images/aikya-harness.png',source_sha256=hashlib.sha256(raw).hexdigest(),
                source_dimensions=[width,height],source_content_bounds=content_bounds,view_bounds=[left,top,right,bottom],columns=columns,pixel_rows=pixel_rows,
                swatches=swatches,rgb_base64=base64.b64encode(pixels).decode())
    target=ROOT/'packages/aikya-pi/src/branding';target.mkdir(parents=True,exist_ok=True)
    for name,data in [('aikya-harness.png',raw),('logo.json',(json.dumps(record,indent=2)+'\n').encode())]:
        path=target/name
        if path.exists() and path.read_bytes()!=data:raise ValueError('Existing differing logo data is preserved')
        if not path.exists():path.write_bytes(data)
    print(json.dumps({key:value for key,value in record.items() if key!='rgb_base64'}))


if __name__=='__main__':main()

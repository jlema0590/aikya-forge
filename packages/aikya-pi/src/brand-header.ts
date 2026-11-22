import {readFileSync,lstatSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {truncateToWidth,replaceControlCharacters} from '@earendil-works/pi-tui';
import {BRAND_LOGO_SHA256,AIKYA_COLORS} from './brand.ts';

let raster:{columns:number;rows:number;pixels:Buffer}|undefined;
function logo() {
  if(raster)return raster;
  const read=(name:string,limit:number)=>{
    const path=new URL('./branding/'+name,import.meta.url),stat=lstatSync(path);
    if(stat.isSymbolicLink()||!stat.isFile()||stat.size>limit)throw new Error('Invalid bundled brand resource');
    return readFileSync(path);
  };
  const png=read('aikya-harness.png',1200000),data=JSON.parse(read('logo.json',12000).toString('utf8'));
  if(createHash('sha256').update(png).digest('hex')!==BRAND_LOGO_SHA256||data.source_sha256!==BRAND_LOGO_SHA256
    ||data.schema!==1||data.columns!==22||data.pixel_rows!==20||typeof data.rgb_base64!=='string')throw new Error('Bundled logo provenance differs');
  const pixels=Buffer.from(data.rgb_base64,'base64');if(pixels.length!==22*20*3)throw new Error('Invalid logo presentation data');
  return raster={columns:22,rows:20,pixels};
}

/** Terminal-cell rendition of the original artwork, not a new logo or PNG edit.
 * No image protocol, external executable, decoder or network is needed at startup. */
export function renderBrandHeader(width:number,version:string,status:string) {
  width=Math.max(1,Math.floor(width));const lines:string[]=[];
  if(width>=60) {
    try {
      const image=logo();
      for(let y=0;y<image.rows;y+=2) {
        let line='';
        for(let x=0;x<image.columns;x++) {
          const top=(y*image.columns+x)*3,bottom=((y+1)*image.columns+x)*3;
          line+='\x1b[38;2;'+[...image.pixels.subarray(top,top+3)].join(';')+'m\x1b[48;2;'
            +[...image.pixels.subarray(bottom,bottom+3)].join(';')+'m▀';
        }
        const label=y===6?'Aikya Harness':y===10?'Aikya Forge':'';
        const fg=AIKYA_COLORS.accent;
        lines.push(line+'\x1b[0m  '+(label?'\x1b[38;2;'+[1,3,5].map(i=>parseInt(fg.slice(i,i+2),16)).join(';')+'m'+label+'\x1b[0m':''));
      }
    }catch { /* A display resource never disables the operator's terminal. */ }
  }
  if(!lines.length)lines.push('Aikya Harness · Aikya Forge');
  lines.push('AIKYA v'+replaceControlCharacters(version),replaceControlCharacters(status)+' · /aikya-settings');
  return lines.map(line=>truncateToWidth(line,width,'…'));
}

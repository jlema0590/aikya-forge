import {execFile} from 'node:child_process';
export type FigletBanner={generator:'plain'|'pyfiglet';variants:{font:string;lines:string[]}[]};
const plain=():FigletBanner=>({generator:'plain',variants:[]});
const cached=new Map<string,Promise<FigletBanner>>();

function decode(raw:string):FigletBanner {
  const value=JSON.parse(raw);
  if(value?.schema!==1||value.text!=='Aikya'||!['plain','pyfiglet'].includes(value.generator)||!Array.isArray(value.variants))throw new Error('Invalid banner');
  if(value.generator==='plain') {if(value.variants.length)throw new Error('Invalid fallback');return plain();}
  if(value.version!=='1.0.4'||value.variants.length!==2)throw new Error('Invalid FIGlet version');
  const variants=value.variants.map((item:{font:unknown;lines:unknown},index:number)=>{
    if(!item||item.font!==['slant','small'][index]||!Array.isArray(item.lines)||!item.lines.length||item.lines.length>8
      ||item.lines.some(row=>typeof row!=='string'||row.length>80||/[^\x20-\x7e]/.test(row)))throw new Error('Invalid FIGlet lines');
    return {font:String(item.font),lines:[...item.lines] as string[]};
  });
  return {generator:'pyfiglet',variants};
}

/** Pure presentation, cached per interpreter: no project access, shell or provider. */
export function loadFigletBanner(python='python3'):Promise<FigletBanner> {
  if(!cached.has(python))cached.set(python,new Promise(resolve=>{
    const env=Object.fromEntries(Object.entries(process.env).filter(([key])=>
      ['PATH','SYSTEMROOT','WINDIR','LANG','LC_ALL','TMPDIR','TEMP','TMP'].includes(key.toUpperCase())));
    execFile(python,['-I','-B','-m','aikya.presentation.banner'],{timeout:3000,maxBuffer:8192,windowsHide:true,env},(error,stdout)=>{
      if(error){resolve(plain());return;}
      try {resolve(decode(stdout));}catch {resolve(plain());}
    });
  }));
  return cached.get(python)!.then(value=>structuredClone(value));
}

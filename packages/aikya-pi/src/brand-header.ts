import {truncateToWidth,replaceControlCharacters} from '@earendil-works/pi-tui';
import {AIKYA_COLORS} from './brand.ts';
import type {FigletBanner} from './figlet.ts';

/** Choose a complete FIGlet word, never wrapped/truncated ASCII artwork. */
export function renderBrandHeader(width:number,version:string,status:string,banner?:FigletBanner) {
  width=Math.max(1,Math.floor(width));const lines:string[]=[];
  const variant=banner?.variants.find(v=>v.lines.every(row=>row.length<=width));
  if(variant) {
    const color='\x1b[38;2;'+[1,3,5].map(i=>parseInt(AIKYA_COLORS.accent.slice(i,i+2),16)).join(';')+'m';
    lines.push(...variant.lines.map(row=>color+row+'\x1b[0m'));
  }
  lines.push('Aikya Forge v'+replaceControlCharacters(version));
  lines.push(replaceControlCharacters(status)+' · /aikya-settings');
  return lines.map(line=>truncateToWidth(line,width,'…'));
}

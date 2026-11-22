/** Logo swatches sampled from the unchanged first-party PNG; supporting UI tokens
 * follow aikya/docs/design/design-system.md and memory-viewer/viewer.css. */
export const AIKYA_COLORS={background:'#0b1f44',panel:'#112139',text:'#edf4ff',muted:'#acbed6',border:'#29405e',
  accent:'#0fb3f1',success:'#1fccba',blue:'#94baff',warning:'#e5cb85',error:'#f3b293'} as const;
export const BRAND_LOGO_SHA256='40a17b102c9aa7cb0fa89840b0efb91ae6a3dc27cf339b01b8042f8e77897432';
export type ConsoleTheme='inherit'|'aikya'|'dark'|'light';
export function appearanceColors(theme:ConsoleTheme) {
  return theme==='aikya'?{background:AIKYA_COLORS.background,text:AIKYA_COLORS.text}
    :theme==='light'?{background:'#ffffff',text:'#111827'}:{background:'#101010',text:'#e5ebf4'};
}

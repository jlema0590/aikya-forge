import {Input,matchesKey,Key,truncateToWidth} from '@earendil-works/pi-tui';

/** Input never renders entered bytes or sends them to the transcript. */
export class SecretInput extends Input {
  #title:string;
  constructor(title:string,done:(value:string|undefined)=>void) {
    super();this.#title=title;
    this.onSubmit=value=>{this.setValue('');done(value.length<=8192&&!/[\x00-\x1f\x7f]/.test(value)?value:undefined);};
    this.onEscape=()=>{this.setValue('');done(undefined);};
  }
  override handleInput(data:string) {
    if(matchesKey(data,Key.ctrl('c'))){this.onEscape?.();return;}
    super.handleInput(data);
    if(this.getValue().length>8192)this.setValue('');
  }
  override render(width:number) {
    return [truncateToWidth(this.#title,width,'…'),truncateToWidth('> '+'•'.repeat(Math.min(60,this.getValue().length)),width,'…'),
      truncateToWidth('Enter: save credential · Esc: cancel',width,'…')];
  }
}

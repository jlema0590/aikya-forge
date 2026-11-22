import type {ConsoleSettings} from './console-preferences.ts';
import type {BudgetStatus} from './usage.ts';

/** Saved selection never resets accounting or replaces explicit command-line policy. */
export function resolveConsoleLaunch(settings:ConsoleSettings,budget:BudgetStatus,provider?:string,model?:string):
  {provider?:string;model?:string;diagnostic?:string} {
  if(Boolean(provider)!==Boolean(model))throw new Error('Select provider and model together');
  if(provider&&model)return {provider,model};
  if(!settings.provider)return {};
  if(budget.status!=='available')return {diagnostic:'Saved provider is inactive: configure an available budget with /aikya-tokens'};
  return {provider:settings.provider.id,model:settings.provider.model};
}

import {createDecisionAdapterRegistry} from '../decision-adapter-sdk.mjs';
import {twilightForestDecisionAdapter} from './twilightforest-decision-adapter.mjs';
import {twilightForestTransitionAdapter} from './twilightforest-transition-adapter.mjs';

// Trusted explicit list; raw records cannot register executable adapters or grant owner authority.
export const registeredModDecisionAdapters=createDecisionAdapterRegistry([twilightForestDecisionAdapter,twilightForestTransitionAdapter]);

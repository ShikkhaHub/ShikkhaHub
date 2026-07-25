import { fn } from 'storybook/test';
import * as actual from '@shikkhahub/shared/src/components/GrowthBookProvider';

export const useFeature = fn(actual.useFeature)
  .mockName('useFeature')
  .mockReturnValue('control');

export * from '@shikkhahub/shared/src/components/GrowthBookProvider';

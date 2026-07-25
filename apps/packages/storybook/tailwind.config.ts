import type { Config } from 'tailwindcss'
import config from '@shikkhahub/shared/tailwind.config';

export default {
  ...config,
  content: [
    './src/**/*.{ts,tsx}',
    './node_modules/@shikkhahub/shared/src/**/*.{ts,tsx}',
  ],
  safelist: [
    {
      pattern: /^(.*?)/,
    },
  ]
} satisfies Config;

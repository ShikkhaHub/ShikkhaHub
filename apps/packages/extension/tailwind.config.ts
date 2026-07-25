// eslint-disable-next-line import/no-extraneous-dependencies
import { type Config } from 'tailwindcss';
import config from '@shikkhahub/shared/tailwind.config';

module.exports = {
  ...config,
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
    './node_modules/@shikkhahub/shared/src/**/*.{js,ts,jsx,tsx}',
  ],
  // eslint-disable-next-line
} satisfies Config;

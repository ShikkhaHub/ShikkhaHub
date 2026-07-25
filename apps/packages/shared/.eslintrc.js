module.exports = {
  extends: ['@shikkhahub'],
  plugins: ['sort-exports'],
  rules: {
    'sort-exports/sort-exports': [
      'error',
      { sortDir: 'asc', ignoreCase: true, pattern: '**/icons/index.ts' },
    ],
  },
};

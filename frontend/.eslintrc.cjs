module.exports = {
  root: true,
  env: { browser: true, es2022: true, node: true },
  extends: [
    'plugin:vue/vue3-recommended',
    'plugin:@typescript-eslint/recommended',
    '@vue/eslint-config-prettier'
  ],
  parser: 'vue-eslint-parser',
  parserOptions: { parser: '@typescript-eslint/parser', ecmaVersion: 'latest', sourceType: 'module' },
  rules: { 'vue/multi-word-component-names': 'off' }
}

import withNuxt from '@nuxt/eslint'

export default withNuxt({
    files: ['**/*.vue', '**/*.ts', '**/*.tsx'],
    rules: {
        'no-undef': 'error',
        'no-unused-vars': 'error',
        'no-unused-expressions': 'error',
        'no-unused-labels': 'error',
        'no-unused-imports': 'error',
        'no-unused-functions': 'error',
        'no-unused-classes': 'error',
        'no-console': 'error',
    }
})
module.exports = {
  content: [
    './templates/**/*.html',
    './theme/static/**/*.js',
    './node_modules/flowbite/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        // These will be overridden by CSS variables from our Theme model
        primary: 'var(--primary)',
        'primary-dark': 'var(--primary-dark)',
        'primary-light': 'var(--primary-light)',
        secondary: 'var(--secondary)',
        'secondary-dark': 'var(--secondary-dark)',
        'secondary-light': 'var(--secondary-light)',
        accent: 'var(--accent)',
        success: 'var(--success)',
        info: 'var(--info)',
        warning: 'var(--warning)',
        danger: 'var(--danger)',
      },
      fontFamily: {
        primary: 'var(--font-primary)',
        headings: 'var(--font-headings)',
      },
      borderRadius: {
        DEFAULT: 'var(--border-radius)',
        button: 'var(--button-border-radius)',
      },
    },
  },
  plugins: [
    require('flowbite/plugin')
  ],
}
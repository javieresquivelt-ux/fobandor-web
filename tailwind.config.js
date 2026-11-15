module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './fobandor/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        'fobandor-orange': '#FF6A00',
        'fobandor-blue': '#2563EB',
        'fobandor-cyan': '#06B6D4',
        'fobandor-dark': '#0D1117',
        'fobandor-light': '#F3F4F6',
      },
      fontFamily: {
        montserrat: ['Montserrat', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

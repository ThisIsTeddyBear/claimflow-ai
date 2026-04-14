/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './hooks/**/*.{js,ts,jsx,tsx}',
    './lib/**/*.{js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#f6f7fb',
        ink: '#122239',
        accent: '#006d77',
        alert: '#c2410c',
        okay: '#1f7a52',
        muted: '#587185'
      },
      boxShadow: {
        panel: '0 10px 30px rgba(18, 34, 57, 0.08)'
      },
      backgroundImage: {
        halo: 'radial-gradient(circle at 20% 20%, rgba(0,109,119,0.16), transparent 42%), radial-gradient(circle at 80% 0%, rgba(194,65,12,0.12), transparent 48%)'
      }
    }
  },
  plugins: []
};
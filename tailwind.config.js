/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue", 
    "./plugins/**/*.{js,ts}",
    "./app.vue",
    "./error.vue"
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Newsreader', 'serif'], // Body text
        heading: ['Inter Flex', 'ui-sans-serif', 'system-ui', 'sans-serif'], // Headings
        mono: ['Source Code Pro', 'ui-monospace', 'SFMono-Regular', 'monospace'], // Code
      }
    },
  },
  plugins: [],
}
export default defineNuxtConfig({
  devtools: { enabled: true },
  
  modules: [
    '@nuxtjs/tailwindcss',
    '@nuxt/content',
    '@nuxtjs/google-fonts'
  ],

  googleFonts: {
    families: {
      'Inter+Flex': {
        wght: [400, 500, 600, 700, 800, 900],
        ital: [400, 700]
      },
      'Newsreader': {
        wght: [200, 300, 400, 500, 600, 700, 800],
        ital: [200, 300, 400, 500, 600, 700, 800]
      },
      'Source+Code+Pro': {
        wght: [200, 300, 400, 500, 600, 700, 800, 900]
      }
    },
    display: 'swap',
    preload: true
  },

  content: {
    // Content module configuration
    markdown: {
      // Allow HTML in markdown
      anchorLinks: false
    }
  },

  css: [
    '~/assets/css/main.css'
  ],

  app: {
    head: {
      title: 'Telephony Mastery Course',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Master telephony concepts and build real-world communication solutions' }
      ]
    }
  }
})
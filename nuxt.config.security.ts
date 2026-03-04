/**
 * SECURE NUXT CONFIGURATION
 * 
 * This configuration ensures secure deployment with content protection
 */

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
    // SECURITY: Only use content/ directory (public previews)
    sources: {
      content: {
        driver: 'fs',
        base: './content'
      }
    },
    
    // Content protection settings
    markdown: {
      anchorLinks: false,
    },
    
    // Exclude any full content patterns
    ignores: [
      '**/*.full.md',
      '**/*-full.md', 
      '**/*-private.md',
      '**/content-full/**',
      '**/content-private/**'
    ]
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
  },

  // SECURITY: Build configuration
  nitro: {
    // Only include safe files in deployment
    ignore: [
      'content-full/**',
      'content-private/**', 
      'content-backup/**',
      '**/*.full.md',
      '**/*-full.md',
      '**/*-private.md',
      'scripts/migrate-content.js'
    ]
  }
})
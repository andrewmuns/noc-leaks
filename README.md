# Telephony Mastery - Course Website

A modern, responsive Nuxt.js website for the Telephony Mastery course platform.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Generate static site
npm run generate

# Preview production build
npm run preview
```

## 📁 Project Structure

```
telephony-mastery-site/
├── assets/css/          # Global CSS with Tailwind
├── components/          # Reusable Vue components
├── content/            # Content management (ready for future content)
├── layouts/            # Page layouts (default.vue included)
├── pages/              # File-based routing
│   ├── index.vue       # Homepage
│   ├── courses.vue     # Course curriculum
│   └── about.vue       # About page
├── public/             # Static assets (logo, images, etc.)
├── nuxt.config.ts      # Nuxt configuration
├── package.json        # Dependencies and scripts
└── tailwind.config.js  # Tailwind CSS configuration
```

## 🎨 Design Features

- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Modern UI**: Clean, professional design with blue theme
- **Component-Based**: Reusable components for scalability
- **SEO Optimized**: Meta tags, proper heading structure
- **Fast Loading**: Optimized assets and images

## 📄 Current Pages

### Homepage (`/`)
- Hero section with call-to-action
- Feature overview cards
- Course topic preview
- Contact CTA section

### Courses (`/courses`)
- Complete curriculum breakdown
- 6 detailed modules with topics and difficulty levels
- Duration estimates for each module
- Interactive course cards

### About (`/about`)
- Mission and vision
- Success statistics
- Learning journey roadmap
- Unique value propositions

## 🛠 Technology Stack

- **Framework**: Nuxt 3 (Vue.js)
- **Styling**: Tailwind CSS
- **Content**: Nuxt Content (ready for markdown)
- **Build Tool**: Vite
- **TypeScript**: Full TypeScript support
- **Fonts**: Google Fonts (Inter Flex, Newsreader, Source Code Pro)

## 🎨 Typography

- **Headings (H1-H6)**: Inter Flex at 900 weight (`font-heading font-black`)
- **Body Text**: Newsreader serif (`font-sans`)
- **Code Elements**: Source Code Pro (`font-mono`)

## 🎯 Next Steps

### Content Integration
Since the GitHub repo was private, you'll need to:

1. **Add Course Content**: 
   - Place markdown files in the `content/` directory
   - Use Nuxt Content to create dynamic course pages

2. **Enhance Features**:
   - Add user authentication/enrollment
   - Integrate payment processing
   - Add progress tracking
   - Include video/interactive content

3. **Customization**:
   - Update logo and branding colors
   - Add testimonials and reviews
   - Include instructor profiles
   - Add FAQ section

### Content Structure Example
```
content/
├── courses/
│   ├── introduction-to-telephony/
│   │   ├── index.md
│   │   ├── lesson-1.md
│   │   └── lesson-2.md
│   └── sip-protocol/
│       ├── index.md
│       └── labs/
└── blog/
    └── telephony-trends-2024.md
```

## 🌐 Development URLs

- **Development**: http://localhost:3000
- **Production**: Ready for deployment to Vercel, Netlify, etc.

## 📝 Customization Guide

### Colors
Update the primary colors in `tailwind.config.js`:
```js
colors: {
  primary: {
    50: '#eff6ff',   // Light blue backgrounds
    500: '#3b82f6',  // Main blue
    600: '#2563eb',  // Hover states
    700: '#1d4ed8',  // Pressed states
  }
}
```

### Logo
Replace `/public/logo.png` with your new logo (already using the one from telephony-mastery folder).

### Content
- Edit page content in `pages/*.vue` files
- Add new pages by creating new `.vue` files in `pages/`
- Use the `layouts/default.vue` for consistent navigation

## 📈 Performance

- Lighthouse scores optimized
- Image lazy loading enabled
- CSS/JS minification in production
- SEO-friendly routing structure

---

**Status**: ✅ Fully functional development environment ready
**Next**: Add your course content and customize branding!
# NY Times-Style Paywall Component

A professional paywall component designed to integrate seamlessly with the Telephony Mastery site's newspaper/directory aesthetic.

## Features

- 🗞️ **Newspaper Design**: Matches site's black borders, uppercase typography, and vintage styling
- 📏 **Word-Based Gating**: Shows content freely until word limit (default 300 words)
- 🎨 **Gradient Fade**: Professional gradient mask similar to NY Times and Chicago Tribune
- 📱 **Mobile Responsive**: Optimized for all screen sizes
- 🎯 **Customizable**: Configurable word limits and subscriber counts
- ♿ **Accessible**: Proper ARIA labels and keyboard navigation
- 🖨️ **Print-Friendly**: Hidden during printing for better UX

## Usage

### Basic Implementation

The paywall is automatically integrated into content pages via `[...slug].vue`. It wraps all content rendered through `ContentRenderer`.

```vue
<PaywallGate 
  :enabled="true"
  :word-limit="300"
  :subscriber-count="15000"
  @request-access="handleRequestAccess"
  @learn-more="handleLearnMore"
>
  <ContentRenderer :value="data" />
</PaywallGate>
```

### Content Configuration

Control paywall behavior through frontmatter in your content files:

```yaml
---
title: "Advanced SIP Protocol Configuration"
description: "Deep dive into SIP protocol configuration and optimization"
paywall: true              # Enable/disable paywall (default: true)
paywallWordLimit: 450      # Custom word limit (default: 300)
---
```

### Disable Paywall for Specific Content

```yaml
---
title: "Free Introduction Lesson"
description: "Open access lesson for new students"
paywall: false             # Disables paywall completely
---
```

## Component Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `enabled` | Boolean | `true` | Whether to show the paywall |
| `wordLimit` | Number | `300` | Number of words before paywall appears |
| `subscriberCount` | Number | `15000` | Number shown in credibility line |

## Events

| Event | Description |
|-------|-------------|
| `@request-access` | Fired when "REQUEST FULL DOCUMENT" button is clicked |
| `@learn-more` | Fired when "LEARN MORE ABOUT ACCESS" button is clicked |

## Styling

The component uses the site's existing design system:

- **Typography**: Inter Flex for headings, Newsreader for body text
- **Colors**: Black borders, white backgrounds, gray gradients
- **Layout**: Consistent with site's newspaper/directory aesthetic
- **Buttons**: Sharp corners, uppercase text, bold styling

### Custom Styling

The component is built with scoped CSS that inherits from your site's design system. Key classes:

```css
.paywall-box        /* Main paywall container */
.paywall-headline   /* "PREMIUM CONTENT" heading */
.paywall-button     /* Call-to-action buttons */
.paywall-gradient   /* Fade effect overlay */
```

## Integration Examples

### Standard Content Page

```vue
<!-- Automatic integration via [...slug].vue -->
<PaywallGate 
  :enabled="data?.paywall !== false"
  :word-limit="data?.paywallWordLimit || 300"
  @request-access="() => navigateTo('/courses?subscribe=true')"
  @learn-more="() => navigateTo('/about#pricing')"
>
  <ContentRenderer :value="data" />
</PaywallGate>
```

### Custom Implementation

```vue
<template>
  <PaywallGate 
    :enabled="showPaywall"
    :word-limit="500"
    :subscriber-count="25000"
    @request-access="handleSubscribe"
    @learn-more="showPricing"
  >
    <article>
      <!-- Your content here -->
    </article>
  </PaywallGate>
</template>

<script setup>
const handleSubscribe = () => {
  // Custom subscription logic
  window.open('https://your-payment-processor.com/subscribe', '_blank')
}

const showPricing = () => {
  // Show pricing modal or navigate to pricing page
  navigateTo('/pricing')
}
</script>
```

## Demo

Visit `/paywall-demo` to see the component in action with a 50-word limit for quick testing.

## Customization

### Word Limit Strategy

- **Free Preview**: 200-300 words (1-2 paragraphs)
- **Premium Courses**: 400-500 words (introduction + first section)
- **Sample Lessons**: 150 words (just the introduction)

### Content Strategy

The component works best when:
1. Content has a natural break point around the word limit
2. The paywall appears after an introduction but before valuable details
3. The preview provides enough value to entice subscriptions
4. Headlines and bullet points are optimized for the cutoff point

### Analytics Integration

Track paywall interactions:

```vue
<PaywallGate 
  @request-access="() => {
    gtag('event', 'paywall_request_access', {
      page_title: data.title,
      word_limit: 300
    })
    handleRequestAccess()
  }"
  @learn-more="() => {
    gtag('event', 'paywall_learn_more')
    handleLearnMore()
  }"
>
```

## Browser Support

- ✅ Chrome/Safari/Firefox (modern versions)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)
- ✅ Progressive enhancement for older browsers
- ✅ Print-friendly (paywall hidden when printing)

## Troubleshooting

### Paywall Not Appearing
1. Check that `enabled` prop is `true`
2. Verify content has more words than `wordLimit`
3. Ensure content is properly rendered before paywall component

### Content Cut Off Incorrectly
- The component counts words in the rendered text content
- HTML tags and formatting are excluded from word count
- Adjust `wordLimit` based on your typical content density

### Styling Issues
- Component inherits from site's existing CSS classes
- Check that Tailwind CSS classes are available
- Verify Inter Flex and Newsreader fonts are loaded

## Performance Notes

- Component uses minimal JavaScript for word counting
- CSS transforms provide smooth animations
- No external dependencies beyond Vue 3
- Optimized for Core Web Vitals compliance
<template>
  <div>
    <!-- Section Index Page -->
    <div v-if="data?.layout === 'section-index'" class="py-8">
      <div class="container-custom">
        <!-- Header -->
        <div class="directory-header mb-8">
          <div class="border-4 border-black p-6">
            <h1 class="text-4xl md:text-5xl font-black uppercase text-center leading-none mb-4 tracking-tighter">
              {{ data.title }}
            </h1>
            <div class="text-center">
              <p class="text-sm uppercase tracking-wider font-bold">
                {{ data.description }}
              </p>
            </div>
          </div>
        </div>

        <!-- Lesson List -->
        <div class="border-4 border-black">
          <div class="p-6">
            <ContentRenderer :value="data" />
          </div>
        </div>

        <!-- Back to Courses -->
        <div class="mt-8 text-center">
          <NuxtLink to="/courses" class="inline-block border-2 border-black px-6 py-3 bg-black text-white hover:bg-gray-800 text-sm font-bold uppercase tracking-wider">
            ← Back to Courses
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Regular Lesson Page -->
    <div v-else class="py-8">
      <div class="container-custom">
        <article class="max-w-[720px] mx-auto">
          <!-- Header -->
          <header class="mb-8">
            <div class="border-4 border-black p-6">
              <div class="vintage-badge text-xs mb-4 inline-block">
                {{ data?.module || 'LESSON' }}
              </div>
              <h1 class="text-3xl md:text-4xl font-black uppercase leading-tight mb-4 tracking-tight">
                {{ data?.title }}
              </h1>
              <p class="text-sm uppercase tracking-wider">{{ data?.description }}</p>
              
              <!-- Lesson Meta -->
              <div class="flex flex-wrap gap-4 mt-4">
                <div class="vintage-badge text-xs" v-if="data?.duration">
                  Duration: {{ data.duration }}
                </div>
                <div class="vintage-badge text-xs" v-if="data?.difficulty">
                  Level: {{ data.difficulty }}
                </div>
                <div class="vintage-badge text-xs" v-if="data?.lesson">
                  Lesson: {{ data.lesson }}
                </div>
              </div>
            </div>
          </header>

          <!-- Content -->
          <div class="prose prose-lg max-w-none border-4 border-black p-6 md:p-8">
            <PaywallGate 
              :enabled="data?.paywall !== false"
              :word-limit="data?.paywallWordLimit || 200"
              :subscriber-count="15000"
              :content-data="data"
              @request-access="handleRequestAccess"
              @learn-more="handleLearnMore"
            >
              <ContentRenderer :value="data" />
            </PaywallGate>
          </div>

          <!-- Navigation -->
          <nav class="mt-8 flex flex-col md:flex-row gap-4">
            <div class="flex-1">
              <NuxtLink :to="`/${currentSection}/`" v-if="currentSection" 
                class="inline-block border-2 border-black px-6 py-3 bg-black text-white hover:bg-gray-800 text-sm font-bold uppercase tracking-wider">
                ← Back to {{ getSectionTitle(currentSection) }}
              </NuxtLink>
            </div>
            
            <div class="flex gap-4">
              <NuxtLink v-if="prevLesson" :to="`/${prevLesson.section}/${prevLesson.slug}`" 
                class="inline-block border-2 border-black px-6 py-3 hover:bg-gray-100 text-sm font-bold uppercase tracking-wider">
                ← Previous
              </NuxtLink>
              <NuxtLink v-if="nextLesson" :to="`/${nextLesson.section}/${nextLesson.slug}`" 
                class="inline-block border-2 border-black px-6 py-3 hover:bg-gray-100 text-sm font-bold uppercase tracking-wider">
                Next →
              </NuxtLink>
            </div>
          </nav>
        </article>
      </div>
    </div>
  </div>
</template>

<script setup>
const route = useRoute()
const slug = Array.isArray(route.params.slug) ? route.params.slug : [route.params.slug]
const path = '/' + slug.join('/')

// Query content
const { data } = await useAsyncData(`content-${path}`, () => {
  return queryContent(path).findOne()
})

// Handle 404
if (!data.value) {
  throw createError({
    statusCode: 404,
    statusMessage: 'Page Not Found'
  })
}

// Set page meta
useHead({
  title: data.value?.title || 'Telephony Mastery',
  meta: [
    { name: 'description', content: data.value?.description || 'Learn telephony concepts and build real-world communication solutions' }
  ]
})

// Get current section for navigation
const currentSection = computed(() => {
  if (slug.length >= 1) {
    return slug[0]
  }
  return null
})

// Section titles mapping
const sectionTitles = {
  'pstn': 'PSTN Fundamentals',
  'digital-voice': 'Digital Voice & Codecs',
  'sip-protocol': 'SIP Protocol',
  'sip-call-flows': 'SIP Call Flows',
  'quality': 'Voice Quality',
  'security': 'Security & Encryption',
  'nat': 'NAT & Firewall Traversal',
  'troubleshooting': 'Troubleshooting',
  'rtp-rtcp': 'RTP & RTCP',
  'protocol-stack': 'Protocol Stack',
  'sdp': 'SDP (Session Description Protocol)',
  'bgp': 'BGP & Routing',
  'webrtc': 'WebRTC',
  'dns': 'DNS & Name Resolution',
  'packet-switching': 'Packet Switching'
}

const getSectionTitle = (section) => {
  return sectionTitles[section] || section.toUpperCase()
}

// TODO: Implement lesson navigation (prev/next)
const prevLesson = ref(null)
const nextLesson = ref(null)

// Paywall event handlers
const handleRequestAccess = () => {
  // Navigate to subscription/enrollment page
  // You can customize this URL to your enrollment flow
  navigateTo('/courses?subscribe=true')
}

const handleLearnMore = () => {
  // Navigate to about page or pricing information
  navigateTo('/about#pricing')
}
</script>

<style scoped>
.container-custom {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.vintage-badge {
  background: #000;
  color: #fff;
  padding: 0.5rem 1rem;
  border: 2px solid #000;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.prose {
  color: #1a1a1a;
}

.prose p {
  font-size: calc(1rem + 2px);
  line-height: 1.6;
}

.prose h1, .prose h2, .prose h3, .prose h4 {
  color: #000;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: -0.025em;
  margin-top: 40px;
  margin-bottom: 40px;
}

.prose h2 {
  border-bottom: 2px solid #000;
  padding-bottom: 0.5rem;
  margin-bottom: 1.5rem;
}

.prose blockquote {
  border-left: 4px solid #000;
  background: #f9f9f9;
  padding: 1rem 1.5rem;
  margin: 1.5rem 0;
  font-style: normal;
}

.prose code {
  background: #e5e5e5;
  padding: 0.125rem 0.25rem;
  border-radius: 2px;
  font-size: calc(0.875em - 2px);
}

.prose pre {
  background: #1a1a1a;
  color: #f1f1f1;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
}
</style>
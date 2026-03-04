<template>
  <div class="paywall-wrapper" ref="paywallWrapper">
    <!-- Content before paywall -->
    <div class="paywall-content" :class="{ 'content-masked': showPaywall }">
      <slot />
    </div>
    
    <!-- Paywall overlay -->
    <div v-if="showPaywall" class="paywall-overlay">
      <!-- Gradient fade -->
      <div class="paywall-gradient"></div>
      
      <!-- Paywall CTA -->
      <div class="paywall-cta">
        <div class="paywall-box">
          <h3 class="paywall-headline">
            {{ (contentData?.title || 'PREMIUM CONTENT').toUpperCase() }}
          </h3>
          
          <h4 class="paywall-subtitle">
            FULL COURSE CONTENT AVAILABLE
          </h4>
          
          <p class="paywall-subhead">
            This is a preview of the Telephony Mastery Course. The complete lesson includes:
          </p>
          
          <ul class="paywall-benefits">
            <li v-for="benefit in getLessonBenefits()" :key="benefit">
              • {{ benefit }}
            </li>
          </ul>
          
          <div class="paywall-actions">
            <button @click="$emit('request-access')" class="paywall-button primary">
              REQUEST FULL DOCUMENT
            </button>
            <button @click="$emit('learn-more')" class="paywall-button secondary">
              LEARN MORE ABOUT ACCESS
            </button>
          </div>
          
          <!-- Professional credibility line -->
          <div class="paywall-credibility">
            <div class="text-xs uppercase tracking-wider font-bold">
              TRUSTED BY {{ subscriberCount.toLocaleString() }}+ PROFESSIONALS
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'

const props = defineProps({
  wordLimit: {
    type: Number,
    default: 300
  },
  enabled: {
    type: Boolean,
    default: true
  },
  subscriberCount: {
    type: Number,
    default: 15000
  },
  contentData: {
    type: Object,
    default: null
  }
})

// Lesson-specific paywall content from our summaries
const getLessonBenefits = () => {
  const slug = props.contentData?.slug || ''
  
  const lessonBenefits = {
    'basic-call-setup': [
      'Complete INVITE-to-BYE call flow with timing analysis and failure points',
      'Session establishment troubleshooting using SIP ladders and RTCP feedback', 
      'Advanced call setup scenarios: early media, forking, and provisional responses',
      'NAT traversal techniques during initial call negotiation (STUN/TURN/ICE)',
      'Carrier-grade call setup optimization strategies for sub-100ms post-dial delay'
    ],
    'analog-to-digital': [
      'Nyquist sampling theorem calculations for preventing aliasing in voice digitization',
      'Quantization noise analysis and how bit depth affects call quality (8-bit vs 16-bit impact)',
      'Real-world A-law vs μ-law codec comparison with actual MOS score differences', 
      'PCM encoding troubleshooting scenarios with Wireshark packet captures',
      'Advanced anti-aliasing filter configuration for enterprise VoIP deployments'
    ],
    'bgp-fundamentals': [
      'BGP path selection algorithm deep dive with real routing table examples',
      'Advanced BGP attributes manipulation (MED, Local Pref, AS Path prepending)',
      'Route origin validation (ROV) implementation for telecom network security',
      'BGP hijacking detection and mitigation strategies with case studies',
      'Multi-homed network design patterns for carrier-grade voice infrastructure'
    ]
    // Add more as needed
  }
  
  return lessonBenefits[slug] || [
    'Detailed technical explanations and advanced concepts',
    'Real-world examples and practical applications', 
    'Industry best practices and troubleshooting guides',
    'Expert insights and professional certification preparation',
    'Hands-on exercises and assessment materials'
  ]
}

const emit = defineEmits(['request-access', 'learn-more'])

const paywallWrapper = ref(null)
const showPaywall = ref(false)

const checkWordCount = () => {
  if (!props.enabled || !paywallWrapper.value) return
  
  // Get all text content from the slot
  const contentEl = paywallWrapper.value.querySelector('.paywall-content')
  if (!contentEl) return
  
  const textContent = contentEl.textContent || contentEl.innerText || ''
  const wordCount = textContent.trim().split(/\s+/).filter(word => word.length > 0).length
  
  showPaywall.value = wordCount > props.wordLimit
}

onMounted(async () => {
  await nextTick()
  // Small delay to ensure content is rendered
  setTimeout(checkWordCount, 100)
})
</script>

<style scoped>
/* Global paywall styles - not scoped */
</style>

<style>
/* NY TIMES STYLE PAYWALL - ELEGANT FADE */
.paywall-content.content-masked {
  position: relative;
}
</style>

<style scoped>
.paywall-wrapper {
  position: relative;
}

.paywall-content {
  transition: all 0.3s ease;
}

.paywall-content.content-masked {
  overflow: hidden;
  max-height: 600px; /* Approximate height for ~300 words */
  position: relative;
}

/* NY Times style fade - only affects bottom portion */
.paywall-content.content-masked::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 120px; /* Gradient fade zone */
  background: linear-gradient(
    to bottom,
    rgba(249, 250, 251, 0) 0%,
    rgba(249, 250, 251, 0.7) 40%,
    rgba(249, 250, 251, 1) 100%
  );
  pointer-events: none;
  z-index: 2;
}

.paywall-overlay {
  position: relative;
  margin-top: -100px; /* Overlap content slightly */
  z-index: 10;
}

/* Ensure paywall content stays below the overlay */
.paywall-content {
  position: relative;
  z-index: 1;
}

.paywall-gradient {
  height: 100px;
  background: linear-gradient(
    to bottom,
    rgba(249, 250, 251, 0) 0%,
    rgba(249, 250, 251, 0.8) 50%,
    rgba(249, 250, 251, 1) 100%
  );
  pointer-events: none;
}

.paywall-cta {
  background: #f9fafb;
  padding: 2rem 0 3rem 0;
  border-top: 4px solid #000;
  border-bottom: 4px solid #000;
}

.paywall-box {
  max-width: 500px;
  margin: 0 auto;
  text-align: center;
  background: white;
  border: 4px solid #000;
  padding: 2.5rem 2rem;
  box-shadow: 8px 8px 0 #000;
}

.paywall-icon {
  margin-bottom: 1.5rem;
}

.paywall-headline {
  font-family: 'Inter Flex', system-ui, sans-serif;
  font-size: 1.75rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: -0.02em;
  line-height: 1.1;
  margin-bottom: 0.5rem;
  color: #000;
}

.paywall-subtitle {
  font-family: 'Inter Flex', system-ui, sans-serif;
  font-size: 1rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 1.5rem;
  color: #6b7280;
}

.paywall-subhead {
  font-family: 'Newsreader', serif;
  font-size: 1.125rem;
  line-height: 1.5;
  color: #374151;
  margin-bottom: 1.5rem;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.paywall-benefits {
  list-style: none;
  padding: 0;
  margin: 2rem 0;
  text-align: left;
  max-width: 350px;
  margin-left: auto;
  margin-right: auto;
}

.paywall-benefits li {
  font-family: 'Inter Flex', system-ui, sans-serif;
  font-size: 0.875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.75rem;
  color: #000;
}

.paywall-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin: 2rem 0 1.5rem 0;
}

.paywall-button {
  font-family: 'Inter Flex', system-ui, sans-serif;
  font-weight: 900;
  text-transform: uppercase;
  font-size: 0.875rem;
  letter-spacing: 0.05em;
  padding: 1rem 2rem;
  border: 2px solid #000;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.paywall-button.primary {
  background: #000;
  color: #fff;
}

.paywall-button.primary:hover {
  background: #374151;
  transform: translateY(-2px);
  box-shadow: 4px 6px 0 #000;
}

.paywall-button.secondary {
  background: #fff;
  color: #000;
}

.paywall-button.secondary:hover {
  background: #f3f4f6;
  transform: translateY(-2px);
  box-shadow: 4px 6px 0 #000;
}

.paywall-credibility {
  border-top: 2px solid #000;
  padding-top: 1rem;
  color: #6b7280;
}

/* Mobile responsiveness */
@media (max-width: 640px) {
  .paywall-box {
    margin: 0 1rem;
    padding: 1.5rem 1rem;
    box-shadow: 4px 4px 0 #000;
  }
  
  .paywall-headline {
    font-size: 1.5rem;
  }
  
  .paywall-subhead {
    font-size: 1rem;
  }
  
  .paywall-actions {
    gap: 0.75rem;
  }
  
  .paywall-button {
    padding: 0.875rem 1.5rem;
    min-height: 50px;
    font-size: 0.75rem;
  }
}

/* Print styles - hide paywall when printing */
@media print {
  .paywall-overlay {
    display: none !important;
  }
  
  .paywall-content.content-masked {
    max-height: none !important;
    overflow: visible !important;
  }
}
</style>
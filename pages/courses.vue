<template>
  <div class="py-8">
    <div class="max-w-[720px] mx-auto px-4">
      <!-- Header -->
      <div class="directory-header mb-8">
        <div class="border-4 border-black p-6">
          <h1 class="text-5xl md:text-6xl font-black uppercase text-center leading-none mb-4 tracking-tighter">
            COURSE<br>
            CURRICULUM
          </h1>
          <div class="text-center">
            <p class="text-sm uppercase tracking-wider font-bold">
              COMPREHENSIVE TRAINING — HANDS-ON APPROACH — MODERN SYSTEMS
            </p>
          </div>
        </div>
      </div>

      <!-- Course Sections -->
      <div class="border-4 border-black">
        <div v-for="(section, index) in courseSections" :key="section.slug" class="border-b-2 border-black last:border-b-0">
          <div class="p-6 hover:bg-gray-50 transition-colors">
            <NuxtLink :to="`/${section.slug}/`" class="block">
              <div class="flex items-start gap-4">
                <div class="flex-shrink-0">
                  <div class="vintage-badge text-lg w-16 h-16 flex items-center justify-center">
                    {{ String(index + 1).padStart(2, '0') }}
                  </div>
                </div>
                <div class="flex-1">
                  <div class="mb-4">
                    <h3 class="text-2xl font-black uppercase mb-2 tracking-tight hover:underline">
                      {{ section.title }}
                    </h3>
                    <p class="text-sm leading-snug uppercase tracking-wide">{{ section.description }}</p>
                  </div>
                  
                  <!-- Lesson Count and Topics -->
                  <div class="mb-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                      <div v-for="topic in section.topics" :key="topic" class="flex items-start gap-2">
                        <span class="text-xs mt-1">•</span>
                        <span class="text-xs uppercase leading-tight">{{ topic }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Duration and Lesson Count -->
                  <div class="flex items-center gap-6">
                    <div class="vintage-badge text-xs">
                      {{ section.lessonCount }} LESSONS
                    </div>
                    <div class="vintage-badge text-xs">
                      LEVEL: {{ section.difficulty }}
                    </div>
                  </div>
                </div>
                <div class="flex-shrink-0 self-center">
                  <div class="text-2xl">→</div>
                </div>
              </div>
            </NuxtLink>
          </div>
        </div>
      </div>

      <!-- CTA -->
      <div class="mt-8 text-center">
        <div class="border-4 border-black p-6 bg-black text-white max-w-2xl mx-auto">
          <div class="border-2 border-white p-4">
            <h3 class="text-2xl font-black uppercase mb-2 tracking-tight">START LEARNING</h3>
            <p class="text-xs uppercase tracking-wide mb-4">
              {{ totalLessons }} LESSONS • PRACTICAL EXAMPLES • REAL-WORLD SCENARIOS
            </p>
            <NuxtLink to="/pstn/" class="btn btn-primary bg-white text-black hover:bg-gray-200">
              BEGIN WITH PSTN FUNDAMENTALS
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
useHead({
  title: 'Courses - Telephony Mastery',
  meta: [
    { name: 'description', content: 'Explore our comprehensive telephony course curriculum with hands-on labs and real-world projects.' }
  ]
})

const courseSections = [
  {
    slug: 'pstn',
    title: 'PSTN Fundamentals',
    description: 'Master the foundations of the Public Switched Telephone Network — from circuit switching to SS7 signaling.',
    lessonCount: 4,
    difficulty: 'Beginner',
    topics: [
      'Birth of telephony and central offices',
      'Circuit switching vs packet switching', 
      'SS7 signaling and call routing',
      'Number portability and LNP database'
    ]
  },
  {
    slug: 'digital-voice',
    title: 'Digital Voice & Codecs',
    description: 'Deep dive into audio codecs, compression algorithms, and voice quality metrics.',
    lessonCount: 7,
    difficulty: 'Intermediate',
    topics: [
      'Analog to digital conversion',
      'G.711, G.729, Opus codecs',
      'Voice quality metrics (MOS, PESQ)',
      'Compression vs quality tradeoffs'
    ]
  },
  {
    slug: 'protocol-stack',
    title: 'Network Protocol Stack',
    description: 'Build a solid foundation in networking — from Ethernet to UDP to TLS.',
    lessonCount: 7,
    difficulty: 'Intermediate',
    topics: [
      'Ethernet frames and Layer 2 switching',
      'IPv4/IPv6 addressing and routing',
      'UDP vs TCP for real-time traffic',
      'TLS encryption and security'
    ]
  },
  {
    slug: 'dns',
    title: 'DNS & Name Resolution',
    description: 'Master DNS resolution, load balancing, and troubleshooting.',
    lessonCount: 3,
    difficulty: 'Intermediate',
    topics: [
      'DNS hierarchy and resolution',
      'GeoDNS and load balancing',
      'Troubleshooting with dig/nslookup'
    ]
  },
  {
    slug: 'bgp',
    title: 'BGP & Internet Routing',
    description: 'Understand Border Gateway Protocol and how voice packets traverse global networks.',
    lessonCount: 4,
    difficulty: 'Advanced',
    topics: [
      'Autonomous systems and peering',
      'BGP path selection and policies',
      'Internet exchange points',
      'BGP hijacks and troubleshooting'
    ]
  },
  {
    slug: 'nat',
    title: 'NAT & Firewall Traversal',
    description: 'Conquer NAT traversal — the biggest challenge in VoIP deployment.',
    lessonCount: 3,
    difficulty: 'Advanced',
    topics: [
      'NAT fundamentals and types',
      'SIP/RTP traversal problems',
      'STUN, TURN, ICE, and media anchoring'
    ]
  },
  {
    slug: 'rtp-rtcp',
    title: 'RTP & RTCP',
    description: 'Master the Real-time Transport Protocol and quality monitoring.',
    lessonCount: 3,
    difficulty: 'Intermediate',
    topics: [
      'RTP packet structure and flow',
      'RTCP feedback and quality reports',
      'DTMF and telephone event handling'
    ]
  },
  {
    slug: 'quality',
    title: 'Voice Quality Engineering',
    description: 'Learn to measure, monitor, and troubleshoot voice quality issues.',
    lessonCount: 5,
    difficulty: 'Advanced',
    topics: [
      'Latency budgets and sources',
      'Jitter and jitter buffer management',
      'Packet loss and recovery',
      'Quality metrics and monitoring'
    ]
  },
  {
    slug: 'sip-protocol',
    title: 'SIP Protocol Deep Dive',
    description: 'Master the Session Initiation Protocol — the backbone of modern VoIP.',
    lessonCount: 7,
    difficulty: 'Advanced',
    topics: [
      'SIP architecture and components',
      'Methods, headers, and response codes',
      'Registration and authentication',
      'Dialogs and transaction state'
    ]
  },
  {
    slug: 'sip-call-flows',
    title: 'SIP Call Flow Scenarios',
    description: 'Understand real-world SIP scenarios from basic calls to advanced features.',
    lessonCount: 4,
    difficulty: 'Advanced',
    topics: [
      'Basic call setup flow',
      'Call failures and error handling',
      'Call transfer with REFER',
      'Hold, resume, and re-INVITE'
    ]
  },
  {
    slug: 'sdp',
    title: 'Session Description Protocol',
    description: 'Master SDP for media negotiation and codec selection.',
    lessonCount: 2,
    difficulty: 'Advanced',
    topics: [
      'SDP structure and offer/answer',
      'Codec negotiation and interworking'
    ]
  },
  {
    slug: 'security',
    title: 'VoIP Security',
    description: 'Secure your voice infrastructure against attacks and eavesdropping.',
    lessonCount: 2,
    difficulty: 'Advanced',
    topics: [
      'SRTP media encryption',
      'End-to-end vs hop-by-hop security'
    ]
  },
  {
    slug: 'troubleshooting',
    title: 'Systematic Troubleshooting',
    description: 'Develop methodical approaches to diagnosing voice problems.',
    lessonCount: 2,
    difficulty: 'Expert',
    topics: [
      'Call quality troubleshooting methodology',
      'Network diagnostics and path analysis'
    ]
  },
  {
    slug: 'webrtc',
    title: 'WebRTC Fundamentals',
    description: 'Explore browser-based real-time communication.',
    lessonCount: 1,
    difficulty: 'Intermediate',
    topics: [
      'WebRTC architecture and APIs'
    ]
  },
  {
    slug: 'packet-switching',
    title: 'Packet Switching & QoS',
    description: 'Understand modern packet networks and Quality of Service.',
    lessonCount: 2,
    difficulty: 'Advanced',
    topics: [
      'Store-and-forward packet switching',
      'QoS, DSCP, and traffic shaping'
    ]
  }
]

const totalLessons = computed(() => {
  return courseSections.reduce((total, section) => total + section.lessonCount, 0)
})
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

.btn-primary {
  padding: 0.75rem 1.5rem;
  border: 2px solid transparent;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.1em;
  transition: all 0.2s ease;
  text-decoration: none;
  display: inline-block;
}

.btn-primary:hover {
  transform: translateY(-1px);
}
</style>
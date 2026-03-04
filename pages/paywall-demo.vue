<template>
  <div class="py-8">
    <div class="container-custom">
      <article class="max-w-[600px] mx-auto">
        <!-- Header -->
        <header class="mb-8">
          <div class="border-4 border-black p-6">
            <div class="vintage-badge text-xs mb-4 inline-block">
              DEMO
            </div>
            <h1 class="text-3xl md:text-4xl font-black uppercase leading-tight mb-4 tracking-tight">
              Rich Paywall Demo
            </h1>
            <p class="text-sm uppercase tracking-wider">Experience the enhanced lesson-specific paywall with auto-generated content summaries</p>
          </div>
        </header>

        <!-- Content with Paywall -->
        <div class="prose prose-lg max-w-none border-4 border-black p-6 md:p-8">
          <PaywallGate 
            :enabled="paywallEnabled"
            :word-limit="50"
            :subscriber-count="15000"
            :content-data="demoLessonData"
            @request-access="handleRequestAccess"
            @learn-more="handleLearnMore"
          >
            <h2>Understanding SIP Protocol Fundamentals</h2>
            
            <p>The Session Initiation Protocol (SIP) is a signaling protocol used for initiating, maintaining, and terminating real-time sessions that include voice, video and messaging applications. SIP is defined in RFC 3261 and is one of the most important protocols in modern telecommunications.</p>

            <p>SIP works as an application-layer control protocol that can establish, modify, and terminate multimedia sessions between two or more endpoints. These sessions include Internet telephony calls, multimedia distribution, and multimedia conferencing. The protocol is designed to be independent of the underlying transport layer; it can run on Transmission Control Protocol (TCP), User Datagram Protocol (UDP), or Stream Control Transmission Protocol (SCTP).</p>

            <h3>Key Components of SIP Architecture</h3>

            <p>SIP operates using several key components that work together to manage communication sessions. The User Agent (UA) represents the endpoints in a SIP communication system. There are two types of User Agents: User Agent Client (UAC) which initiates SIP requests, and User Agent Server (UAS) which receives and responds to SIP requests.</p>

            <p>The SIP proxy server is another crucial component that receives SIP requests from clients and forwards them to other SIP servers or directly to the destination User Agent. Proxy servers can perform various functions including authentication, authorization, network access control, routing, reliable request retransmission, and security.</p>

            <h3>SIP Message Structure</h3>

            <p>SIP messages are text-based and follow a format similar to HTTP. Each SIP message consists of a start line, one or more header fields, an empty line indicating the end of the header fields, and an optional message body. The start line can be either a request line (for requests) or a status line (for responses).</p>

            <p>Request messages include methods such as INVITE (establish a session), ACK (acknowledge a response), BYE (terminate a session), CANCEL (cancel a pending request), REGISTER (register a user's location), and OPTIONS (query a server about its capabilities).</p>

            <h3>Call Flow Examples</h3>

            <p>A typical SIP call flow begins with the caller sending an INVITE request to the callee. This INVITE contains session description information, typically using the Session Description Protocol (SDP), which describes the media parameters for the proposed session. The callee responds with a status code indicating whether they accept, reject, or redirect the call.</p>

            <p>If the call is accepted, the callee sends a 200 OK response, and the caller acknowledges this with an ACK request. At this point, the media session can begin using the Real-time Transport Protocol (RTP). When either party wants to end the call, they send a BYE request, which is acknowledged by the other party.</p>

            <h3>Advanced SIP Features</h3>

            <p>SIP supports various advanced features that make it suitable for enterprise communications. These include call transfer, call forwarding, call waiting, conference calling, and presence services. The protocol's extensibility allows for the addition of new features through the definition of new methods and headers.</p>
          </PaywallGate>
        </div>

        <!-- Demo Controls -->
        <div class="mt-8 p-6 border-2 border-black bg-gray-50">
          <h3 class="font-black uppercase text-lg mb-4">✨ Rich Paywall Features</h3>
          <p class="text-sm mb-4"><strong>NEW:</strong> This enhanced paywall automatically generates lesson-specific content from frontmatter including:</p>
          
          <ul class="text-xs mb-4 space-y-1">
            <li>📚 <strong>Big bold lesson title header</strong> from frontmatter</li>
            <li>🔒 <strong>Lock icon + "FULL COURSE CONTENT AVAILABLE"</strong> professional styling</li>
            <li>📝 <strong>Lesson-specific preview text</strong> from description</li>
            <li>✅ <strong>Green checkmark objectives</strong> auto-generated from lesson objectives</li>
            <li>🚀 <strong>Enhanced CTA button</strong> with modern styling</li>
            <li>🏷️ <strong>Lesson metadata badges</strong> (module, duration, difficulty)</li>
          </ul>
          
          <p class="text-xs mb-4 italic">Demo triggers after 50 words. Production typically uses 300+ words.</p>
          
          <div class="flex flex-wrap gap-4">
            <button @click="togglePaywall" class="btn btn-secondary text-xs">
              {{ paywallEnabled ? 'DISABLE' : 'ENABLE' }} PAYWALL
            </button>
            <NuxtLink to="/courses" class="btn btn-primary text-xs">
              VIEW LIVE LESSONS
            </NuxtLink>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

useHead({
  title: 'Rich Paywall Demo - Telephony Mastery',
  meta: [
    { name: 'description', content: 'Demonstration of the enhanced NY Times-style rich paywall component' }
  ]
})

const paywallEnabled = ref(true)

// Demo lesson data to showcase rich paywall functionality
const demoLessonData = {
  title: "Advanced SIP Call Transfer Mechanisms",
  description: "Master the complexities of SIP REFER method, Replaces header, and B2BUA transfer handling in enterprise telephony systems.",
  module: "Module 3: SIP Protocol Mastery",
  lesson: "15",
  difficulty: "Advanced",
  duration: "45 minutes",
  objectives: [
    "Understand blind transfer implementation using REFER with simple Refer-To targets",
    "Master attended transfer coordination with REFER and Replaces parameters",
    "Analyze NOTIFY messages for transfer progress monitoring and failure diagnosis",
    "Troubleshoot common SIP transfer interoperability issues across vendor platforms",
    "Implement B2BUA transfer handling with proper media re-bridging strategies"
  ]
}

const togglePaywall = () => {
  paywallEnabled.value = !paywallEnabled.value
  // Force component re-render by changing key
  location.reload()
}

const handleRequestAccess = () => {
  alert('🚀 Unlock Full Course Access clicked! In production, this would redirect to your enrollment/subscription flow.')
}

const handleLearnMore = () => {
  alert('View Pricing & Plans clicked! In production, this would show pricing or about information.')
}
</script>
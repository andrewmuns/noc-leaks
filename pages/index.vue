<template>
  <div>
    <!-- Directory Header -->
    <section class="directory-header">
      <div class="container-custom">
        <div class="border-4 border-black p-8 bg-white">
          <h1 class="text-6xl md:text-8xl font-black uppercase text-center leading-none mb-4 tracking-tighter">
            TELEPHONY<br>
            SYSTEMS<br>
            ENGINEERING
          </h1>
          
          <div class="text-center mb-6">
            <p class="text-lg font-bold uppercase tracking-wide">
              Provided courtesy of Telnyx NoC Engineers
            </p>
            <p class="text-sm uppercase tracking-wider">
              SIP Protocol • Voice Quality • Network Infrastructure • Security
            </p>
          </div>
          
          <div class="flex flex-col sm:flex-row gap-4 justify-center">
            <NuxtLink to="/courses" class="btn btn-primary">
              START TRAINING
            </NuxtLink>
            <NuxtLink to="/about" class="btn btn-secondary">
              LEARN MORE
            </NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <!-- Services Listing -->
    <section class="py-12 bg-white border-t-4 border-b-4 border-black">
      <div class="container-custom">
        <div class="text-center mb-8">
          <div class="vintage-badge inline-block mb-4">KNOWLEDGE BASE</div>
          <h2 class="text-4xl font-black uppercase tracking-tight">TECHNICAL TOPICS</h2>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-1">
          <div class="card text-left">
            <div class="vintage-badge mb-3">001</div>
            <h3 class="text-xl font-black uppercase mb-2">PROTOCOL FUNDAMENTALS</h3>
            <p class="text-sm leading-snug">
              UDP VS TCP • CODECS • SIP ARCHITECTURE • RTP FLOWS • NETWORK STACK
            </p>
          </div>
          
          <div class="card text-left">
            <div class="vintage-badge mb-3">002</div>
            <h3 class="text-xl font-black uppercase mb-2">CALL FLOWS & DEBUG</h3>
            <p class="text-sm leading-snug">
              SIP SCENARIOS • TROUBLESHOOTING • QUALITY ANALYSIS • SYSTEMATIC METHODS
            </p>
          </div>
          
          <div class="card text-left">
            <div class="vintage-badge mb-3">003</div>
            <h3 class="text-xl font-black uppercase mb-2">ADVANCED TOPICS</h3>
            <p class="text-sm leading-snug">
              JITTER ANALYSIS • NAT TRAVERSAL • BGP ROUTING • WEBRTC • SECURITY
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Directory Listings -->
    <section class="py-12 bg-white">
      <div class="container-custom">
        <div class="border-4 border-black p-6">
          <div class="text-center mb-6">
            <h2 class="text-3xl font-black uppercase tracking-tight mb-2">TECHNICAL MODULES</h2>
            <p class="text-sm uppercase tracking-wide font-bold">
              52+ LESSONS — PROTOCOL ANALYSIS — REAL WORLD SCENARIOS
            </p>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-0 border-2 border-black">
            <div class="p-4 border-b-2 md:border-r-2 md:border-b-0 border-black">
              <div class="flex items-start gap-3">
                <div class="vintage-badge text-xs">A</div>
                <div class="flex-1">
                  <h4 class="font-black text-sm uppercase mb-1">PSTN FUNDAMENTALS</h4>
                  <p class="text-xs leading-tight">Circuit switching, SS7 signaling, number portability</p>
                </div>
              </div>
            </div>
            
            <div class="p-4 border-b-2 border-black">
              <div class="flex items-start gap-3">
                <div class="vintage-badge text-xs">B</div>
                <div class="flex-1">
                  <h4 class="font-black text-sm uppercase mb-1">DIGITAL VOICE & CODECS</h4>
                  <p class="text-xs leading-tight">G.711, G.729, Opus compression & voice quality</p>
                </div>
              </div>
            </div>
            
            <div class="p-4 border-b-2 md:border-r-2 md:border-b-0 border-black">
              <div class="flex items-start gap-3">
                <div class="vintage-badge text-xs">C</div>
                <div class="flex-1">
                  <h4 class="font-black text-sm uppercase mb-1">SIP PROTOCOL & CALL FLOWS</h4>
                  <p class="text-xs leading-tight">Registration, authentication, call scenarios</p>
                </div>
              </div>
            </div>
            
            <div class="p-4 border-b-2 border-black">
              <div class="flex items-start gap-3">
                <div class="vintage-badge text-xs">D</div>
                <div class="flex-1">
                  <h4 class="font-black text-sm uppercase mb-1">VOICE QUALITY & JITTER</h4>
                  <p class="text-xs leading-tight">Latency budgets, packet loss, troubleshooting</p>
                </div>
              </div>
            </div>
            
            <div class="p-4 md:border-r-2 border-black">
              <div class="flex items-start gap-3">
                <div class="vintage-badge text-xs">E</div>
                <div class="flex-1">
                  <h4 class="font-black text-sm uppercase mb-1">NAT & FIREWALL TRAVERSAL</h4>
                  <p class="text-xs leading-tight">STUN, TURN, ICE, media anchoring solutions</p>
                </div>
              </div>
            </div>
            
            <div class="p-4">
              <div class="flex items-start gap-3">
                <div class="vintage-badge text-xs">F</div>
                <div class="flex-1">
                  <h4 class="font-black text-sm uppercase mb-1">BGP & ROUTING</h4>
                  <p class="text-xs leading-tight">Internet routing, autonomous systems, peering</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Directory Footer -->
    <section class="py-8 bg-black text-white">
      <div class="container-custom">
        <div class="border-4 border-white p-6 text-center">
          <div class="mb-4">
            <h2 class="text-3xl font-black uppercase tracking-tight mb-2">ENROLLMENT OPEN</h2>
            <p class="text-sm uppercase tracking-wide font-bold">
              JOIN THOUSANDS OF CERTIFIED PROFESSIONALS
            </p>
          </div>
          
          <div class="mb-6 text-xs uppercase tracking-wider">
            COMPREHENSIVE TRAINING • EXPERT INSTRUCTION • INDUSTRY CERTIFICATION
          </div>
          
          <NuxtLink to="/courses" class="btn btn-primary bg-white text-black hover:bg-gray-200">
            VIEW FULL DIRECTORY
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
useHead({
  title: 'Telephony Mastery - Learn Modern Communication Systems',
  meta: [
    { name: 'description', content: 'Master telephony concepts and build real-world communication solutions with our comprehensive course.' }
  ]
})
</script>
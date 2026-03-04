<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b-4 border-black">
      <nav class="container-custom">
        <div class="flex items-center justify-between py-3">
          <!-- Directory Header -->
          <div class="flex items-center space-x-4">
            <div class="vintage-badge text-xs">☎</div>
            <h1 class="text-lg font-black uppercase tracking-tight">
              NoC Leaks
            </h1>
          </div>
          
          <!-- Navigation -->
          <div class="hidden md:flex items-center space-x-6">
            <NuxtLink to="/" class="text-xs font-black uppercase tracking-wide hover:text-gray-600">
              HOME
            </NuxtLink>
            <NuxtLink to="/courses" class="text-xs font-black uppercase tracking-wide hover:text-gray-600">
              COURSES
            </NuxtLink>
            <NuxtLink to="/about" class="text-xs font-black uppercase tracking-wide hover:text-gray-600">
              ABOUT
            </NuxtLink>
          </div>
          
          <!-- Mobile menu button -->
          <button 
            @click="mobileMenuOpen = !mobileMenuOpen"
            class="md:hidden vintage-badge text-xs"
          >
            MENU
          </button>
        </div>
        
        <!-- Mobile menu -->
        <div v-if="mobileMenuOpen" class="md:hidden py-4 border-t-2 border-black">
          <div class="flex flex-col space-y-2">
            <NuxtLink to="/" class="px-4 py-2 text-xs font-black uppercase tracking-wide hover:bg-gray-100">
              HOME
            </NuxtLink>
            <NuxtLink to="/courses" class="px-4 py-2 text-xs font-black uppercase tracking-wide hover:bg-gray-100">
              COURSES
            </NuxtLink>
            <NuxtLink to="/about" class="px-4 py-2 text-xs font-black uppercase tracking-wide hover:bg-gray-100">
              ABOUT
            </NuxtLink>
          </div>
        </div>
      </nav>
    </header>

    <!-- Main content -->
    <main>
      <slot />
    </main>

    <!-- Footer -->
    <footer class="bg-black text-white border-t-4 border-black">
      <div class="container-custom py-6">
        <div class="border-2 border-white p-4 text-center">
          <div class="text-xs uppercase tracking-wider font-bold mb-2">
            COPYRIGHT {{ new Date().getFullYear() }} — TELEPHONY MASTERY DIRECTORY
          </div>
          <div class="text-xs uppercase tracking-wider">
            ALL RIGHTS RESERVED • PROFESSIONAL TRAINING SERVICES
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const mobileMenuOpen = ref(false)
</script>
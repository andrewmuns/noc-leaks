#!/usr/bin/env python3
"""
Fix lesson mapping issues by moving lessons to correct sections based on content
"""

import os
import shutil
from pathlib import Path

# Correct mapping based on actual lesson titles and content
CORRECT_MAPPING = {
    # PSTN Section (1-4) ✓
    1: "pstn",     # The Birth of Telephony
    2: "pstn",     # Circuit Switching  
    3: "pstn",     # SS7 Signaling
    4: "pstn",     # Number Portability
    
    # Digital Voice Section (5-9)
    5: "digital-voice",     # Number Lookup and Caller Identity (CNAM) - moved from digital-voice 
    6: "digital-voice",     # Verify API — Two-Factor Authentication - moved from digital-voice
    7: "digital-voice",     # Analog to Digital — The Nyquist Theorem and PCM ✓
    8: "digital-voice",     # G.711 — The Universal Codec ✓
    9: "digital-voice",     # Compressed Codecs — G.729, G.722 ✓
    10: "digital-voice",    # Opus — The Modern Codec (moved from packet-switching)
    11: "digital-voice",    # Voice Quality Metrics (moved from packet-switching)
    
    # Packet Switching (10-11) -> NEW: (12-13)
    12: "packet-switching", # Packet Switching — Store-and-Forward (moved from protocol-stack)
    13: "packet-switching", # Quality of Service (QoS) (moved from protocol-stack)
    
    # Protocol Stack (12-18) -> NEW: (14-20)  
    14: "protocol-stack",   # Ethernet and Layer 2 ✓
    15: "protocol-stack",   # IPv4 — Addressing ✓
    16: "protocol-stack",   # IPv6 — Why It Exists ✓
    17: "protocol-stack",   # UDP — Why Real-Time Traffic ✓
    18: "protocol-stack",   # TCP — Reliability ✓
    19: "protocol-stack",   # TLS — How Encryption Works (moved from dns)
    20: "protocol-stack",   # The Application Layer (moved from dns)
    
    # DNS (19-21) -> NEW: (21-23)
    21: "dns",              # DNS Fundamentals ✓
    22: "dns",              # DNS-Based Load Balancing (moved from bgp)
    23: "dns",              # DNS Troubleshooting (moved from bgp)
    
    # BGP (22-25) -> NEW: (24-27)
    24: "bgp",              # Autonomous Systems ✓
    25: "bgp",              # BGP Mechanics ✓  
    26: "bgp",              # Peering, Transit (moved from nat)
    27: "bgp",              # BGP Incidents (moved from nat)
    
    # NAT (26-28) -> NEW: (28-30)
    28: "nat",              # NAT Fundamentals ✓
    29: "nat",              # NAT Traversal for SIP and RTP (moved from rtp-rtcp)
    30: "nat",              # SIP ALG, Session Border Controllers (moved from rtp-rtcp)
    
    # RTP/RTCP (29-31) -> NEW: (31-33)
    31: "rtp-rtcp",         # RTP — Real-time Transport Protocol ✓
    32: "rtp-rtcp",         # RTCP — Feedback, Quality Reporting (moved from quality)
    33: "rtp-rtcp",         # DTMF — RFC 2833/4733 (moved from quality)
    
    # Quality (32-36) -> NEW: (34-38)
    34: "quality",          # Latency Budget ✓
    35: "quality",          # Jitter — Why Packets Arrive ✓
    36: "quality",          # The Jitter Buffer ✓
    37: "quality",          # Packet Loss — Causes, Effects (moved from sip-protocol)
    38: "quality",          # Packet Reordering, Duplication (moved from sip-protocol)
    
    # SIP Protocol (37-43) -> NEW: (39-45)
    39: "sip-protocol",     # SIP Architecture ✓
    40: "sip-protocol",     # SIP Methods ✓
    41: "sip-protocol",     # SIP Headers ✓
    42: "sip-protocol",     # SIP Response Codes ✓
    43: "sip-protocol",     # SIP Dialogs and Transactions ✓
    44: "sip-protocol",     # SIP Registration (moved from sip-call-flows)
    45: "sip-protocol",     # SIP Authentication (moved from sip-call-flows)
    
    # SIP Call Flows (44-47) -> NEW: (46-49)
    46: "sip-call-flows",   # Basic Call Setup ✓
    47: "sip-call-flows",   # Call Failures ✓
    48: "sip-call-flows",   # Call Transfer (moved from sdp)
    49: "sip-call-flows",   # Call Hold, Resume (moved from sdp)
    
    # SDP (48-49) -> NEW: (50-51)
    50: "sdp",              # SDP Structure (moved from troubleshooting)
    51: "sdp",              # Codec Negotiation (moved from troubleshooting)
    
    # Troubleshooting (50-51) -> NEW: (52-53)
    52: "troubleshooting",  # Systematic Call Quality (moved from security)
    53: "troubleshooting",  # Network Diagnostics (moved from security)
    
    # Security (52-53) -> NEW: (54-55)
    54: "security",         # SRTP — Encrypting RTP (moved from webrtc)
    55: "security",         # End-to-End vs Hop-by-Hop (moved from webrtc)
    
    # WebRTC (54-56) -> NEW: (56)
    56: "webrtc",           # WebRTC Architecture ✓
}

def reorganize_lessons():
    """Reorganize lessons to correct sections"""
    base_path = Path.home() / 'Desktop/telephony-mastery/telephony-mastery-site/content/module-1-foundations'
    
    print("Reorganizing Module 1 lessons to correct sections...")
    print("=" * 60)
    
    # Create temporary directory for reorganization
    temp_dir = base_path / '_temp_reorganization'
    temp_dir.mkdir(exist_ok=True)
    
    moves_made = []
    errors = []
    
    # First, move all lessons to temp directory
    print("Step 1: Moving all lessons to temporary directory...")
    for lesson_num in range(1, 57):
        lesson_file = f"lesson-{lesson_num:03d}.md"
        
        # Find current location
        current_file = None
        for section_dir in base_path.iterdir():
            if section_dir.is_dir() and section_dir.name != '_temp_reorganization':
                potential_file = section_dir / lesson_file
                if potential_file.exists():
                    current_file = potential_file
                    break
        
        if current_file:
            temp_file = temp_dir / lesson_file
            shutil.move(str(current_file), str(temp_file))
            print(f"  Moved {lesson_file} to temp")
        else:
            error = f"Could not find {lesson_file}"
            print(f"  ❌ {error}")
            errors.append(error)
    
    # Second, move lessons from temp to correct sections
    print("\nStep 2: Moving lessons to correct sections...")
    for lesson_num in range(1, 57):
        lesson_file = f"lesson-{lesson_num:03d}.md"
        temp_file = temp_dir / lesson_file
        
        if not temp_file.exists():
            continue
            
        target_section = CORRECT_MAPPING.get(lesson_num)
        if not target_section:
            error = f"No mapping defined for lesson {lesson_num}"
            print(f"  ❌ {error}")
            errors.append(error)
            continue
            
        # Ensure target section directory exists
        target_dir = base_path / target_section
        target_dir.mkdir(exist_ok=True)
        
        target_file = target_dir / lesson_file
        shutil.move(str(temp_file), str(target_file))
        
        move_info = f"lesson-{lesson_num:03d}.md → {target_section}/"
        print(f"  ✅ {move_info}")
        moves_made.append(move_info)
    
    # Clean up temp directory
    try:
        temp_dir.rmdir()
        print(f"\nCleaned up temporary directory")
    except OSError:
        print(f"\nWarning: Could not remove temp directory (may contain remaining files)")
    
    # Summary
    print(f"\nReorganization Summary:")
    print(f"=" * 40)
    print(f"✅ Successfully moved: {len(moves_made)} lessons")
    print(f"❌ Errors: {len(errors)}")
    
    if errors:
        print(f"\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    # Generate final section counts
    print(f"\nFinal lesson distribution by section:")
    print(f"-" * 45)
    
    section_counts = {}
    for section_name in set(CORRECT_MAPPING.values()):
        section_dir = base_path / section_name
        if section_dir.exists():
            lesson_files = list(section_dir.glob("lesson-*.md"))
            section_counts[section_name] = len(lesson_files)
            print(f"📁 {section_name:20} {len(lesson_files):2} lessons")
    
    total_lessons = sum(section_counts.values())
    print(f"\n📊 Total lessons: {total_lessons}/56")
    
    return len(moves_made), errors

if __name__ == "__main__":
    moves_made, errors = reorganize_lessons()
    
    if len(errors) == 0:
        print(f"\n🎉 Reorganization completed successfully!")
        print(f"   All 56 Module 1 lessons are now in their correct sections.")
    else:
        print(f"\n⚠️  Reorganization completed with {len(errors)} errors.")
        print(f"   Please review and fix the errors listed above.")
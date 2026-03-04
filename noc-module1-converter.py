#!/usr/bin/env python3
"""
NOC Mastery Course Module 1 to Telephony Mastery Site Converter
Converts lesson-001.md through lesson-056.md to the new format
"""

import os
import re
import json
from pathlib import Path

# Define the mapping of lessons to sections and subdirectories
LESSON_MAPPING = {
    # Section 1.1: The PSTN (lessons 1-4) - pstn
    1: {"section": "pstn", "section_name": "The PSTN"},
    2: {"section": "pstn", "section_name": "The PSTN"},
    3: {"section": "pstn", "section_name": "The PSTN"},
    4: {"section": "pstn", "section_name": "The PSTN"},
    
    # Section 1.2: Digital Voice (lessons 5-9) - digital-voice
    5: {"section": "digital-voice", "section_name": "Digital Voice"},
    6: {"section": "digital-voice", "section_name": "Digital Voice"},
    7: {"section": "digital-voice", "section_name": "Digital Voice"},
    8: {"section": "digital-voice", "section_name": "Digital Voice"},
    9: {"section": "digital-voice", "section_name": "Digital Voice"},
    
    # Section 1.3: Packet vs Circuit Switching (lessons 10-11) - packet-switching
    10: {"section": "packet-switching", "section_name": "Packet Switching vs Circuit Switching"},
    11: {"section": "packet-switching", "section_name": "Packet Switching vs Circuit Switching"},
    
    # Section 1.4: Protocol Stack (lessons 12-18) - protocol-stack
    12: {"section": "protocol-stack", "section_name": "The Internet Protocol Stack"},
    13: {"section": "protocol-stack", "section_name": "The Internet Protocol Stack"},
    14: {"section": "protocol-stack", "section_name": "The Internet Protocol Stack"},
    15: {"section": "protocol-stack", "section_name": "The Internet Protocol Stack"},
    16: {"section": "protocol-stack", "section_name": "The Internet Protocol Stack"},
    17: {"section": "protocol-stack", "section_name": "The Internet Protocol Stack"},
    18: {"section": "protocol-stack", "section_name": "The Internet Protocol Stack"},
    
    # Section 1.5: DNS (lessons 19-21) - dns
    19: {"section": "dns", "section_name": "DNS Deep Dive"},
    20: {"section": "dns", "section_name": "DNS Deep Dive"},
    21: {"section": "dns", "section_name": "DNS Deep Dive"},
    
    # Section 1.6: BGP (lessons 22-25) - bgp
    22: {"section": "bgp", "section_name": "BGP: How the Internet Routes"},
    23: {"section": "bgp", "section_name": "BGP: How the Internet Routes"},
    24: {"section": "bgp", "section_name": "BGP: How the Internet Routes"},
    25: {"section": "bgp", "section_name": "BGP: How the Internet Routes"},
    
    # Section 1.7: NAT (lessons 26-28) - nat
    26: {"section": "nat", "section_name": "NAT and Its Impact on Real-Time Communications"},
    27: {"section": "nat", "section_name": "NAT and Its Impact on Real-Time Communications"},
    28: {"section": "nat", "section_name": "NAT and Its Impact on Real-Time Communications"},
    
    # Section 1.8: RTP/RTCP (lessons 29-31) - rtp-rtcp
    29: {"section": "rtp-rtcp", "section_name": "RTP and RTCP: Voice/Video over IP"},
    30: {"section": "rtp-rtcp", "section_name": "RTP and RTCP: Voice/Video over IP"},
    31: {"section": "rtp-rtcp", "section_name": "RTP and RTCP: Voice/Video over IP"},
    
    # Section 1.9: Quality (lessons 32-36) - quality
    32: {"section": "quality", "section_name": "Jitter, Latency, and Call Quality"},
    33: {"section": "quality", "section_name": "Jitter, Latency, and Call Quality"},
    34: {"section": "quality", "section_name": "Jitter, Latency, and Call Quality"},
    35: {"section": "quality", "section_name": "Jitter, Latency, and Call Quality"},
    36: {"section": "quality", "section_name": "Jitter, Latency, and Call Quality"},
    
    # Section 1.10: SIP Protocol (lessons 37-43) - sip-protocol
    37: {"section": "sip-protocol", "section_name": "SIP Protocol Deep Dive"},
    38: {"section": "sip-protocol", "section_name": "SIP Protocol Deep Dive"},
    39: {"section": "sip-protocol", "section_name": "SIP Protocol Deep Dive"},
    40: {"section": "sip-protocol", "section_name": "SIP Protocol Deep Dive"},
    41: {"section": "sip-protocol", "section_name": "SIP Protocol Deep Dive"},
    42: {"section": "sip-protocol", "section_name": "SIP Protocol Deep Dive"},
    43: {"section": "sip-protocol", "section_name": "SIP Protocol Deep Dive"},
    
    # Section 1.11: SIP Call Flows (lessons 44-47) - sip-call-flows
    44: {"section": "sip-call-flows", "section_name": "SIP Call Flows"},
    45: {"section": "sip-call-flows", "section_name": "SIP Call Flows"},
    46: {"section": "sip-call-flows", "section_name": "SIP Call Flows"},
    47: {"section": "sip-call-flows", "section_name": "SIP Call Flows"},
    
    # Section 1.12: SDP (lessons 48-49) - sdp
    48: {"section": "sdp", "section_name": "SDP and Media Negotiation"},
    49: {"section": "sdp", "section_name": "SDP and Media Negotiation"},
    
    # Section 1.13: Troubleshooting (lessons 50-51) - troubleshooting
    50: {"section": "troubleshooting", "section_name": "Packet Loss, Jitter, and Troubleshooting"},
    51: {"section": "troubleshooting", "section_name": "Packet Loss, Jitter, and Troubleshooting"},
    
    # Section 1.14: Security (lessons 52-53) - security
    52: {"section": "security", "section_name": "TLS and SRTP: Securing Communications"},
    53: {"section": "security", "section_name": "TLS and SRTP: Securing Communications"},
    
    # Section 1.15: WebRTC (lessons 54-56) - webrtc
    54: {"section": "webrtc", "section_name": "WebRTC"},
    55: {"section": "webrtc", "section_name": "WebRTC"},
    56: {"section": "webrtc", "section_name": "WebRTC"},
}

def extract_duration_minutes(duration_text):
    """Extract duration in minutes from '~X min read' format"""
    if not duration_text:
        return "5 minutes"
    
    # Look for patterns like "~7 min read", "8 minutes", "10-15 min", etc.
    match = re.search(r'(\d+)(?:-\d+)?\s*min', duration_text, re.IGNORECASE)
    if match:
        return f"{match.group(1)} minutes"
    return "5 minutes"

def determine_difficulty(lesson_num, content):
    """Determine difficulty based on lesson number and content complexity"""
    # Basic mapping based on progression through the course
    if lesson_num <= 10:
        return "Beginner"
    elif lesson_num <= 30:
        return "Intermediate"
    else:
        return "Advanced"
    
    # Could add content-based analysis here if needed
    # if "advanced" in content.lower() or "complex" in content.lower():
    #     return "Advanced"

def extract_objectives_from_content(content):
    """Extract learning objectives from the content"""
    objectives = []
    
    # Look for "Key Concepts" section
    key_concepts_match = re.search(r'\*\*Key Concepts:\*\*(.*?)(?=\n\*\*|\n##|\nz[^a-z]|$)', content, re.DOTALL)
    if key_concepts_match:
        concepts_text = key_concepts_match.group(1)
        # Extract numbered list items
        for match in re.finditer(r'(\d+)\.\s*([^\n]+)', concepts_text):
            objectives.append(match.group(2).strip())
    
    # Fallback: extract from Key Takeaways
    if not objectives:
        takeaways_match = re.search(r'\*\*Key Takeaways:\*\*(.*?)(?=\n\*\*|\n##|$)', content, re.DOTALL)
        if takeaways_match:
            takeaways_text = takeaways_match.group(1)
            for match in re.finditer(r'(\d+)\.\s*([^\n]+)', takeaways_text):
                objective = match.group(2).strip()
                # Clean up and make it an objective
                if objective.endswith('—'):
                    objective = objective[:-1].strip()
                objectives.append(f"Understand {objective}")
    
    return objectives[:5]  # Limit to 5 objectives

def extract_title_and_meta(content):
    """Extract title and metadata from lesson content"""
    lines = content.split('\n')
    
    title = ""
    module_section = ""
    duration = "5 minutes"
    prerequisites = []
    
    # Extract title (first # line)
    for line in lines[:10]:
        if line.startswith('# '):
            title = line[2:].strip()
            # Remove "Lesson X:" prefix
            title = re.sub(r'^Lesson \d+:\s*', '', title)
            break
    
    # Extract metadata from the header lines
    for line in lines[:15]:
        if "Module 1" in line and "Section" in line:
            module_section = line
        elif "~" in line and "min read" in line:
            duration = extract_duration_minutes(line)
        elif "Prerequisites:" in line:
            prereq_text = line.split("Prerequisites:")[-1].strip()
            if prereq_text and prereq_text != "None":
                # Parse prerequisites (could be "Lesson 1", "Lessons 6, 7, 8", etc.)
                prereq_matches = re.findall(r'Lesson (\d+)', prereq_text)
                prerequisites = [f"lesson-{num.zfill(3)}" for num in prereq_matches]
    
    return title, module_section, duration, prerequisites

def clean_content(content):
    """Clean and transform content for new format"""
    lines = content.split('\n')
    cleaned_lines = []
    in_header = True
    
    for i, line in enumerate(lines):
        # Skip the header section (until first real content)
        if in_header:
            if line.startswith('# ') and i == 0:
                continue  # Skip title, will be in frontmatter
            elif line.startswith('**Module 1'):
                continue  # Skip module/section line
            elif '⏱' in line or 'min read' in line:
                continue  # Skip duration line
            elif line.strip() == '---':
                continue  # Skip separator
            elif line.strip() == '' and len(cleaned_lines) == 0:
                continue  # Skip leading empty lines
            else:
                in_header = False
        
        if not in_header:
            # Convert NOC Tip callouts
            if line.startswith('🔧 **NOC Tip:**'):
                cleaned_lines.append('> **💡 NOC Tip:** ' + line[17:])
            # Convert other emoji callouts
            elif re.match(r'^[🔧⚠️💡📝🚨]\s*\*\*', line):
                cleaned_lines.append('> ' + line)
            else:
                cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def convert_lesson(source_path, target_dir, lesson_num):
    """Convert a single lesson file"""
    print(f"Converting lesson {lesson_num:03d}...")
    
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metadata
    title, module_section, duration, prerequisites = extract_title_and_meta(content)
    objectives = extract_objectives_from_content(content)
    difficulty = determine_difficulty(lesson_num, content)
    
    # Get section info
    section_info = LESSON_MAPPING.get(lesson_num, {"section": "misc", "section_name": "Module 1"})
    
    # Create frontmatter
    frontmatter_data = {
        'title': title,
        'description': f"Learn about {title.lower()}",
        'module': "Module 1: Foundations",
        'lesson': lesson_num,
        'difficulty': difficulty,
        'duration': duration,
        'objectives': objectives if objectives else [f"Understand {title.lower()}"]
    }
    
    # Format frontmatter as YAML
    frontmatter = "---\n"
    for key, value in frontmatter_data.items():
        if isinstance(value, list):
            frontmatter += f"{key}:\n"
            for item in value:
                frontmatter += f"  - {item}\n"
        else:
            frontmatter += f'{key}: "{value}"\n'
    frontmatter += "---\n\n"
    
    # Clean content
    cleaned_content = clean_content(content)
    
    # Combine frontmatter and content
    final_content = frontmatter + cleaned_content
    
    # Write to target location
    section_dir = target_dir / section_info['section']
    section_dir.mkdir(exist_ok=True)
    target_file = section_dir / f"lesson-{lesson_num:03d}.md"
    
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    return {
        'lesson_num': lesson_num,
        'title': title,
        'section': section_info['section'],
        'section_name': section_info['section_name'],
        'target_file': str(target_file),
        'objectives_count': len(objectives)
    }

def main():
    # Paths
    source_dir = Path.home() / 'Desktop/telephony-mastery/noc-mastery-course-v2-main/lessons'
    target_dir = Path.home() / 'Desktop/telephony-mastery/telephony-mastery-site/content/module-1-foundations'
    
    print("NOC Mastery Course Module 1 Converter")
    print("=" * 50)
    
    conversion_report = []
    errors = []
    
    # Process lessons 1-56
    for lesson_num in range(1, 57):
        lesson_file = source_dir / f"lesson-{lesson_num:03d}.md"
        
        if not lesson_file.exists():
            error = f"Source file not found: {lesson_file}"
            print(f"❌ {error}")
            errors.append(error)
            continue
        
        try:
            result = convert_lesson(lesson_file, target_dir, lesson_num)
            conversion_report.append(result)
            print(f"✅ Lesson {lesson_num:03d}: {result['title']}")
        except Exception as e:
            error = f"Error converting lesson {lesson_num:03d}: {str(e)}"
            print(f"❌ {error}")
            errors.append(error)
    
    # Generate summary report
    print(f"\nConversion Summary:")
    print(f"=" * 50)
    print(f"✅ Successfully converted: {len(conversion_report)} lessons")
    print(f"❌ Errors: {len(errors)}")
    
    if errors:
        print(f"\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    # Generate detailed report by section
    print(f"\nLessons by Section:")
    print(f"-" * 30)
    
    section_counts = {}
    for result in conversion_report:
        section = result['section']
        if section not in section_counts:
            section_counts[section] = []
        section_counts[section].append(result)
    
    for section, lessons in sorted(section_counts.items()):
        print(f"\n📁 {section}/ ({len(lessons)} lessons):")
        for lesson in lessons:
            print(f"  - lesson-{lesson['lesson_num']:03d}.md: {lesson['title']}")
    
    # Save detailed report as JSON
    report_file = target_dir.parent / 'module-1-conversion-report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'conversion_summary': {
                'total_lessons': len(conversion_report),
                'successful': len(conversion_report),
                'errors': len(errors),
                'error_details': errors
            },
            'lessons': conversion_report,
            'sections': {section: len(lessons) for section, lessons in section_counts.items()}
        }, f, indent=2)
    
    print(f"\n📊 Detailed report saved to: {report_file}")
    print(f"\nConversion complete! Module 1 lessons are ready in:")
    print(f"  {target_dir}")

if __name__ == "__main__":
    main()
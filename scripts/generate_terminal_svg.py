#!/usr/bin/env python3
"""
Terminal SVG Animation Generator

Generates an animated SVG simulating a terminal session with typing effects.
Customizable for profile READMEs.
Regenerate with -- python3 scripts/generate_terminal_svg.py  
Author: hitesh.o.agrawal@gmail.com
"""
import calendar
import datetime
import html
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Configuration for the terminal appearance
THEME = {
    "width": 800,
    "height": 650,  # Increased to fit all content comfortably -- hitesh
    "font_size": 14,
    "line_height": 22,
    "char_width": 8.5,  # Approx for monospace font
    "padding": 20,
    "header_height": 34,
    "colors": {
        "bg": "#282a36",        # Dracula Background
        "header": "#21222c",    # Darker header
        "text": "#f8f8f2",      # Foreground
        "cmd": "#50fa7b",       # Green for commands
        "path": "#bd93f9",      # Purple for paths
        "comment": "#6272a4",   # Grey/Blue for comments
        "cursor": "#f8f8f2",    # Cursor color
    }
}

@dataclass
class TerminalLine:
    """Represents a single line of text in the terminal."""
    content: str
    is_command: bool
    y_pos: int
    start_delay: float
    duration: float

class TerminalSVGGenerator:
    """Handles the creation of the animated SVG."""

    def __init__(self, output_path: str = "assets/terminal.svg"):
        self.output_path = output_path
        self.config = THEME
        self.current_y = self.config["header_height"] + self.config["padding"]
        self.current_delay = 0.5  # Initial delay
        self.css_defs = []
        self.body_elements = []

    def _get_uptime(self) -> str:
        """Calculates formatted uptime from a fixed DOB."""        
        dob = datetime.datetime.strptime("03-12-1981", "%d-%m-%Y")
        now = datetime.datetime.now()
        
        years = now.year - dob.year
        months = now.month - dob.month
        days = now.day - dob.day
        
        if days < 0:
            months -= 1
            # Get days in previous month
            # valid range for month is 1-12
            prev_month = (now.month - 2) % 12 + 1
            prev_month_year = now.year if now.month > 1 else now.year - 1
            _, days_in_prev = calendar.monthrange(prev_month_year, prev_month)
            days += days_in_prev
            
        if months < 0:
            years -= 1
            months += 12
            
        y_label = "year" if years == 1 else "years"
        m_label = "month" if months == 1 else "months"
        d_label = "day" if days == 1 else "days"
            
        return f"{years} {y_label}, {months} {m_label}, {days} {d_label}"

    def _generate_header(self) -> str:
        """Creates the window decoration and header bar."""
        c = self.config["colors"]
        w, h = self.config["width"], self.config["height"]
        hh = self.config["header_height"]
        
        return f'''
    <!-- Window Background -->
    <rect width="{w}" height="{h}" rx="10" ry="10" fill="{c["bg"]}"/>
    
    <!-- Title Bar -->
    <path d="M0 10 C0 4.5 4.5 0 10 0 L{w-10} 0 C{w-4.5} 0 {w} 4.5 {w} 10 L{w} {hh} L0 {hh} Z" fill="{c["header"]}"/>
    
    <!-- Window Controls -->
    <circle cx="20" cy="17" r="6" fill="#ff5555"/>
    <circle cx="40" cy="17" r="6" fill="#f1fa8c"/>
    <circle cx="60" cy="17" r="6" fill="#50fa7b"/>
    
    <!-- Title -->
    <text x="{w/2}" y="21" text-anchor="middle" fill="{c["comment"]}" 
        font-family="-apple-system, BlinkMacSystemFont, sans-serif" font-size="13" font-weight="500">
        hitesh@mylinuxhome: ~
    </text>
'''

    def _add_command(self, cmd_text: str):
        """Adds a command line with typing animation."""
        line_id = f"cmd_{int(self.current_y)}"
        c = self.config["colors"]
        char_w = self.config["char_width"]
        
        escaped_text = html.escape(cmd_text)
        
        # Typing duration based on length
        duration = len(cmd_text) * 0.05
        width_px = len(cmd_text) * char_w
        
        # Keyframe animation for typing effect
        self.css_defs.append(f'''
        #{line_id} {{
            overflow: hidden; 
            border-right: 2px solid transparent;            
            width: 0;
            opacity: 0;
            animation: 
                type_{line_id} {duration}s steps({len(cmd_text)}, end) forwards,
                cursor_{line_id} {duration}s step-end forwards;
            animation-delay: {self.current_delay}s;
        }}
        @keyframes type_{line_id} {{
            0% {{ width: 0; opacity: 1; border-right-color: {c["cursor"]}; }}
            99% {{ border-right-color: {c["cursor"]}; }}
            100% {{ width: {width_px}px; opacity: 1; border-right-color: transparent; }}
        }}
        ''')

        # SVG Elements
        prompt = f'<tspan fill="{c["path"]}">~</tspan> <tspan fill="{c["cmd"]}">❯</tspan> '
        self.body_elements.append(
            f'<text x="{self.config["padding"]}" y="{self.current_y}" class="code">'
            f'{prompt}<tspan id="{line_id}" fill="{c["text"]}">{escaped_text}</tspan>'
            f'</text>'
        )

        self.current_y += self.config["line_height"]
        self.current_delay += duration + 0.4  # Small pause after typing

    def _add_output(self, output_text: str):
        """Adds command output lines with a simple fade-in."""
        lines = output_text.split('\n')
        c = self.config["colors"]
        
        for line in lines:
            line_id = f"out_{int(self.current_y)}"
            escaped_line = html.escape(line)
            
            self.css_defs.append(f'''
            #{line_id} {{
                opacity: 0;
                animation: fade_in 0.1s ease forwards;
                animation-delay: {self.current_delay}s;
            }}
            ''')
            
            self.body_elements.append(
                f'<text x="{self.config["padding"]}" y="{self.current_y}" id="{line_id}" '
                f'class="code" fill="{c["text"]}">{escaped_line}</text>'
            )
            
            self.current_y += self.config["line_height"]
            self.current_delay += 0.05  # Very fast output

        self.current_delay += 0.2  # Pause before next prompt

    def build(self):
        """Assembles the final SVG."""
        commands = [
            ("whoami", "hitesh_agrawal"),
            ("uptime", self._get_uptime()),
            ("whereis /home/hitesh", "/home/hitesh: Ahmedabad, India"),
            ("pwd", "~/GSR_Markets"),
            ("cat /etc/skills.conf", 
"""# Core Strengths
• Low-latency & deterministic systems
• Multi-region HA & disaster recovery
• Kubernetes at scale (production)
• Observability-first & SLO-driven
• Unix/Linux internals & performance"""),
            ("history | grep -A 5 'experience'", 
"""2018-Now: Senior SRE (VP) @ GSR Markets
2016-18 : VP - Athena Core @ JP Morgan
2014-16 : Sr. Systems Eng @ CME Group
2013-14 : Cloud Systems Analyst @ Autodesk
2008-13 : Principal Eng / Manager @ Yahoo!"""),
            ("finger hitesh",
"""Email: hitesha1981@gmail.com,hitesh.o.agrawal@gmail.com
telegram: @hitesh_agrawal
LinkedIn: https://www.linkedin.com/in/agrawalhitesh/"""),
            ("date", datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y")),
        ]

        # Generate content
        for cmd, output in commands:
            self._add_command(cmd)
            self._add_output(output)

        # Active cursor at the end
        c = self.config["colors"]
        prompt = f'<tspan fill="{c["path"]}">~</tspan> <tspan fill="{c["cmd"]}">❯</tspan> '
        self.body_elements.append(
            f'<text x="{self.config["padding"]}" y="{self.current_y}" class="code">'
            f'{prompt}<tspan fill="{c["text"]}" class="cursor">_</tspan>'
            f'</text>'
        )

        # Common CSS
        common_css = f'''
        .code {{ font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace; font-size: {self.config["font_size"]}px; white-space: pre; }}
        .cursor {{ animation: blink 1s step-end infinite; }}
        @keyframes blink {{ 50% {{ opacity: 0; }} }}
        @keyframes fade_in {{ to {{ opacity: 1; }} }}
        '''

        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.config["width"]}" height="{self.config["height"]}" viewBox="0 0 {self.config["width"]} {self.config["height"]}">
    <style>
        {common_css}
        {''.join(self.css_defs)}
    </style>
    {self._generate_header()}
    <g transform="translate(0, 0)">
        {''.join(self.body_elements)}
    </g>
</svg>'''

        with open(self.output_path, "w") as f:
            f.write(svg_content)
        print(f"✓ Generated {self.output_path}")

if __name__ == "__main__":
    generator = TerminalSVGGenerator()
    generator.build()

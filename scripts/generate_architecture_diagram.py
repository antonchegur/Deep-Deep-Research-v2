#!/usr/bin/env python3
"""
Generate a basic architecture diagram for Deep Deep Research v2
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Create directory if it doesn't exist
os.makedirs('docs/assets', exist_ok=True)

# Set up figure
fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Set colors
colors = {
    'input': '#5DA5DA',      # blue
    'acquisition': '#FAA43A', # orange
    'processing': '#60BD68',  # green
    'analysis': '#F17CB0',    # pink
    'output': '#B2912F',      # brown
    'connector': '#DECF3F',   # yellow
    'arrows': '#4D4D4D'       # dark gray
}

# Draw the main components
components = [
    ('Input Processing', (1, 8, 2, 1), colors['input']),
    ('Data Acquisition', (1, 6, 2, 1), colors['acquisition']),
    ('Data Processing', (4, 6, 2, 1), colors['processing']),
    ('Analysis & Synthesis', (4, 4, 2, 1), colors['analysis']),
    ('Output Generation', (4, 2, 2, 1), colors['output']),
    ('External Services', (7, 6, 2, 1), colors['connector']),
]

for name, (x, y, width, height), color in components:
    rect = patches.Rectangle((x, y), width, height, facecolor=color, alpha=0.8)
    ax.add_patch(rect)
    ax.text(x + width/2, y + height/2, name, 
            ha='center', va='center', fontsize=10, fontweight='bold')

# Draw arrows for data flow
arrows = [
    ((2, 7.5), (4, 6.5)),    # Input to Processing
    ((3, 6.5), (4, 6.5)),    # Acquisition to Processing
    ((5, 5.5), (5, 5)),      # Processing to Analysis
    ((5, 3.5), (5, 3)),      # Analysis to Output
    ((6, 6.5), (7, 6.5)),    # Processing to External
    ((7, 6), (6, 5.5)),      # External to Analysis
]

for (x1, y1), (x2, y2) in arrows:
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=colors['arrows'], lw=1.5))

# Add labels for specific modules
modules = [
    ('CLI', (0.5, 8.8)),
    ('Wikipedia', (0.5, 5.5)),
    ('DuckDuckGo', (0.5, 5.2)),
    ('arXiv', (0.5, 4.9)),
    ('Chunking Engine', (3.5, 5.5)),
    ('Data Cleaner', (3.5, 5.2)),
    ('GPT-4 Interface', (3.5, 3.5)),
    ('Content Organizer', (3.5, 3.2)), 
    ('PDF Generator', (3.5, 1.5)),
    ('Data Visualizer', (3.5, 1.2)),
    ('OpenAI API', (7.5, 5.5)),
]

for name, (x, y) in modules:
    ax.text(x, y, name, fontsize=8, ha='left')

# Add title
plt.suptitle('Deep Deep Research v2 - System Architecture', fontsize=14, fontweight='bold')

# Add flow direction legend
plt.figtext(0.5, 0.05, 'Data Flow ↓', ha='center', fontweight='bold')

# Save the diagram
plt.savefig('docs/assets/architecture_diagram.png', dpi=200, bbox_inches='tight')
print("Architecture diagram saved to docs/assets/architecture_diagram.png") 
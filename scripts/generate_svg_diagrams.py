#!/usr/bin/env python3
"""
Generate SVG diagrams for H_1 and H_2 graphs.
"""
import math
from generate_h_graphs import generate_hk

def generate_h1_full_svg():
    """Generate complete H_1 graph with all edges visible."""
    n, m, edges, vertex_types, guards, pairs, witnesses, all_witnesses = generate_hk(1)
    
    # Layout: circular for small graph
    # Positions: guards at top, pairs in middle, witnesses at bottom
    width = 600
    height = 500
    
    positions = {}
    
    # Guard g1 at top center
    positions[1] = (300, 80)
    
    # Pairs a1, b1 below guard
    positions[2] = (220, 200)  # a1
    positions[3] = (380, 200)  # b1
    
    # Witnesses: a1's witnesses on left, b1's on right
    # a1's witnesses: 4,5,6,7
    a1_witnesses = [4, 5, 6, 7]
    for i, w in enumerate(a1_witnesses):
        x = 120 + i * 50
        y = 350
        positions[w] = (x, y)
    
    # b1's witnesses: 8,9,10,11
    b1_witnesses = [8, 9, 10, 11]
    for i, w in enumerate(b1_witnesses):
        x = 330 + i * 50
        y = 350
        positions[w] = (x, y)
    
    # Generate SVG
    svg_lines = []
    svg_lines.append(f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    
    # Draw edges first
    for u, v in edges:
        x1, y1 = positions[u]
        x2, y2 = positions[v]
        svg_lines.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--muted)" stroke-width="1.5" opacity="0.4" />')
    
    # Draw vertices
    for v_id in range(1, n+1):
        x, y = positions[v_id]
        v_type, v_label = vertex_types[v_id]
        
        if v_type == 'guard':
            fill = 'var(--guard-soft)'
            stroke = 'var(--guard)'
            radius = 18
        elif v_type == 'pair':
            fill = 'var(--pair-soft)'
            stroke = 'var(--pair)'
            radius = 18
        else:  # witness
            fill = 'var(--wit-soft)'
            stroke = 'var(--wit)'
            radius = 12
        
        svg_lines.append(f'  <circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2.5" />')
        svg_lines.append(f'  <text x="{x}" y="{y+5}" font-size="13" font-weight="700" text-anchor="middle" fill="var(--ink)">{v_label}</text>')
    
    # Add statistics
    svg_lines.append(f'  <text x="{width//2}" y="30" font-size="16" font-weight="700" text-anchor="middle" fill="var(--ink)">H₁ 完全図（n=11, m=17, k=1）</text>')
    svg_lines.append(f'  <text x="{width//2}" y="480" font-size="14" text-anchor="middle" fill="var(--muted)">すべての辺を表示（17本）</text>')
    
    svg_lines.append('</svg>')
    
    return '\n'.join(svg_lines)

def generate_h2_structure_svg():
    """Generate H_2 structure diagram showing non-edges."""
    n, m, edges, vertex_types, guards, pairs, witnesses, all_witnesses = generate_hk(2)
    
    width = 800
    height = 600
    
    positions = {}
    
    # Guards at top
    positions[1] = (300, 80)  # g1
    positions[2] = (500, 80)  # g2
    
    # Pairs in middle (form a square)
    positions[3] = (250, 200)  # a1
    positions[4] = (350, 200)  # b1
    positions[5] = (450, 200)  # a2
    positions[6] = (550, 200)  # b2
    
    # Witnesses below
    # a1's 5 witnesses: 7-11
    for i in range(5):
        positions[7+i] = (150 + i*40, 350)
    
    # b1's 5 witnesses: 12-16
    for i in range(5):
        positions[12+i] = (280 + i*40, 400)
    
    # a2's 5 witnesses: 17-21
    for i in range(5):
        positions[17+i] = (420 + i*40, 400)
    
    # b2's 5 witnesses: 22-26
    for i in range(5):
        positions[22+i] = (550 + i*40, 350)
    
    # Generate non-edges list
    non_edges = set()
    
    # Guard-guard
    non_edges.add((1, 2))
    
    # g_i with a_i, b_i
    non_edges.add((1, 3))
    non_edges.add((1, 4))
    non_edges.add((2, 5))
    non_edges.add((2, 6))
    
    # Witnesses with their core
    for i in range(5):
        non_edges.add((3, 7+i))   # a1
        non_edges.add((4, 12+i))  # b1
        non_edges.add((5, 17+i))  # a2
        non_edges.add((6, 22+i))  # b2
    
    # Witness-witness (all pairs)
    for i, w1 in enumerate(range(7, 27)):
        for w2 in range(w1+1, 27):
            non_edges.add((w1, w2))
    
    # Generate SVG
    svg_lines = []
    svg_lines.append(f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    
    # Title
    svg_lines.append(f'  <text x="{width//2}" y="30" font-size="18" font-weight="700" text-anchor="middle" fill="var(--ink)">H₂ の構造（n=26, m=110, k=2）</text>')
    svg_lines.append(f'  <text x="{width//2}" y="50" font-size="14" text-anchor="middle" fill="var(--muted)">非エッジのみ破線で表示（完全グラフから 215 本削除）</text>')
    
    # Draw key edges (M clique)
    m_vertices = [3, 4, 5, 6]
    for i, u in enumerate(m_vertices):
        for v in m_vertices[i+1:]:
            x1, y1 = positions[u]
            x2, y2 = positions[v]
            svg_lines.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--pair)" stroke-width="2" opacity="0.6" />')
    
    # Draw non-edges as dashed lines (sample only, for clarity)
    # Only show important non-edges
    important_non_edges = [
        (1, 2),  # guard-guard
        (1, 3), (1, 4),  # g1 with its pair
        (2, 5), (2, 6),  # g2 with its pair
        (3, 7), (3, 8),  # a1 with some witnesses
        (4, 12), (4, 13),  # b1 with some witnesses
    ]
    
    for u, v in important_non_edges:
        if u in positions and v in positions:
            x1, y1 = positions[u]
            x2, y2 = positions[v]
            svg_lines.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--guard)" stroke-width="2" stroke-dasharray="5 3" opacity="0.5" />')
    
    # Draw vertices
    for v_id in range(1, n+1):
        x, y = positions[v_id]
        v_type, v_label = vertex_types[v_id]
        
        if v_type == 'guard':
            fill = 'var(--guard-soft)'
            stroke = 'var(--guard)'
            radius = 16
            font_size = 13
        elif v_type == 'pair':
            fill = 'var(--pair-soft)'
            stroke = 'var(--pair)'
            radius = 16
            font_size = 13
        else:  # witness
            fill = 'var(--wit-soft)'
            stroke = 'var(--wit)'
            radius = 8
            font_size = 10
        
        svg_lines.append(f'  <circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2" />')
        if v_type != 'witness' or v_id in [7, 12, 17, 22]:  # Label only first witness of each group
            svg_lines.append(f'  <text x="{x}" y="{y+4}" font-size="{font_size}" font-weight="700" text-anchor="middle" fill="var(--ink)">{v_label}</text>')
    
    # Add labels
    svg_lines.append(f'  <text x="150" y="320" font-size="13" font-weight="700" text-anchor="start" fill="var(--guard)">U (guards)</text>')
    svg_lines.append(f'  <text x="400" y="170" font-size="13" font-weight="700" text-anchor="middle" fill="var(--pair)">M (pair clique)</text>')
    svg_lines.append(f'  <text x="170" y="480" font-size="12" text-anchor="start" fill="var(--wit)">a₁の証人(5個)</text>')
    svg_lines.append(f'  <text x="300" y="530" font-size="12" text-anchor="start" fill="var(--wit)">b₁の証人(5個)</text>')
    svg_lines.append(f'  <text x="440" y="530" font-size="12" text-anchor="start" fill="var(--wit)">a₂の証人(5個)</text>')
    svg_lines.append(f'  <text x="570" y="480" font-size="12" text-anchor="start" fill="var(--wit)">b₂の証人(5個)</text>')
    
    # Legend
    svg_lines.append(f'  <g transform="translate(50, 540)">')
    svg_lines.append(f'    <line x1="0" y1="0" x2="30" y2="0" stroke="var(--pair)" stroke-width="2" />')
    svg_lines.append(f'    <text x="35" y="5" font-size="12" fill="var(--muted)">辺あり（M内）</text>')
    svg_lines.append(f'    <line x1="150" y1="0" x2="180" y2="0" stroke="var(--guard)" stroke-width="2" stroke-dasharray="5 3" />')
    svg_lines.append(f'    <text x="185" y="5" font-size="12" fill="var(--muted)">辺なし（主要なもののみ表示）</text>')
    svg_lines.append(f'  </g>')
    
    svg_lines.append('</svg>')
    
    return '\n'.join(svg_lines)

if __name__ == '__main__':
    # Generate H1 SVG
    h1_svg = generate_h1_full_svg()
    with open('/workspace/docs/hk-explained/h1_full.svg', 'w') as f:
        f.write(h1_svg)
    print("Generated h1_full.svg")
    
    # Generate H2 SVG
    h2_svg = generate_h2_structure_svg()
    with open('/workspace/docs/hk-explained/h2_structure.svg', 'w') as f:
        f.write(h2_svg)
    print("Generated h2_structure.svg")
    
    print("\nSVG files can be embedded directly in HTML or saved as separate files.")

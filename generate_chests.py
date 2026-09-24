"""Generate original illustrated case chests. No external cover images."""
from pathlib import Path
import json, re, colorsys, html
root=Path(__file__).parent
cases=json.loads(re.search(r'const cases=(\[.*?\]);',(root/'index.html').read_text()).group(1))
# Each motif is stamped onto a three-dimensional case, not displayed instead of a case.
motifs=[
'<path d="M0-31 20-12 10 8 0 26-10 8-20-12Z"/><path d="M0-31V26M-20-12H20"/>',
'<path d="M-26 15-17-21 0-5 17-21 26 15Z"/><circle r="6" cy="1"/>',
'<path d="M-28 9 0-27 28 9 0 28Z"/><path d="M-28 9H28M0-27V28"/>',
'<circle r="25"/><circle r="13"/><path d="M0-34V34M-34 0H34"/>',
'<path d="M0-31 8-9 31-9 13 6 21 27 0 14-21 27-13 6-31-9-8-9Z"/>',
'<path d="M-26-14 0-30 26-14V17L0 31-26 17Z"/><path d="M-26-14 0 2 26-14M0 2V31"/>',
'<path d="M0-30C-30 1-26 30 0 29 26 30 30 1 0-30Z"/><path d="M-12 14Q0-18 12 14"/>',
'<path d="M-31 0Q0-31 31 0 0 31-31 0Z"/><circle r="10"/>',
'<path d="M0-32 27-14V17L0 32-27 17V-14Z"/><path d="M-27-14H27M-27 17H27"/>',
'<path d="M0-32 22-9 18 6 30 20 0 32-30 20-18 6-22-9Z"/><path d="M-22-9H22"/>',
'<path d="M-28-24H28V-8H13V26H-13V-8H-28Z"/><path d="M-13 5H13"/>',
'<path d="M0-31 9-8 32-6 15 9 20 30 0 19-20 30-15 9-32-6-9-8Z"/><circle r="7"/>'
]
def rgb(h,s,v):return '#%02x%02x%02x'%tuple(round(x*255) for x in colorsys.hsv_to_rgb(h,s,v))
for i,c in enumerate(cases):
    hue=(i*.61803398875+.09)%1
    accent=rgb(hue,.52,.99); light=rgb(hue,.20,.98); mid=rgb(hue,.43,.56); dark=rgb(hue,.46,.19)
    # Variation across the chest's materials, hardware and secondary markings.
    material=['#4b3046','#324a5b','#58412f','#354538','#443955','#37414e'][i%6]
    trim=['#e7ba73','#d5dcf0','#c4a3f5','#badad2'][i%4]
    stud=''.join(f'<circle cx="{x}" cy="{y}" r="2.8" fill="{trim}"/>' for x in (77,100,298,320) for y in (155,205))
    ribs=''.join(f'<path d="M{x} 140v77l8 5v-82Z" fill="{mid}" opacity=".74" stroke="{trim}" stroke-width="1.5"/>' for x in (88,307))
    lidlines=''.join(f'<path d="M{x} 94l-19 44" stroke="{trim}" stroke-opacity=".55" stroke-width="4"/>' for x in (121,183,245,307))
    # Inset panel plus individual decoration; the silhouette always remains a recognizable case.
    motif=motifs[i%len(motifs)]
    extras=['<path d="M107 183h37m115 0h32"/>','<path d="M119 169l12 10-12 10m162-20-12 10 12 10"/>','<circle cx="121" cy="183" r="5"/><circle cx="279" cy="183" r="5"/>','<path d="M107 190l21-17 14 17m151 0-21-17-14 17"/>'][i%4]
    name=html.escape(c['name'],quote=True)
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 320" role="img" aria-label="Кейс {name}">
<defs>
 <radialGradient id="halo"><stop stop-color="{accent}" stop-opacity=".32"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>
 <linearGradient id="lid" x1="0" y1="0" x2=".85" y2="1"><stop stop-color="{light}"/><stop offset=".42" stop-color="{mid}"/><stop offset="1" stop-color="{dark}"/></linearGradient>
 <linearGradient id="face" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{material}"/><stop offset="1" stop-color="{dark}"/></linearGradient>
 <filter id="shadow"><feGaussianBlur stdDeviation="11"/></filter>
</defs>
<ellipse cx="200" cy="269" rx="135" ry="24" fill="#050610" opacity=".58" filter="url(#shadow)"/>
<ellipse cx="200" cy="155" rx="181" ry="143" fill="url(#halo)"/>
<!-- thick hinged lid: top, side and curved front lip -->
<path d="M53 113 122 70Q199 46 278 70l70 43-47 35H99Z" fill="url(#lid)" stroke="{trim}" stroke-width="4" stroke-linejoin="round"/>
<path d="M278 70q56 13 70 43v97l-45 38v-99Z" fill="{dark}" stroke="{trim}" stroke-width="4" stroke-linejoin="round"/>
<path d="M53 113q32-48 69-43l-23 77-46 18Z" fill="{mid}" stroke="{trim}" stroke-width="4" stroke-linejoin="round"/>
<path d="M99 142 199 118 301 142v95L200 268 99 237Z" fill="url(#face)" stroke="{trim}" stroke-width="5" stroke-linejoin="round"/>
<path d="M99 142q101-39 202 0v28q-102-29-202 0Z" fill="url(#lid)" stroke="{trim}" stroke-width="4"/>
<path d="M99 222 200 249l101-27v15L200 268 99 237Z" fill="{mid}" stroke="{trim}" stroke-width="3"/>
<path d="M117 167 200 149l83 18v52L200 244l-83-25Z" fill="{dark}" opacity=".8" stroke="{trim}" stroke-opacity=".65" stroke-width="2"/>
{lidlines}{ribs}{stud}
<!-- plate and thematic relief are physically fixed to the front of the chest -->
<path d="M151 159 200 145 249 159v68L200 244l-49-17Z" fill="{mid}" stroke="{trim}" stroke-width="4"/>
<path d="M160 166 200 155l40 11v55l-40 13-40-13Z" fill="{dark}" stroke="{accent}" stroke-width="2"/>
<g transform="translate(200 194) scale(.75 .86)" fill="none" stroke="{light}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">{motif}</g>
<g fill="none" stroke="{trim}" stroke-width="2" opacity=".9">{extras}</g>
<!-- clasp in front of the seam, hanging hardware, and reflective facets -->
<path d="M188 139h24v16l-12 6-12-6Z" fill="{trim}" stroke="{dark}" stroke-width="2"/>
<path d="M55 117q35-26 64-37m165 0q36 12 59 34" fill="none" stroke="white" stroke-width="3" opacity=".28"/>
<path d="M112 231 199 257 290 229" fill="none" stroke="white" stroke-width="2" opacity=".22"/>
</svg>'''
    (root/'assets'/f'case-{c["id"]}.svg').write_text(svg)
print('Created',len(cases),'original chest covers')

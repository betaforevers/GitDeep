with open("index.html", "r") as f:
    text = f.read()

import re
# We want to move <section class="results-section hidden" id="results-section">...</section>
# inside <section class="hero-section">...</section> just before the <a href="#about-section" class="scroll-indicator"...>

# 1. extract results section
results_match = re.search(r'(<section class="results-section hidden" id="results-section">.*?</section>\n)', text, re.DOTALL)
results_html = results_match.group(1)

# 2. remove results section from text
text = text.replace(results_html, "")

# 3. insert results section right before the scroll-indicator
indicator_idx = text.find('<a href="#about-section" class="scroll-indicator"')
text = text[:indicator_idx] + results_html + "            " + text[indicator_idx:]

with open("index.html", "w") as f:
    f.write(text)

print("Moved results section!")

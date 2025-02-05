---
name: Custom issue template
about: Checklist for map creation issues.
title: New Map - [Map Name]
labels: ''
assignees: ''

---

- [ ] Plan out how the map will be divided up and estimate the total region count.
- [ ] Create map projection in QGIS.
- [ ] Draw the regions.
    - [ ] Be sure to remove excess lines around map focus area.
    - [ ] Line width should be set to 4px.
- [ ] Create print template and export map from QGIS as SVG.
- [ ] Export map layer PNGs using Affinity Designer and Affinity Photo.
    - [ ] background.png (texture + lines)
    - [ ] main.png (lines + color)
    - [ ] text.png (region ids)
    - [ ] magnified.png (magnified boxes and arrows)
    - [ ] For the border layer, make sure to do a magic wand selection with 0% tolerance on the lines to remove anti-aliasing.
- [ ] Create map reference in Affinity Photo.
    - [ ] blank.png
    - [ ] reference.png
- [ ] Create map data files.
    - [ ] regdata.json
    - [ ] map_config.json
- [ ] Test to make sure new map is working with turn processor.

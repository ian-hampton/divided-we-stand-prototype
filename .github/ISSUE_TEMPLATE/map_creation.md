---
name: Map Creation Template
about: Checklist for map creation issues.
title: New Map - [Map Name]
labels: ''
assignees: ''

---

- [ ] Plan out how the map will be divided up and estimate the total region count.
- [ ] Create map projection in QGIS.
- [ ] Draw the regions.
    - [ ] Be sure to remove excess lines around map focus area.
    - [ ] Line width should be set to 2px.
- [ ] Create print template and export map from QGIS as SVG.
- [ ] Export map layer PNGs using Affinity Designer and Affinity Photo.
    - [ ] For the border layer, for best results do the following:
          - Convert border image to pixel layer.
          - Create curves adjustment layer, select alpha band and drag button in top right to top left.
          - Mask adjustment layer to border layer.
    - [ ] background.png (texture + borders)
    - [ ] main.png (borders + color)
    - [ ] text.png (region ids)
    - [ ] magnified.png (magnified boxes and arrows)    
- [ ] Create map reference in Affinity Photo.
    - [ ] blank.png
    - [ ] reference.png
- [ ] Create map data files.
    - [ ] regdata.json
    - [ ] map_config.json
- [ ] Test to make sure new map is working with turn processor.

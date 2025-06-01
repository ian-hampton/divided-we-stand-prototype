---
name: Map Creation Template
about: Checklist for map creation issues.
title: New Map - [Map Name]
labels: ["enhancement", "graphics"]
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
- [ ] Create map graph.
    - [ ] Generate graph.json using image-to-graph-dws script.
    - [ ] Run create_graph.py on graph.json.
    - [ ] Manually fill in the following region data:
        - [ ] fullName
        - [ ] isEdgeOfMap
        - [ ] hasRegionalCapital
        - [ ] isMagnified
        - [ ] randomStartAllowed
        - [ ] additionalRegionCoords
        - [ ] improvementCoords and unitCoords for magnified regions
        - [ ] adjacency data from sea routes (if applicable)
- [ ] Create map config file (config.json).
- [ ] Run map_test_complete.py to verify map generation is working.

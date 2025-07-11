## Tag Documentation

This document is a complete reference for all modifiers that can be attached to game tags and how to use them.

| Modifier Name                | Description                                                                              | Example                                                     |
|------------------------------|------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| Expire Turn                  | Tag expires on the specified turn.                                                       | new_tag["Expire Turn"] = 99999                              |
| Agenda Cost                  | Agenda research cost increased by specified value.                                       | new_tag["Agenda Cost"] = 5                                  |
| Alliance Bonus               | Tagged nation gains specified political power income for each alliance.                  | new_tag["Alliance Political Power Bonus"] = 0.25            |
| Alliance Limit               | Alliance limit increases by specified value.                                             | new_tag["Alliance Limit Modifier"] = 1                      |
| Cannot Declare War on X      | Tagged nation cannot declare war on the nation specified.                                | new_tag[f"Cannot Declare War On #{nation.id}"] = True       |
| Capital Adjacency Boost      | Improvements adjacent to any of the tagged nation's Capitals produce 100% more income.   | new_tag["Capital Boost"] = True                             |
| Combat Roll Bonus            | Tagged nation gains +1 to all combat rolls against a specific nation.                    | new_tag["Combat Roll Bonus"] = nation.id                    |
| Disalow Agenda Research      | Cannot research any agendas until tag expires.                                           | new_tag["No Agenda Research"] = True                        |
| Improvement Build Discount   | Decreases build cost by specified value (as a percentage). 100% = 1.0                    | new_tag["Build Discount"] = 0.2                             |
| Improvement Income           | Improvement income increases by given resource-amount pairs.                             | See below.                                                  |
| Improvement Income Multiplier| Improvement income increases by given resource-amount pairs (as a percentage). 100% = 1.0| See below.                                                  |
| Market Buy Price             | Buy price for all resources decreased by specified value (as a percentage). 100% = 1.0   | new_tag["Market Buy Modifier"] = 0.2                        |
| Market Sell Price            | Sell price for all resources increased by specified value (as a percentage). 100% = 1.0  | new_tag["Market Sell Modifier"] = 0.2                       |
| Region Claim Political Cost  | Claim action political power cost (usually 0) increased by specified value.              | new_tag["Region Claim Cost"] = 1                            |
| Research Category Bonus      | Awards an amount of any 1 resource for completing research in specified categories.      | See below.                                                  |
| Resource Rate                | Resource income increases by specified value (as a percentage). 100% = 100.              | new_tag[f"{action.resource_name} Rate"] = 20                |
| Trade Fee                    | Trade fee increases the number of steps indicated by value.                              | new_tag["Trade Fee Modifier"] = 1                           |

### Additional Examples

#### Improvement Income
```python
new_tag = {
    "Improvement Income": {
        "Boot Camp": {
            "Military Capacity": 1
        }
    },
    "Expire Turn": 99999
}
nation.tags["NEW TAG NAME"] = new_tag
```

#### Improvement Income Multiplier
```python
new_tag = {
    "Improvement Income Multiplier": {
        "Research Laboratory": {
            "Research": -0.2
        },
        "Research Institute": {
            "Research": -0.2
        }
    },
    "Expire Turn": 99999
}
nation.tags["NEW TAG NAME"] = new_tag
```

#### Research Category Bonus
```python
new_tag = {
    "Research Bonus": {
        "Amount": 2,
        "Resource": "Political Power",
        "Categories": ["Energy", "Infrastructure"]
    },
    "Expire Turn": 99999
}
nation.tags["NEW TAG NAME"] = new_tag
```
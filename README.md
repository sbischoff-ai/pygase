[![Build Status](https://dev.azure.com/pxlbrain/pygase/_apis/build/status/sbischoff-ai.python-game-service?branchName=master)](https://dev.azure.com/pxlbrain/pygase/_build/latest?definitionId=1&branchName=master)
![Azure DevOps tests (branch)](https://img.shields.io/azure-devops/tests/pxlbrain/pygase/1/master.svg)
![Azure DevOps coverage (branch)](https://img.shields.io/azure-devops/coverage/pxlbrain/pygase/1/master.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

![PyPI](https://img.shields.io/pypi/v/pygase.svg)
# PyGaSe
**Py**thon**Ga**me**Se**rver

A Python package that contains a versatile lightweight UDP-based client-server API and network protocol for 
real-time online games.

### Installation:
```
pip install pygase
```

## Example

[This example game implements](/chase/) an online game of chase, in which players can move around,
while one of them is the chaser who has to catch another player. A player who has been
catched becomes the next chaser and can catch other players after a 5s protection countdown.

For a complete API documentation look in [here](/docs/api/) (see GitHub if you're on PyPI.org).

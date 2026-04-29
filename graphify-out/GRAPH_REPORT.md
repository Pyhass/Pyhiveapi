# Graph Report - .  (2026-04-28)

## Corpus Check
- 67 files · ~115,776 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 689 nodes · 1578 edges · 44 communities detected
- Extraction: 58% EXTRACTED · 42% INFERRED · 0% AMBIGUOUS · INFERRED: 660 edges (avg confidence: 0.64)
- Token cost: 15,000 input · 4,500 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Device API Operations|Device API Operations]]
- [[_COMMUNITY_Hive Exception Types|Hive Exception Types]]
- [[_COMMUNITY_Session & Configuration|Session & Configuration]]
- [[_COMMUNITY_Test Coverage Reports|Test Coverage Reports]]
- [[_COMMUNITY_Action Device Module|Action Device Module]]
- [[_COMMUNITY_AWS Cognito SRP Auth|AWS Cognito SRP Auth]]
- [[_COMMUNITY_SRP Crypto Utilities|SRP Crypto Utilities]]
- [[_COMMUNITY_Architecture Overview|Architecture Overview]]
- [[_COMMUNITY_Sync API Client|Sync API Client]]
- [[_COMMUNITY_Async API Client|Async API Client]]
- [[_COMMUNITY_Smart Plug Module|Smart Plug Module]]
- [[_COMMUNITY_Heating Climate Module|Heating Climate Module]]
- [[_COMMUNITY_Smart Light Module|Smart Light Module]]
- [[_COMMUNITY_Project & CICD|Project & CI/CD]]
- [[_COMMUNITY_Debug Tracer|Debug Tracer]]
- [[_COMMUNITY_Coverage Report UI|Coverage Report UI]]
- [[_COMMUNITY_Device Key Translation|Device Key Translation]]
- [[_COMMUNITY_Test Mock Objects|Test Mock Objects]]
- [[_COMMUNITY_Package Build Setup|Package Build Setup]]
- [[_COMMUNITY_Async-Sync Code Generation|Async-Sync Code Generation]]
- [[_COMMUNITY_Time Utilities|Time Utilities]]
- [[_COMMUNITY_TRV Device Linking|TRV Device Linking]]
- [[_COMMUNITY_Docs & Graph Integration|Docs & Graph Integration]]
- [[_COMMUNITY_Package Init (src)|Package Init (src)]]
- [[_COMMUNITY_Auth Module File|Auth Module File]]
- [[_COMMUNITY_Heating Operation Modes|Heating Operation Modes]]
- [[_COMMUNITY_Heating Return Modes|Heating Return Modes]]
- [[_COMMUNITY_API Package Init|API Package Init]]
- [[_COMMUNITY_Requests HTTP Dependency|Requests HTTP Dependency]]
- [[_COMMUNITY_Loguru Logging Dependency|Loguru Logging Dependency]]
- [[_COMMUNITY_Pyquery HTML Dependency|Pyquery HTML Dependency]]
- [[_COMMUNITY_Pre-commit Linting|Pre-commit Linting]]
- [[_COMMUNITY_Pylint Static Analysis|Pylint Static Analysis]]
- [[_COMMUNITY_Tox Test Automation|Tox Test Automation]]
- [[_COMMUNITY_PBR Build Tool|PBR Build Tool]]
- [[_COMMUNITY_Code of Conduct|Code of Conduct]]
- [[_COMMUNITY_Map Dict Wrapper|Map Dict Wrapper]]
- [[_COMMUNITY_Security Policy|Security Policy]]
- [[_COMMUNITY_Coverage Functions Index|Coverage Functions Index]]
- [[_COMMUNITY_Coverage Classes Index|Coverage Classes Index]]
- [[_COMMUNITY_Coverage UI Asset|Coverage UI Asset]]
- [[_COMMUNITY_Coverage Favicon|Coverage Favicon]]
- [[_COMMUNITY_HTML Coverage Report|HTML Coverage Report]]
- [[_COMMUNITY_Coverage.py Tool|Coverage.py Tool]]

## God Nodes (most connected - your core abstractions)
1. `debug()` - 54 edges
2. `HiveHelper` - 38 edges
3. `HiveSession` - 37 edges
4. `HiveAttributes` - 34 edges
5. `Device` - 34 edges
6. `HiveApiError` - 30 edges
7. `HiveAuthError` - 30 edges
8. `Map` - 30 edges
9. `HiveRefreshTokenExpired` - 29 edges
10. `HiveReauthRequired` - 29 edges

## Surprising Connections (you probably didn't know these)
- `_pollDevices private poll extraction implementation plan` --conceptually_related_to--> `HiveSession session lifecycle class`  [INFERRED]
  docs/superpowers/plans/2026-04-25-scan-interval-and-camera-removal.md → CLAUDE.md
- `_SCAN_INTERVAL module-level constant 120 seconds` --conceptually_related_to--> `HiveSession session lifecycle class`  [INFERRED]
  docs/superpowers/specs/2026-04-25-scan-interval-and-camera-removal-design.md → CLAUDE.md
- `HiveSession` --uses--> `HiveAttributes`  [INFERRED]
  src/session.py → /Users/kholejones/Git/Home-Automation/Pyhiveapi/src/device_attributes.py
- `HiveSession` --uses--> `HiveApiError`  [INFERRED]
  src/session.py → /Users/kholejones/Git/Home-Automation/Pyhiveapi/src/helper/hive_exceptions.py
- `HiveSession` --uses--> `HiveAuthError`  [INFERRED]
  src/session.py → /Users/kholejones/Git/Home-Automation/Pyhiveapi/src/helper/hive_exceptions.py

## Hyperedges (group relationships)
- **CI to PyPI Release Pipeline** — workflows_readme_ci_yml, workflows_readme_dev_release_pr_yml, workflows_readme_release_on_master_yml, workflows_readme_python_publish_yml, workflows_readme_pypi_trusted_publishing [EXTRACTED 0.95]
- **Scan Interval and Camera Removal Refactor** — spec_scan_interval_design, spec_camera_removal_design, plan_scan_interval_goal, plan_camera_removal, plan_force_update, plan_poll_devices [EXTRACTED 0.92]
- **Async-first dual-package architecture via unasync** — readme_apyhiveapi, readme_pyhiveapi_sync, claude_md_unasync, claude_md_hiveasyncapi [EXTRACTED 0.90]

## Communities

### Community 0 - "Device API Operations"
Cohesion: 0.03
Nodes (73): Set action enabled/disabled state.          Args:             device (dict): Dev, Call the get devices endpoint., Set the state of a Device., An error has occurred interacting with the Hive API., get_secret_hash(), HiveAuthAsync, Initialise async variables., Process device challenge. (+65 more)

### Community 1 - "Hive Exception Types"
Cohesion: 0.16
Nodes (61): dict, Exception, HiveApiError, HiveAuthError, HiveFailedToRefreshTokens, HiveInvalid2FACode, HiveInvalidDeviceAuthentication, HiveInvalidPassword (+53 more)

### Community 2 - "Session & Configuration"
Cohesion: 0.04
Nodes (39): UnknownConfig, Constants for Pyhiveapi., Helper class for pyhiveapi., EntityConfig, Configuration for creating a device entity., HiveSession, Hive Device Attribute Module., exception_handler() (+31 more)

### Community 3 - "Test Coverage Reports"
Cohesion: 0.05
Nodes (61): apyhiveapi.action (17% coverage), Alarm class (9% class coverage), apyhiveapi.alarm (22% coverage), Camera class (9% class coverage), apyhiveapi.camera (19% coverage), Climate class (3% class coverage), apyhiveapi.helper.const (100% coverage), Coverage Report Index (+53 more)

### Community 4 - "Action Device Module"
Cohesion: 0.06
Nodes (24): HiveAction, Set action to turn off.          Args:             device (dict): Device to set, Hive Action Code.      Returns:         object: Return hive action object., Backwards-compatible alias for get_action., Backwards-compatible alias for set_status_on., Backwards-compatible alias for set_status_off., Initialise Action.          Args:             session (object, optional): sessio, Action device to update.          Args:             device (dict): Device to be (+16 more)

### Community 5 - "AWS Cognito SRP Auth"
Cohesion: 0.08
Nodes (30): calculate_u(), compute_hkdf(), get_random(), get_secret_hash(), hash_sha256(), hex_hash(), hex_to_long(), HiveAuth (+22 more)

### Community 6 - "SRP Crypto Utilities"
Cohesion: 0.11
Nodes (24): calculate_u(), compute_hkdf(), get_random(), hash_sha256(), hex_hash(), hex_to_long(), long_to_hex(), pad_hex() (+16 more)

### Community 7 - "Architecture Overview"
Cohesion: 0.08
Nodes (27): const.py HIVE_TYPES PRODUCTS DEVICES mappings, createDevices device discovery function, Device dataclass entity model, File-based testing using use@file.com fixture data, Hive public API class, Hive custom exceptions module, HiveApiAsync async HTTP client class, HiveAttributes HA state attribute computer (+19 more)

### Community 8 - "Sync API Client"
Cohesion: 0.14
Nodes (13): HiveApi, Get login properties to make the login request., Build and query all endpoint., Call the get devices endpoint., Call the get products endpoint., Hive API initialisation., Call the get actions endpoint., Call a way to get motion sensor info. (+5 more)

### Community 9 - "Async API Client"
Cohesion: 0.11
Nodes (13): HiveApiAsync, Get login properties to make the login request., Refresh tokens - DEPRECATED NOW BY AWS TOKEN MANAGEMENT., Build and query all endpoint., Call the get products endpoint., Call the get actions endpoint., Call a way to get motion sensor info., Call endpoint to get local weather from Hive API. (+5 more)

### Community 10 - "Smart Plug Module"
Cohesion: 0.11
Nodes (12): HiveSmartPlug, Home Assistant switch class.      Args:         SmartPlug (Class): Initialises t, Plug Device.      Returns:         object: Returns Plug object, Initialise switch.          Args:             session (object): This is the sess, Home Assistant wrapper to get updated switch state.          Args:             d, Home Assisatnt wrapper for turning switch on.          Args:             device, Home Assisatnt wrapper for turning switch off.          Args:             device, Backwards-compatible alias for turn_on. (+4 more)

### Community 11 - "Heating Climate Module"
Cohesion: 0.12
Nodes (9): Climate, Climate class for Home Assistant.      Args:         Heating (object): Heating c, Initialise heating.          Args:             session (object, optional): Used, Min/Max Temp.          Args:             device (dict): device to get min/max te, Backwards-compatible alias for set_mode., Backwards-compatible alias for set_target_temperature., Backwards-compatible alias for set_boost_on., Backwards-compatible alias for set_boost_off. (+1 more)

### Community 12 - "Smart Light Module"
Cohesion: 0.18
Nodes (7): Light, Home Assistant Light Code.      Args:         HiveLight (object): HiveLight Code, Initialise light.          Args:             session (object, optional): Used to, Set light to turn off.          Args:             device (dict): Device to be tu, Backwards-compatible alias for turn_on., Backwards-compatible alias for turn_off., Backwards-compatible alias for get_light.

### Community 13 - "Project & CI/CD"
Cohesion: 0.2
Nodes (12): Hive smart home platform, Home Assistant platform, pyhive-integration PyPI package, Pyhiveapi README, Git branching model feature-dev-master, ci.yml continuous integration workflow, dev-publish.yml manual dev PyPI publish workflow, dev-release-pr.yml release PR and version bump workflow (+4 more)

### Community 14 - "Debug Tracer"
Cohesion: 0.18
Nodes (5): DebugContext, Set trace calls on entering debugger., Remove trace on exiting debugger., Print out lines for function., Debug context to trace any function calls inside the context.

### Community 15 - "Coverage Report UI"
Cohesion: 0.29
Nodes (2): getCellValue(), rowComparator()

### Community 16 - "Device Key Translation"
Cohesion: 0.25
Nodes (4): Translate a legacy camelCase key to the current snake_case attribute name., Support dict-style read access, resolving legacy camelCase keys., Support dict-style write access, resolving legacy camelCase keys., Return True if the key resolves to a non-None attribute.

### Community 17 - "Test Mock Objects"
Cohesion: 0.33
Nodes (5): MockConfig, MockDevice, Mock services for tests., Mock Device for tests., Mock config for tests.

### Community 18 - "Package Build Setup"
Cohesion: 0.5
Nodes (3): Setup pyhiveapi package., Get requirements from file., requirements_from_file()

### Community 19 - "Async-Sync Code Generation"
Cohesion: 1.0
Nodes (3): unasync sync code generation tool, apyhiveapi async package, pyhiveapi sync package

### Community 20 - "Time Utilities"
Cohesion: 1.0
Nodes (1): Convert minutes string to datetime.          Args:             minutes_to_conver

### Community 21 - "TRV Device Linking"
Cohesion: 1.0
Nodes (1): Use TRV device to get the linked thermostat device.          Args:             d

### Community 22 - "Docs & Graph Integration"
Cohesion: 1.0
Nodes (2): AGENTS.md repository guidelines and project structure, graphify knowledge graph integration

### Community 23 - "Package Init (src)"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Auth Module File"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Heating Operation Modes"
Cohesion: 1.0
Nodes (1): Get heating list of possible modes.          Returns:             list: Operatio

### Community 26 - "Heating Return Modes"
Cohesion: 1.0
Nodes (1): Get heating list of possible modes.          Returns:             list: Return l

### Community 27 - "API Package Init"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Requests HTTP Dependency"
Cohesion: 1.0
Nodes (1): requests HTTP library dependency

### Community 29 - "Loguru Logging Dependency"
Cohesion: 1.0
Nodes (1): loguru logging dependency

### Community 30 - "Pyquery HTML Dependency"
Cohesion: 1.0
Nodes (1): pyquery HTML parsing dependency

### Community 31 - "Pre-commit Linting"
Cohesion: 1.0
Nodes (1): pre-commit linting framework dependency

### Community 32 - "Pylint Static Analysis"
Cohesion: 1.0
Nodes (1): pylint static analysis tool

### Community 33 - "Tox Test Automation"
Cohesion: 1.0
Nodes (1): tox test automation tool

### Community 34 - "PBR Build Tool"
Cohesion: 1.0
Nodes (1): pbr Python build tool

### Community 35 - "Code of Conduct"
Cohesion: 1.0
Nodes (1): Contributor Covenant Code of Conduct

### Community 36 - "Map Dict Wrapper"
Cohesion: 1.0
Nodes (1): Map attribute-access dict wrapper class

### Community 37 - "Security Policy"
Cohesion: 1.0
Nodes (1): Security policy supported versions

### Community 38 - "Coverage Functions Index"
Cohesion: 1.0
Nodes (1): Coverage Function Index

### Community 39 - "Coverage Classes Index"
Cohesion: 1.0
Nodes (1): Coverage Class Index

### Community 40 - "Coverage UI Asset"
Cohesion: 1.0
Nodes (1): Keyboard Closed Icon (Coverage Report Asset)

### Community 41 - "Coverage Favicon"
Cohesion: 1.0
Nodes (1): Coverage.py Favicon (32px)

### Community 42 - "HTML Coverage Report"
Cohesion: 1.0
Nodes (1): HTML Coverage Report

### Community 43 - "Coverage.py Tool"
Cohesion: 1.0
Nodes (1): Coverage.py Tool

## Ambiguous Edges - Review These
- `apyhiveapi.session (55% coverage)` → `apyhiveapi.api.hive_auth (0% coverage)`  [AMBIGUOUS]
  htmlcov/index.html · relation: conceptually_related_to

## Knowledge Gaps
- **305 isolated node(s):** `Setup pyhiveapi package.`, `Get requirements from file.`, `Tests for session polling behaviour.`, `Placeholder smoke test.`, `force_update() calls _poll_devices and returns its result when no poll is runnin` (+300 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Time Utilities`** (2 nodes): `.convert_minutes_to_time()`, `Convert minutes string to datetime.          Args:             minutes_to_conver`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `TRV Device Linking`** (2 nodes): `.get_heat_on_demand_device()`, `Use TRV device to get the linked thermostat device.          Args:             d`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Docs & Graph Integration`** (2 nodes): `AGENTS.md repository guidelines and project structure`, `graphify knowledge graph integration`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Package Init (src)`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Auth Module File`** (1 nodes): `async_auth.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Heating Operation Modes`** (1 nodes): `Get heating list of possible modes.          Returns:             list: Operatio`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Heating Return Modes`** (1 nodes): `Get heating list of possible modes.          Returns:             list: Return l`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `API Package Init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Requests HTTP Dependency`** (1 nodes): `requests HTTP library dependency`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Loguru Logging Dependency`** (1 nodes): `loguru logging dependency`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Pyquery HTML Dependency`** (1 nodes): `pyquery HTML parsing dependency`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Pre-commit Linting`** (1 nodes): `pre-commit linting framework dependency`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Pylint Static Analysis`** (1 nodes): `pylint static analysis tool`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Tox Test Automation`** (1 nodes): `tox test automation tool`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `PBR Build Tool`** (1 nodes): `pbr Python build tool`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Code of Conduct`** (1 nodes): `Contributor Covenant Code of Conduct`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Map Dict Wrapper`** (1 nodes): `Map attribute-access dict wrapper class`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Security Policy`** (1 nodes): `Security policy supported versions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Coverage Functions Index`** (1 nodes): `Coverage Function Index`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Coverage Classes Index`** (1 nodes): `Coverage Class Index`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Coverage UI Asset`** (1 nodes): `Keyboard Closed Icon (Coverage Report Asset)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Coverage Favicon`** (1 nodes): `Coverage.py Favicon (32px)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `HTML Coverage Report`** (1 nodes): `HTML Coverage Report`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Coverage.py Tool`** (1 nodes): `Coverage.py Tool`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `apyhiveapi.session (55% coverage)` and `apyhiveapi.api.hive_auth (0% coverage)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `debug()` connect `Device API Operations` to `Hive Exception Types`, `Session & Configuration`, `Action Device Module`, `Sync API Client`, `Async API Client`, `Debug Tracer`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Why does `HiveAuthAsync` connect `Device API Operations` to `SRP Crypto Utilities`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `HiveSession` connect `Hive Exception Types` to `Device API Operations`, `Action Device Module`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 51 inferred relationships involving `debug()` (e.g. with `.set_target_temperature()` and `.set_mode()`) actually correct?**
  _`debug()` has 51 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `HiveHelper` (e.g. with `HiveSession` and `Hive Session Code.      Raises:         HiveUnknownConfiguration: Unknown config`) actually correct?**
  _`HiveHelper` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `HiveSession` (e.g. with `HiveAttributes` and `HiveApiError`) actually correct?**
  _`HiveSession` has 14 INFERRED edges - model-reasoned connections that need verification._
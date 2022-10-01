# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CodeQL Action

### Changed

- Bumped version of Poetry Action
- Added a Nautobot version to the testing matrix in CI
- Bumped `oauthlib` to 3.2.1
- Unpinned `responses` testing library

### Removed

## [0.1.3] - 2022-08-13

### Added

- Added default (configurable) setting to always drop link-local addresses from IPv6 assigned interfaces from vSphere
- Added logging to interface addresses dropped

### Changed

- Bumped Django to 3.2.15 due to security fix

### Removed

## [0.1.2] - 2022-07-20

### Added

- fixed bug where VM with zero interfaces caused a key error from empty response
- Added several `debug` statements to show more verbose, optional logging

### Changed

- bumped local dependencies, mostly due to django vulnerability

### Removed

## [0.1.1] - 2022-05-18

### Added

- Added documentation on warning for `ENFORCE_CLUSTER_GROUP_TOP_LEVEL`
- Added `netutils` package
- fixed a bug with `mac_address` being None causing an orm query call exception

### Changed

### Removed

## [0.1.0] - 2022-05-17

- Initial release of Nautobot SSoT vSphere Plugin

### Added

### Changed

### Removed

## [Unreleased]

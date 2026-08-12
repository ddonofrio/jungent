# Changelog

All notable changes to Jungent will be documented in this file.

## [Unreleased]

### Fixed
- Fixed ruff linting issues (SIM102 nested if statements, SIM110 loop vs any())
- Fixed black formatting issues across all source files
- Fixed double `.isoformat()` calls in models.py from_dict methods
- Added missing `datetime` import to instruction_funnel.py
- Updated datetime.utcnow() to timezone-aware datetime.now(timezone.utc) where appropriate

### Improved
- Enhanced Instruction Funnel module with full behavioral scenario implementations:
  - Scenario A: Large initial prompt with tool extraction and context reduction
  - Scenario B: Work-order request handling with relevant tool selection  
  - Scenario C: PowerShell security exception recovery instruction
- Added audit event logging for module decisions
- Improved protocol validation in Hammer & Scissors

### Added
- CI workflow (.github/workflows/ci.yml) for automated testing and quality checks
- Documentation files:
  - docs/proxy-mode.md - Proxy Mode overview with configuration reference
  - docs/hammer-and-scissors.md - Module interface and architecture documentation
  - docs/instruction-funnel.md - Behavioral scenarios and decision trace documentation
- .gitignore updates to exclude generated files properly
- README.md updated with "Jungent gives your agent wings." product positioning
- Installation instructions added to README

### Changed
- Canonical models in src/jungent/models.py use timezone-aware datetimes
- Updated pyproject.toml ruff configuration migrated to `[tool.ruff.lint]` format
- Black formatting applied to all source files for consistency

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-01-01

### Added
- **Gemini 3 Support:** Updated default AI model to `gemini-3-flash-preview` for improved categorization and performance.
- **Single Source of Truth:** Centralized model configuration in `src/autospendtracker/config/settings.py`.
- **JSON Token Storage:** Switched from `pickle` to `JSON` for Gmail credentials storage, improving security and portability.

### Changed
- **Default Configuration:** Updated `.env.example`, `.env.production.example`, and `docker-compose.yml` to use Gemini 3.
- **Docker Entrypoint:** Simplified `entrypoint.sh` to run directly as `appuser` (removed unnecessary `su-exec` dependency).
- **Authentication:** Refactored `auth.py` to use `google-auth-oauthlib`'s `Credentials.to_json` and `from_authorized_user_info`.

### Fixed
- **Docker Health Check:** Fixed permission issues and missing dependencies in Docker health check execution.
- **Unit Tests:** Updated `test_auth.py` and `test_ai.py` to align with new JSON-based auth and configuration injection.

## [2.0.0] - 2025-01-01

### Added
- **Project Modernization:** Restructured project to standard `src/` layout.
- **Dependency Management:** Migrated to `uv` and `pyproject.toml`.
- **Docker Optimization:** Multi-stage build reducing image size to ~180MB.

## [1.0.0] - 2024-01-01

### Added
- Initial release of AutoSpendTracker.
- Automated email parsing from Gmail.
- AI-based transaction categorization using Vertex AI/Gemini.
- Google Sheets integration.

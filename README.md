# DIS Verification GenAI

AI-powered verification and test plan generation system for Defense Information Systems (DIS) testing and compliance.

## Quick Start

For installation and setup instructions, see:
- [QUICKSTART.md](QUICKSTART.md) - Quick installation guide
- [INSTALL.md](INSTALL.md) - Detailed installation instructions

## Features

- AI-powered test plan generation
- Document verification and compliance checking
- Support for multiple AI models (OpenAI, Anthropic, local Ollama models)
- Docker-based deployment for easy setup
- Vector database integration for intelligent document retrieval
- RAG (Retrieval Augmented Generation) capabilities

## Installation

### Download Installers

Download the latest release for your platform:
- **Windows**: `dis-verification-genai-X.X.X.msi`
- **Linux (Debian/Ubuntu)**: `dis-verification-genai_X.X.X_amd64.deb`
- **Linux (RHEL/CentOS/Fedora)**: `dis-verification-genai-X.X.X.x86_64.rpm`
- **macOS**: `dis-verification-genai-X.X.X.dmg`

See [Releases](https://github.com/martinmanuel9/dis_verification_genai/releases)

### Prerequisites

- Docker 24.0.0 or later
- Docker Compose 2.20.0 or later
- 8 GB RAM minimum (16 GB recommended)
- 50 GB disk space
- 4 CPU cores recommended

## Usage

After installation:

1. Configure your API keys in `.env`
2. Start the services: `docker compose up -d`
3. Access the web interface: http://localhost:8501

## Documentation

- [Quick Start Guide](QUICKSTART.md)
- [Installation Guide](INSTALL.md)
- [Release Process](RELEASE_PROCESS.md)
- [Changelog](CHANGELOG.md)

## License

Proprietary - All rights reserved

## Support

For issues and support:
- [GitHub Issues](https://github.com/martinmanuel9/dis_verification_genai/issues)

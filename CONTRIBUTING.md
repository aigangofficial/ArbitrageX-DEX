# Contributing to ArbitrageX

We love your input! We want to make contributing to ArbitrageX as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Pull Request Process

1. Update the README.md with details of changes to the interface, if applicable.
2. Update the docs/ folder with any new documentation.
3. The PR will be merged once you have the sign-off of two other developers.

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using GitHub's [issue tracker]

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/yourusername/arbitragex/issues/new).

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Use a Consistent Coding Style

* Use TypeScript for backend and frontend code
* 2 spaces for indentation rather than tabs
* You can try running `npm run lint` for style unification

## Code of Conduct

### Our Pledge

In the interest of fostering an open and welcoming environment, we as contributors and maintainers pledge to making participation in our project and our community a harassment-free experience for everyone.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable behavior and are expected to take appropriate and fair corrective action in response to any instances of unacceptable behavior.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.

## Development Environment

### Requirements

1. Node.js v16+
2. Python 3.8+
3. MongoDB 4.4+
4. Mainnet RPC URL (Alchemy recommended)
5. Docker & Docker Compose

### Setup

1. Fork and Clone
```bash
git clone https://github.com/yourusername/arbitragex.git
cd arbitragex
```

2. Install Dependencies
```bash
npm install
cd backend && npm install
cd frontend && npm install
```

3. Configure Environment
```bash
cp config/.env.example config/.env.fork
# Edit .env.fork with your settings
```

### Mainnet Fork Development

All development must be done against a mainnet fork for consistent testing:

1. Configure Fork
```env
MAINNET_RPC_URL=your_mainnet_rpc_url
FORK_BLOCK_NUMBER=19261000
FORK_ENABLED=true
```

2. Start Development Environment
```bash
npm run start:fork
```

3. Run Tests
```bash
npm test
```

### Code Style

1. TypeScript
- Use strict mode
- Follow ESLint configuration
- Document public functions
- Use type annotations

2. Solidity
- Follow Solidity style guide
- Use latest stable version (0.8.20)
- Document functions with NatSpec
- Include test coverage

3. React
- Use functional components
- Implement proper error boundaries
- Follow component structure
- Document props

### Testing Requirements

1. Smart Contracts
- 100% test coverage
- Include mainnet fork tests
- Test flash loan repayment
- Verify gas usage

2. Backend
- API endpoint tests
- WebSocket service tests
- Integration tests
- Performance tests

3. Frontend
- Component tests
- Integration tests
- E2E tests
- Network status tests

### Pull Request Process

1. Create Feature Branch
```bash
git checkout -b feature/your-feature
```

2. Develop and Test
- Write tests first
- Implement feature
- Run all tests
- Update documentation

3. Submit PR
- Reference issue number
- Include test results
- Add documentation
- Update CHANGELOG

### Code Review

PRs must pass:
1. All tests on mainnet fork
2. Linter checks
3. Type checking
4. Security review
5. Performance review

### Documentation

Update:
1. README.md
2. API documentation
3. Test documentation
4. Deployment guides

### Monitoring

Implement:
1. Metrics collection
2. Error tracking
3. Performance monitoring
4. Alert configuration

### Security

Follow:
1. Smart contract best practices
2. OWASP guidelines
3. Gas optimization patterns
4. Input validation

### Release Process

1. Version Bump
```bash
npm version patch|minor|major
```

2. Update CHANGELOG.md
3. Create Release PR
4. Deploy to Staging
5. Test on Mainnet Fork
6. Create GitHub Release

### Support

- GitHub Issues
- Discord Community
- Documentation
- Stack Overflow

### Code of Conduct

1. Be respectful
2. Follow guidelines
3. Help others
4. Report issues

### License

MIT License - see LICENSE file

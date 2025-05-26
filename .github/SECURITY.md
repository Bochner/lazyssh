# Security Policy

## Supported Versions

We provide security updates for the following versions of LazySSH:

| Version | Supported          |
| ------- | ------------------ |
| 1.3.x   | :white_check_mark: |
| 1.2.x   | :white_check_mark: |
| 1.1.x   | :x:                |
| < 1.1   | :x:                |

## Reporting a Vulnerability

The LazySSH team takes security bugs seriously. We appreciate your efforts to responsibly disclose your findings.

### How to Report

Please report security vulnerabilities by emailing **lazyssh-security@example.com**.

**Do not report security vulnerabilities through public GitHub issues.**

### What to Include

Please include the following information in your report:

- Description of the vulnerability
- Steps to reproduce the issue
- Affected versions
- Any potential impact
- Suggested fix (if you have one)

### Response Timeline

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours.
- **Initial Assessment**: We will provide an initial assessment within 5 business days.
- **Fix and Disclosure**: We aim to fix confirmed vulnerabilities within 30 days and will coordinate disclosure timing with you.

### Security Features

LazySSH includes several security features:

- **SSH Key Management**: Secure handling of SSH keys and credentials
- **Connection Validation**: Verification of SSH connections before establishing tunnels
- **Input Sanitization**: Proper sanitization of user inputs to prevent injection attacks
- **Secure Defaults**: Conservative default settings that prioritize security

### Security Best Practices

When using LazySSH:

1. **Keep Updated**: Always use the latest version
2. **Secure Keys**: Use strong SSH keys and protect private keys
3. **Network Security**: Use LazySSH only on trusted networks when possible
4. **Access Control**: Limit access to LazySSH configuration files
5. **Monitoring**: Monitor SSH connections and tunnel usage

### Scope

This security policy applies to:

- LazySSH core application
- Official installation scripts
- Documentation that could affect security

Out of scope:

- Third-party dependencies (report directly to the maintainers)
- Issues in forked versions
- Social engineering attacks

### Recognition

We will acknowledge security researchers who help improve LazySSH security in our release notes and security advisories (with their permission).

## Contact

For security-related questions or concerns, contact: **lazyssh-security@example.com**

For general support: [GitHub Issues](https://github.com/Bochner/lazyssh/issues) 
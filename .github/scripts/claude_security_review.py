#!/usr/bin/env python3
"""
Claude Code Security Review Script
Uses Anthropic API to analyze code files for security vulnerabilities
"""

import os
import sys
import json
from pathlib import Path

def analyze_file_with_claude(file_path, api_key):
    """Analyze a single file for security vulnerabilities using Claude API"""
    try:
        import anthropic
    except ImportError:
        print("Installing anthropic package...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "anthropic"])
        import anthropic

    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except Exception as e:
        return {
            "file": file_path,
            "error": f"Could not read file: {str(e)}",
            "vulnerabilities": []
        }

    # Skip empty files or very small files
    if len(code_content.strip()) < 10:
        return {
            "file": file_path,
            "message": "File too small to analyze",
            "vulnerabilities": []
        }

    # Create Anthropic client
    client = anthropic.Anthropic(api_key=api_key)

    # Security review prompt
    prompt = f"""You are a senior security engineer performing a code security audit.

Analyze the following code file for security vulnerabilities, focusing on:

## OWASP Top 10
1. SQL Injection - Unsanitized database queries
2. Cross-Site Scripting (XSS) - Unescaped user input in HTML/JS
3. Broken Authentication - Auth flow and session issues
4. Sensitive Data Exposure - Hardcoded secrets, API keys, passwords
5. XML External Entities (XXE) - XML parsing vulnerabilities
6. Broken Access Control - Authorization logic flaws
7. Security Misconfiguration - Insecure settings
8. Insecure Deserialization - Unsafe pickle, yaml, json usage
9. Known Vulnerabilities - Dangerous function usage
10. Insufficient Logging - Missing security event logging

## Python-Specific Security
- Command injection via os.system(), subprocess, eval(), exec()
- Path traversal in file operations
- Pickle deserialization attacks
- Insecure random number generation (random vs secrets)
- Timing attacks in authentication
- SSRF in HTTP requests
- Regex denial of service (ReDoS)

## File Information
**File**: `{file_path}`
**Language**: {Path(file_path).suffix}

## Code to Analyze:
```
{code_content}
```

## Output Format
For each vulnerability, provide:
- Severity: CRITICAL, HIGH, MEDIUM, or LOW
- Line number (if applicable)
- Issue description
- Security impact
- Recommended fix

If no vulnerabilities are found, respond with: "NO_VULNERABILITIES_FOUND"

Be concise and specific. Focus on real security issues, not style or best practices."""

    try:
        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        analysis = message.content[0].text

        # Check if no vulnerabilities found
        if "NO_VULNERABILITIES_FOUND" in analysis:
            return {
                "file": file_path,
                "status": "clean",
                "vulnerabilities": []
            }

        return {
            "file": file_path,
            "status": "reviewed",
            "analysis": analysis,
            "vulnerabilities": parse_vulnerabilities(analysis)
        }

    except Exception as e:
        return {
            "file": file_path,
            "error": f"API error: {str(e)}",
            "vulnerabilities": []
        }


def parse_vulnerabilities(analysis_text):
    """Parse vulnerability information from Claude's response"""
    vulnerabilities = []

    # Look for severity markers
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if severity in analysis_text:
            vulnerabilities.append({
                "severity": severity,
                "found": True
            })

    return vulnerabilities


def format_markdown_report(results):
    """Format results as markdown for GitHub"""
    report = []
    report.append("# Claude Code Security Analysis\n")

    total_files = len(results)
    files_with_issues = sum(1 for r in results if r.get("vulnerabilities") or r.get("analysis"))

    report.append(f"**Files Analyzed**: {total_files}")
    report.append(f"**Files with Findings**: {files_with_issues}\n")

    # Group by status
    clean_files = [r for r in results if r.get("status") == "clean"]
    reviewed_files = [r for r in results if r.get("status") == "reviewed"]
    error_files = [r for r in results if r.get("error")]

    if clean_files:
        report.append(f"\n## ✅ Clean Files ({len(clean_files)})")
        for result in clean_files:
            report.append(f"- `{result['file']}`")

    if reviewed_files:
        report.append(f"\n## 🔍 Security Findings ({len(reviewed_files)})")
        for result in reviewed_files:
            report.append(f"\n### `{result['file']}`")
            report.append(f"\n{result.get('analysis', 'No details available')}")

    if error_files:
        report.append(f"\n## ⚠️ Analysis Errors ({len(error_files)})")
        for result in error_files:
            report.append(f"- `{result['file']}`: {result.get('error', 'Unknown error')}")

    report.append("\n---")
    report.append("\n*Analysis powered by Claude 3.5 Sonnet via Anthropic API*")

    return "\n".join(report)


def main():
    """Main function"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Get files to analyze from command line args
    files_to_analyze = sys.argv[1:] if len(sys.argv) > 1 else []

    if not files_to_analyze:
        print("No files to analyze")
        sys.exit(0)

    print(f"Analyzing {len(files_to_analyze)} file(s) with Claude...")

    results = []
    for file_path in files_to_analyze:
        print(f"  Analyzing: {file_path}")
        result = analyze_file_with_claude(file_path, api_key)
        results.append(result)

    # Generate markdown report
    report = format_markdown_report(results)

    # Save to file
    output_file = "security-reports/claude-analysis.md"
    os.makedirs("security-reports", exist_ok=True)

    with open(output_file, 'w') as f:
        f.write(report)

    print(f"\n✅ Analysis complete. Report saved to: {output_file}")

    # Print summary
    critical_count = sum(1 for r in results
                        for v in r.get("vulnerabilities", [])
                        if v.get("severity") == "CRITICAL")

    if critical_count > 0:
        print(f"\n⚠️  Found {critical_count} CRITICAL vulnerability/ies")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

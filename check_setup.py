"""Diagnostic script to check AutoSpendTracker setup.

Run this to verify your environment is correctly configured.
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Check Python version."""
    print("=" * 60)
    print("Checking Python Version...")
    print("=" * 60)
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major == 3 and version.minor >= 11:
        print("✓ Python version is compatible (3.11+)")
        return True
    else:
        print("✗ Python version must be 3.11 or higher")
        return False


def check_env_file():
    """Check .env file exists and has required values."""
    print("\n" + "=" * 60)
    print("Checking .env Configuration...")
    print("=" * 60)

    env_path = Path(".env")
    if not env_path.exists():
        print("✗ .env file not found")
        print("  → Create .env file from .env.example")
        print("  → Command: cp .env.example .env")
        return False

    print("✓ .env file exists")

    # Check for required values
    required_vars = ["PROJECT_ID", "SPREADSHEET_ID"]
    missing = []

    with open(".env", "r") as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content or f"{var}=your-" in content:
                missing.append(var)

    if missing:
        print(f"✗ Missing or not configured: {', '.join(missing)}")
        print("  → Edit .env and set actual values")
        return False

    print(f"✓ Required variables configured: {', '.join(required_vars)}")
    return True


def check_credentials():
    """Check credential files exist."""
    print("\n" + "=" * 60)
    print("Checking Credential Files...")
    print("=" * 60)

    creds_ok = True

    # Check credentials.json (Gmail OAuth)
    gmail_creds = Path("credentials.json")
    if gmail_creds.exists():
        print("✓ credentials.json found (Gmail OAuth)")
    else:
        print("✗ credentials.json not found")
        print("  → Download from Google Cloud Console")
        print("  → Enable Gmail API and create OAuth 2.0 credentials")
        creds_ok = False

    # Check ASTservice.json (Service Account)
    service_creds = Path("ASTservice.json")
    if service_creds.exists():
        print("✓ ASTservice.json found (Service Account)")
    else:
        print("✗ ASTservice.json not found")
        print("  → Download from Google Cloud Console")
        print("  → Create Service Account with appropriate permissions")
        creds_ok = False

    return creds_ok


def check_dependencies():
    """Check required Python packages are installed."""
    print("\n" + "=" * 60)
    print("Checking Python Dependencies...")
    print("=" * 60)

    required_packages = [
        "google-genai",
        "google-api-python-client",
        "google-auth-oauthlib",
        "beautifulsoup4",
        "python-dotenv",
        "pydantic"
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} not installed")
            missing.append(package)

    if missing:
        print(f"\n✗ Missing packages: {', '.join(missing)}")
        print("  → Install with: uv pip install -e .")
        return False

    print("\n✓ All required dependencies installed")
    return True


def check_package_installation():
    """Check if autospendtracker package is installed."""
    print("\n" + "=" * 60)
    print("Checking Package Installation...")
    print("=" * 60)

    try:
        import autospendtracker
        print("✓ autospendtracker package is importable")

        # Check if it's in development mode
        package_path = Path(autospendtracker.__file__).parent.parent.parent
        if package_path.name == "src":
            print("✓ Package installed in development mode")
        return True
    except ImportError as e:
        print("✗ autospendtracker package not importable")
        print(f"  Error: {e}")
        print("  → Install with: uv pip install -e .")
        return False


def check_gcp_setup():
    """Check Google Cloud Platform setup."""
    print("\n" + "=" * 60)
    print("Checking Google Cloud Setup...")
    print("=" * 60)

    print("Please verify manually:")
    print("  □ Gmail API is enabled in your GCP project")
    print("  □ Google Sheets API is enabled in your GCP project")
    print("  □ Vertex AI API is enabled in your GCP project")
    print("  □ Service account has necessary permissions")
    print("  □ OAuth consent screen is configured")
    print("\n  → Visit: https://console.cloud.google.com/apis/dashboard")


def main():
    """Run all diagnostic checks."""
    print("\n" + "=" * 70)
    print("AutoSpendTracker Diagnostic Tool")
    print("=" * 70)

    checks = [
        ("Python Version", check_python_version),
        ("Environment File", check_env_file),
        ("Credentials", check_credentials),
        ("Dependencies", check_dependencies),
        ("Package Installation", check_package_installation),
    ]

    results = {}
    for name, check_func in checks:
        results[name] = check_func()

    # GCP check (manual verification)
    check_gcp_setup()

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    passed = sum(results.values())
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")

    print("\n" + "=" * 70)
    if passed == total:
        print("✓ All checks passed! You're ready to run the application.")
        print("\nNext steps:")
        print("  1. Verify GCP setup manually (see above)")
        print("  2. Run: python run_app.py")
    else:
        print(f"✗ {total - passed} check(s) failed. Please fix the issues above.")
        print("\nQuick fixes:")
        if not results.get("Environment File"):
            print("  • cp .env.example .env && nano .env")
        if not results.get("Dependencies"):
            print("  • uv pip install -e .")
        if not results.get("Credentials"):
            print("  • Download credentials from Google Cloud Console")
    print("=" * 70)


if __name__ == "__main__":
    main()

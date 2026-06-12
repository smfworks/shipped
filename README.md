# shipped

Release management CLI — bump versions, generate changelogs, tag releases, push to GitHub + PyPI.

## Install

```bash
pip install shipped
```

## Usage

```bash
# Show current version
shipped current

# Bump version
shipped bump patch   # 1.2.3 → 1.2.4
shipped bump minor   # 1.2.3 → 1.3.0
shipped bump major   # 1.2.3 → 2.0.0

# Generate changelog from git history
shipped changelog
shipped changelog -o CHANGELOG.md

# Create a git tag
shipped tag

# Push tag to remote
shipped push

# Publish to PyPI
shipped publish
shipped publish --test  # TestPyPI

# Full release (bump + changelog + tag + push + publish)
shipped release patch
shipped release minor --test
```

## License

MIT
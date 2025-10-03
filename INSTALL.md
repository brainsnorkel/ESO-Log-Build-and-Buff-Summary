# Installation Guide

## Quick Install

Run the installer script:

```bash
./install.sh
```

This will create a symlink in `~/bin` (or `/usr/local/bin` if `~/bin` doesn't exist).

## Add to PATH (if needed)

If the installer warns that the bin directory is not in your PATH, add this to your `~/.zshrc` or `~/.bashrc`:

```bash
export PATH="$HOME/bin:$PATH"
```

Then reload your shell:

```bash
source ~/.zshrc  # or source ~/.bashrc
```

## Verify Installation

Test the command:

```bash
eso-report --help
```

## Usage Examples

### Post kills to Discord webhook (recommended)
```bash
eso-report mTbKBVJGW8z6AR4P --discord-webhook-post
```

### Post kills AND wipes
```bash
eso-report mTbKBVJGW8z6AR4P --discord-webhook-post --include-wipes
```

### Generate Discord file only
```bash
eso-report mTbKBVJGW8z6AR4P --output discord
```

### Console output only
```bash
eso-report mTbKBVJGW8z6AR4P
```

## Requirements

1. **Python 3.9+**
2. **Environment variables** (create `.env` file in project root):
   ```
   ESOLOGS_ID=your_client_id
   ESOLOGS_SECRET=your_client_secret
   DISCORD_WEBHOOK_URL=your_webhook_url
   ```

3. **Python dependencies** (install from project root):
   ```bash
   pip install -r requirements.txt
   ```

## Uninstall

Remove the symlink:

```bash
rm ~/bin/eso-report
```

## Manual Installation

If you prefer to install manually:

1. Copy `eso-report` to your bin directory:
   ```bash
   cp eso-report ~/bin/
   ```

2. Make it executable:
   ```bash
   chmod +x ~/bin/eso-report
   ```

3. Ensure `~/bin` is in your PATH (see above)

## Troubleshooting

### Command not found
- Make sure `~/bin` is in your PATH
- Verify the symlink exists: `ls -la ~/bin/eso-report`

### Import errors
- Make sure you're running from the project directory or have installed dependencies
- Check that your virtual environment is activated if using one

### API credential errors
- Verify `.env` file exists in the project root
- Check that `ESOLOGS_ID` and `ESOLOGS_SECRET` are set correctly


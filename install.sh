#!/bin/bash
# workspace-sleep installer

set -e

REPO="https://raw.githubusercontent.com/Miraakz9/i3wm-workspace-auto-suspend/main"
INSTALL_DIR="$HOME/.config/i3"
SCRIPT="workspace_sleep.py"
I3_CONFIG="$HOME/.config/i3/config"

#Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # no color

info()    { echo -e "${BLUE}[*]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warning() { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo -e "${BLUE}workspace-sleep installer${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

#Check dependencies
info "Checking dependencies..."

command -v python3 >/dev/null 2>&1 || error "python3 is required but not installed."
command -v i3-msg  >/dev/null 2>&1 || error "i3-msg is required. Are you running i3wm?"
command -v curl    >/dev/null 2>&1 || command -v wget >/dev/null 2>&1 || error "curl or wget is required."

success "Dependencies OK"

#Create install directory
info "Creating $INSTALL_DIR if needed..."
mkdir -p "$INSTALL_DIR"

#Download script
info "Downloading $SCRIPT..."

if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$REPO/$SCRIPT" -o "$INSTALL_DIR/$SCRIPT"
else
    wget -q "$REPO/$SCRIPT" -O "$INSTALL_DIR/$SCRIPT"
fi

chmod +x "$INSTALL_DIR/$SCRIPT"
success "Downloaded to $INSTALL_DIR/$SCRIPT"

#Add to i3 config
EXEC_LINE="exec --no-startup-id python3 $INSTALL_DIR/$SCRIPT"

if [ ! -f "$I3_CONFIG" ]; then
    warning "i3 config not found at $I3_CONFIG — skipping auto-start setup."
    warning "Add this line manually to your i3 config:"
    echo ""
    echo "    $EXEC_LINE"
    echo ""
else
    if grep -q "workspace_sleep.py" "$I3_CONFIG"; then
        warning "workspace_sleep already found in i3 config — skipping."
    else
        info "Adding auto-start to i3 config..."
        echo "" >> "$I3_CONFIG"
        echo "# workspace-sleep: suspend inactive workspace apps" >> "$I3_CONFIG"
        echo "$EXEC_LINE" >> "$I3_CONFIG"
        success "Added to $I3_CONFIG"
    fi
fi

#Kill any old instances
if pgrep -f workspace_sleep.py >/dev/null 2>&1; then
    info "Stopping existing instance..."
    pkill -f workspace_sleep.py || true
    sleep 1
fi

#Start the script
info "Starting workspace-sleep..."
nohup python3 "$INSTALL_DIR/$SCRIPT" > /dev/null 2>&1 &
sleep 1

if pgrep -f workspace_sleep.py >/dev/null 2>&1; then
    success "workspace-sleep is running!"
else
    error "Failed to start workspace-sleep. Check $INSTALL_DIR/$SCRIPT manually."
fi

#Done
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN} Installation complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo " Script:    $INSTALL_DIR/$SCRIPT"
echo " Log:       /tmp/workspace_sleep.log"
echo " i3 config: $I3_CONFIG"
echo ""
echo " Watch logs:    tail -f /tmp/workspace_sleep.log"
echo " Stop:          pkill -f workspace_sleep.py"
echo " Uninstall:     bash <(curl -fsSL $REPO/uninstall.sh)"
echo ""

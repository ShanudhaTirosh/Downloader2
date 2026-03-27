#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
#  Shanu Fx Private Downloader - Linux/macOS Setup
#  Author: Shanudha Tirosh
# ════════════════════════════════════════════════════════════════

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Shanu Fx Private Downloader - Setup               ║${NC}"
echo -e "${CYAN}║               by Shanudha Tirosh                      ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Check Python ──────────────────────────────────────────────────────────────
echo -e "${CYAN}[1/5]${NC} Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}  ERROR: python3 not found. Install Python 3.11+${NC}"
    exit 1
fi
PYVER=$(python3 --version)
echo -e "${GREEN}  ✓ ${PYVER}${NC}"

# ── Create venv ───────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[2/5]${NC} Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}  ✓ venv created${NC}"
else
    echo -e "${GREEN}  ✓ venv already exists${NC}"
fi

source venv/bin/activate

# ── Upgrade pip ───────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[3/5]${NC} Upgrading pip..."
pip install --upgrade pip -q
echo -e "${GREEN}  ✓ pip upgraded${NC}"

# ── Install requirements ──────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[4/5]${NC} Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}  ✓ Dependencies installed${NC}"

# ── Check FFmpeg ──────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}[5/5]${NC} Checking FFmpeg..."
if command -v ffmpeg &>/dev/null; then
    echo -e "${GREEN}  ✓ FFmpeg found${NC}"
else
    echo -e "${YELLOW}  ⚠  FFmpeg not found — installing...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install -y ffmpeg 2>/dev/null || \
        sudo yum install -y ffmpeg 2>/dev/null || \
        echo -e "${YELLOW}  Please install FFmpeg: sudo apt install ffmpeg${NC}"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ffmpeg 2>/dev/null || \
        echo -e "${YELLOW}  Please install FFmpeg: brew install ffmpeg${NC}"
    fi
fi

# ── Create launcher script ────────────────────────────────────────────────────
cat > run.sh << 'EOF'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source venv/bin/activate
python main.py "$@"
EOF
chmod +x run.sh

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Setup complete!                                      ║${NC}"
echo -e "${GREEN}║  Run the app with:  ./run.sh                          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

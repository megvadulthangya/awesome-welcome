#!/bin/bash

# XLibre telepítő wrapper script
# Verzió: 1.3 (Javítva: sudo bash futtatás /tmp noexec miatt)

# Lock fájl
LOCKFILE="/tmp/xlibre-installer.lock"

# Lock ellenőrzés
if [ -f "$LOCKFILE" ]; then
    if [[ $LANG == hu* ]]; then
        echo "Az XLibre telepítő már fut!"
    else
        echo "XLibre installer is already running!"
    fi
    exit 1
fi

# Lock fájl létrehozása
touch "$LOCKFILE"
trap 'rm -f "$LOCKFILE"' EXIT INT TERM

# Nyelv beállítása
if [[ $LANG == hu* ]]; then
    INSTALLED_MSG="Az XLibre már telepítve van!"
    INSTALLING_MSG="XLibre telepítése terminál ablakban..."
    DOWNLOAD_FAIL_MSG="A telepítő letöltése sikertelen!"
    NO_TERMINAL_MSG="Nem található támogatott terminál (Tilix, URXVT)!"
    TEST_MSG="XLibre telepítő elindul..."
    PRESS_ENTER="Nyomj Enter-t a bezáráshoz..."
else
    INSTALLED_MSG="XLibre is already installed!"
    INSTALLING_MSG="Starting XLibre installation in terminal window..."
    DOWNLOAD_FAIL_MSG="Failed to download installer!"
    NO_TERMINAL_MSG="No supported terminal found (Tilix, URXVT)!"
    TEST_MSG="XLibre installer starting..."
    PRESS_ENTER="Press Enter to close..."
fi

# Ellenőrzés
check_installation() {
    if pacman -Q xlibre-xserver &>/dev/null 2>&1; then
        show_message "XLibre" "$INSTALLED_MSG"
        exit 0
    fi
}

# Terminál keresése
find_terminal() {
    if command -v tilix &>/dev/null; then echo "tilix"; return 0; fi
    if command -v urxvt &>/dev/null; then echo "urxvt"; return 0; fi
    if command -v xfce4-terminal &>/dev/null; then echo "xfce4-terminal"; return 0; fi
    if command -v alacritty &>/dev/null; then echo "alacritty"; return 0; fi
    if command -v kitty &>/dev/null; then echo "kitty"; return 0; fi
    if command -v gnome-terminal &>/dev/null; then echo "gnome-terminal"; return 0; fi
    return 1
}

# Üzenet megjelenítése
show_message() {
    local title="$1"
    local message="$2"
    if command -v notify-send &>/dev/null; then
        notify-send -a "Awesome Welcome" "$title" "$message"
    else
        echo "$title: $message"
    fi
}

# Letöltés
download_installer() {
    local temp_script=$(mktemp)
    # Hozzáadtam a -L kapcsolót is, hogy kövesse az átirányításokat, ha vannak
    if ! curl -L -sS -o "$temp_script" "https://x11libre.net/repo/arch_based/x86_64/install-xlibre.sh"; then
        show_message "XLibre" "$DOWNLOAD_FAIL_MSG"
        exit 1
    fi
    # Bár a chmod +x itt van, a sudo bash megoldásnál kevésbé kritikus, de maradjon
    chmod +x "$temp_script"
    echo "$temp_script"
}

# Fő folyamat
install_xlibre() {
    show_message "XLibre" "$INSTALLING_MSG"
    local temp_script=$(download_installer)
    local terminal=$(find_terminal)
    
    if [ -z "$terminal" ]; then
        show_message "XLibre" "$NO_TERMINAL_MSG"
        rm -f "$temp_script"
        exit 1
    fi

    # --- JAVÍTÁS ITT ---
    # sudo '$temp_script' HELYETT sudo bash '$temp_script'
    # Ez megkerüli a /tmp noexec korlátozását és a hibás shebang problémákat
    local cmd="echo '$TEST_MSG'; echo ''; sudo bash '$temp_script'; echo ''; echo '$PRESS_ENTER'; read; rm -f '$temp_script'"

    case "$terminal" in
        "tilix")
            tilix -e bash -c "$cmd"
            ;;
        "urxvt")
            urxvt -e bash -c "$cmd"
            ;;
        "xfce4-terminal")
            xfce4-terminal --geometry=80x24 -e "bash -c \"$cmd\""
            ;;
        *)
            "$terminal" -e bash -c "$cmd"
            ;;
    esac
}

main() {
    check_installation
    install_xlibre
}

main "$@"
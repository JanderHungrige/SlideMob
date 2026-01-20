import os

# DMG metadata
filename = 'SlideMob.dmg'
volume_name = 'SlideMob'

# Get project root - assume we're running from the project root
project_root = os.getcwd()

# Input application bundle
app_path = os.path.join(project_root, 'dist', 'SlideMob.app')

# The icon to use for the volume
icon = os.path.join(project_root, 'src', 'slidemob', 'images', 'Appleicon.icns')

# Display settings
badge_icon = icon

# Window configuration
window_rect = ((100, 100), (600, 400))
background = 'builtin-arrow'

# Icon locations
icon_locations = {
    'SlideMob.app': (150, 120),
    'Applications': (450, 120)
}

# Symbols to create
symlinks = {
    'Applications': '/Applications'
}

# Contents of the DMG
files = [app_path]

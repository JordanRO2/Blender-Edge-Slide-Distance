# Blender Edge Slide Distance

Slide edge loops by exact distance measurements instead of factors.

## Overview

Edge Slide by Distance adds precise distance-based edge sliding to Blender's modeling toolkit. Instead of using Blender's default factor-based sliding (0-1), you can now specify exact measurements in real-world units.

## Features

- 📏 **Exact Distance Input**: Enter precise measurements in meters, centimeters, feet, or inches
- 🔍 **Smart Edge Loop Detection**: Automatically detects and analyzes edge loops
- 🔄 **Intelligent Conversion**: Converts distances to Blender's factor system automatically
- 📊 **Multiple Measurement Methods**: Choose between average, minimum, maximum, or first edge distance
- ⚙️ **Full Control**: Supports even sliding, clamping, and direction flipping
- 🔌 **Native Integration**: Works seamlessly with Blender's edge slide system

## Installation

1. Download the latest release from the [Releases](https://github.com/JordanRO2/Blender-Edge-Slide-Distance/releases) page
2. In Blender, go to Edit → Preferences → Add-ons
3. Click "Install" and select the downloaded zip file
4. Enable "Mesh: Blender Edge Slide Distance"

## Usage

### Quick Start
1. Enter Edit Mode (Tab)
2. Select an edge loop (Alt+Click on an edge)
3. Press **Shift+Alt+G** (or go to Edge menu → "Slide by Distance")
4. Enter your desired distance
5. Click OK

### Options

- **Distance**: The exact distance to slide (positive or negative)
- **Even**: Make the edge loop slide evenly
- **Clamp**: Constrain sliding within boundaries
- **Flipped**: Flip the slide direction
- **Measure**: How to calculate distances across the loop
  - Average: Use the average distance
  - Minimum: Use the smallest distance
  - Maximum: Use the largest distance
  - First Selected: Use the first edge's distance

### Tips

- **Positive values**: Slide toward one boundary
- **Negative values**: Slide toward the opposite boundary
- **Units**: Automatically uses your scene's unit system (metric/imperial)

## Perfect For

- 🏗️ Architectural modeling requiring exact measurements
- ⚙️ CAD-like precision modeling
- 🔧 Technical and mechanical part design
- 📐 Any workflow needing precise edge placement

## Requirements

- Blender 4.5.0 or higher

## Technical Details

The addon works by:
1. Detecting the selected edge loop
2. Finding the slide boundaries (parallel edges)
3. Measuring the maximum slide distance
4. Converting your input distance to Blender's 0-1 factor
5. Calling Blender's native edge slide with the calculated factor

## License

GPL v3 - Same as Blender

## Support

For bug reports and feature requests, please use the [Issues](https://github.com/JordanRO2/Blender-Edge-Slide-Distance/issues) page.

## Credits

Developed for the Blender community to bring CAD-like precision to mesh modeling.
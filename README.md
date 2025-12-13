# Image Explorer

A simple, lightweight Python web application for browsing and viewing images in a folder tree structure. Perfect for quickly previewing image collections, photography portfolios, or any directory with nested image folders.

![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)

## Features

- **📁 Recursive Folder Scanning** - Automatically scans all subfolders for images
- **🌳 Interactive Folder Tree** - Navigate through your directory structure with a hierarchical sidebar
- **🖼️ Beautiful Image Gallery** - Responsive grid layout with thumbnail previews
- **🔍 Advanced Image Viewer** - Full-screen lightbox with zoom, pan, and keyboard navigation (powered by PhotoSwipe)
- **🎯 Smart Filtering** - Click folders to filter images (includes subfolders)
- **🎨 Clean UI** - Modern, intuitive interface with smooth animations
- **👁️ Collapsible Sidebar** - Toggle sidebar visibility for more screen space
- **📊 Image Count Badges** - See how many images are in each folder at a glance
- **🚀 Zero Configuration** - Single Python file, just run and go!

## Screenshots

### Gallery View
Browse images in a clean, responsive grid layout with folder navigation.

### Lightbox View
View full-size images with zoom, pan, and keyboard controls.

## Supported Image Formats

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- GIF (`.gif`)
- BMP (`.bmp`)
- WebP (`.webp`)
- SVG (`.svg`)
- ICO (`.ico`)

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/dedenbangkit/image-explorer.git
   cd image-explorer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install Flask>=2.3.0 Pillow>=10.0.0
   ```

## Usage

### Basic Usage

Run the script in your current directory:
```bash
python image_viewer.py
```

This will:
1. Scan the current directory and all subdirectories for images
2. Find an available port (starting from 5000)
3. Start a local web server and display the URL
4. You can then open the URL in your browser

### Specify a Directory

Browse images in a specific folder:
```bash
python image_viewer.py /path/to/your/images
```

### Examples

```bash
# View images in your Pictures folder
python image_viewer.py ~/Pictures

# View images in a project directory
python image_viewer.py /home/user/Projects/photography

# View images in current directory
python image_viewer.py .
```

### Stopping the Server

Press `Ctrl+C` in the terminal to stop the web server.

## How to Use the Interface

### Sidebar Navigation
- **Click folder names** to filter images by that folder (includes subfolders)
- **Toggle sidebar** using the ☰ button for more screen space
- **View image counts** - each folder shows how many images it contains

### Image Gallery
- **Click thumbnails** to open full-screen lightbox viewer
- **Hover thumbnails** for elevation effect
- **See file paths** under each thumbnail

### Lightbox Viewer
- **Click/Tap** - Close viewer or navigate
- **Arrow Keys** - Navigate between images
- **Escape** - Close viewer
- **Scroll/Pinch** - Zoom in/out
- **Drag** - Pan zoomed image

## Project Structure

```
image-explorer/
├── image_viewer.py      # Main application (single file!)
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── LICENSE             # GPL-3.0 license
└── .gitignore          # Git ignore rules
```

## Technical Details

### Built With

- **[Flask](https://flask.palletsprojects.com/)** - Lightweight web framework
- **[Pillow](https://python-pillow.org/)** - Image processing library (for reading dimensions)
- **[PhotoSwipe](https://photoswipe.com/)** - JavaScript lightbox library (loaded via CDN)

### How It Works

1. **Scanning** - Walks through directory tree using `os.walk()` to find all image files
2. **Metadata** - Reads image dimensions using Pillow to prevent stretching
3. **Structure** - Builds hierarchical folder tree for sidebar navigation
4. **Serving** - Flask serves the HTML interface and image files
5. **Filtering** - Client-side JavaScript handles folder filtering and sidebar toggling
6. **Viewing** - PhotoSwipe provides professional image viewing experience

### Performance

- Lazy loading for thumbnails
- Efficient folder tree structure
- Lightweight HTML/CSS/JS
- No database required
- Minimal memory footprint

## Configuration

All configuration is handled automatically, but you can modify these settings in `image_viewer.py`:

- **Port**: Change `port = 5000` in the `main()` function (image_viewer.py:317)
- **Image extensions**: Modify `IMAGE_EXTENSIONS` set (image_viewer.py:18)
- **Thumbnail size**: Adjust `.gallery-item img` height in CSS (image_viewer.py:180)
- **Grid columns**: Modify `grid-template-columns` in CSS (image_viewer.py:161)

## Troubleshooting

### Port Already in Use
The script automatically finds an available port starting from 5000. If ports 5000-5099 are all occupied, the script will show an error. You can modify the port range in the `find_available_port()` function if needed.

### Images Not Showing
- Check file extensions are supported
- Verify file permissions are readable
- Ensure images aren't corrupted

### Slow Loading
- Reduce image file sizes in source directory
- Check disk I/O performance
- Consider limiting folder depth

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [PhotoSwipe](https://photoswipe.com/) - Excellent JavaScript image gallery library
- [Flask](https://flask.palletsprojects.com/) - Micro web framework
- [Pillow](https://python-pillow.org/) - Python Imaging Library

## Author

**dedenbangkit**
- GitHub: [@dedenbangkit](https://github.com/dedenbangkit)

## Support

If you find this project helpful, please give it a ⭐ on GitHub!

---

**Note**: This is a local-only web application. It does not expose your images to the internet and only runs on your local machine.

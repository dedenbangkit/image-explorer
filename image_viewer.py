#!/usr/bin/env python3
"""
Simple Image Viewer - Scans folders recursively and displays images in a web browser
Usage: python image_viewer.py [folder_path]
"""

import os
import sys
import mimetypes
import socket
from pathlib import Path
from flask import Flask, render_template_string, send_from_directory
from PIL import Image

app = Flask(__name__)

# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico'}

# Global variable to store the base directory
BASE_DIR = None

# HTML template with PhotoSwipe library
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Viewer</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/photoswipe/5.3.8/photoswipe.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            margin: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 280px;
            background: white;
            border-right: 1px solid #ddd;
            display: flex;
            flex-direction: column;
            transition: margin-left 0.3s ease;
            position: relative;
        }
        .sidebar.collapsed {
            margin-left: -280px;
        }
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid #eee;
            background: #fafafa;
        }
        .sidebar-title {
            font-size: 14px;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        .sidebar-subtitle {
            font-size: 12px;
            color: #999;
        }
        .folder-tree {
            flex: 1;
            overflow-y: auto;
            padding: 10px 0;
        }
        .folder-item {
            padding: 8px 20px;
            cursor: pointer;
            font-size: 13px;
            color: #555;
            display: flex;
            align-items: center;
            transition: background 0.15s;
            user-select: none;
        }
        .folder-item:hover {
            background: #f0f0f0;
        }
        .folder-item.active {
            background: #e3f2fd;
            color: #1976d2;
            font-weight: 500;
        }
        .folder-icon {
            margin-right: 8px;
            font-size: 14px;
        }
        .folder-count {
            margin-left: auto;
            font-size: 11px;
            color: #999;
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 10px;
        }
        .folder-item.active .folder-count {
            background: #bbdefb;
            color: #1976d2;
        }

        /* Toggle button */
        .sidebar-toggle {
            position: absolute;
            right: -40px;
            top: 20px;
            width: 40px;
            height: 40px;
            background: white;
            border: 1px solid #ddd;
            border-left: none;
            border-radius: 0 8px 8px 0;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            color: #666;
            transition: background 0.15s;
        }
        .sidebar-toggle:hover {
            background: #f5f5f5;
        }

        /* Main content */
        .main-content {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .info {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .current-folder {
            color: #1976d2;
            font-weight: 500;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }
        .gallery-item {
            position: relative;
            cursor: pointer;
            overflow: hidden;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            background: white;
        }
        .gallery-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }
        .gallery-item.hidden {
            display: none;
        }
        .gallery-item img {
            width: 100%;
            height: 200px;
            object-fit: cover;
            display: block;
        }
        .image-info {
            padding: 10px;
            background: white;
        }
        .image-path {
            font-size: 11px;
            color: #999;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .pswp__dynamic-caption {
            background: rgba(0,0,0,0.75);
            color: white;
            padding: 10px 15px;
        }
        .no-images {
            text-align: center;
            color: #999;
            padding: 40px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-toggle" id="sidebarToggle">☰</div>
        <div class="sidebar-header">
            <div class="sidebar-title">Folders</div>
            <div class="sidebar-subtitle">{{ images|length }} total images</div>
        </div>
        <div class="folder-tree">
            {% for folder in folders %}
            <div class="folder-item {% if loop.first %}active{% endif %}"
                 data-folder="{{ folder.path }}"
                 style="padding-left: {{ 20 + folder.level * 20 }}px;">
                <span class="folder-icon">📁</span>
                <span class="folder-name">{{ folder.name }}</span>
                <span class="folder-count">{{ folder.image_count }}</span>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <h1>Image Viewer</h1>
        <div class="info">
            <strong>Base Folder:</strong> {{ base_path }}<br>
            <strong>Current Filter:</strong> <span class="current-folder" id="currentFolder">All Folders</span><br>
            <strong>Showing:</strong> <span id="imageCount">{{ images|length }}</span> image(s)
        </div>

        <div class="gallery" id="gallery">
            {% for img in images %}
            <a href="{{ img.url }}"
               data-pswp-width="{{ img.width }}"
               data-pswp-height="{{ img.height }}"
               data-folder="{{ img.folder }}"
               class="gallery-item"
               target="_blank">
                <img src="{{ img.url }}" alt="{{ img.name }}" loading="lazy">
                <div class="image-info">
                    <div class="image-path" title="{{ img.rel_path }}">{{ img.rel_path }}</div>
                </div>
            </a>
            {% endfor %}
        </div>
        <div class="no-images" id="noImages" style="display: none;">
            No images in this folder
        </div>
    </div>

    <script>
        // Sidebar toggle
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebarToggle');

        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            sidebarToggle.textContent = sidebar.classList.contains('collapsed') ? '☰' : '✕';
        });

        // Folder filtering
        const folderItems = document.querySelectorAll('.folder-item');
        const galleryItems = document.querySelectorAll('.gallery-item');
        const currentFolderEl = document.getElementById('currentFolder');
        const imageCountEl = document.getElementById('imageCount');
        const noImagesEl = document.getElementById('noImages');
        const galleryEl = document.getElementById('gallery');
        let currentFilter = '.';

        function filterImages(folderPath) {
            currentFilter = folderPath;
            let visibleCount = 0;

            galleryItems.forEach(item => {
                const itemFolder = item.getAttribute('data-folder');

                // Show if folder matches or is a subfolder
                const shouldShow = folderPath === '.' ||
                                   itemFolder === folderPath ||
                                   itemFolder.startsWith(folderPath + '/') ||
                                   (folderPath === '.' && itemFolder === '.');

                if (shouldShow) {
                    item.classList.remove('hidden');
                    visibleCount++;
                } else {
                    item.classList.add('hidden');
                }
            });

            imageCountEl.textContent = visibleCount;

            if (visibleCount === 0) {
                galleryEl.style.display = 'none';
                noImagesEl.style.display = 'block';
            } else {
                galleryEl.style.display = 'grid';
                noImagesEl.style.display = 'none';
            }
        }

        folderItems.forEach(item => {
            item.addEventListener('click', () => {
                // Update active state
                folderItems.forEach(f => f.classList.remove('active'));
                item.classList.add('active');

                // Get folder path and name
                const folderPath = item.getAttribute('data-folder');
                const folderName = item.querySelector('.folder-name').textContent;

                // Update current folder display
                currentFolderEl.textContent = folderPath === '.' ? 'All Folders' : folderName;

                // Filter images
                filterImages(folderPath);
            });
        });
    </script>

    <script type="module">
        import PhotoSwipeLightbox from 'https://cdnjs.cloudflare.com/ajax/libs/photoswipe/5.3.8/photoswipe-lightbox.esm.min.js';

        const lightbox = new PhotoSwipeLightbox({
            gallery: '#gallery',
            children: 'a:not(.hidden)',
            pswpModule: () => import('https://cdnjs.cloudflare.com/ajax/libs/photoswipe/5.3.8/photoswipe.esm.min.js'),
            padding: { top: 50, bottom: 50, left: 50, right: 50 },
            bgOpacity: 0.9,
            zoom: true,
        });

        lightbox.on('uiRegister', function() {
            lightbox.pswp.ui.registerElement({
                name: 'custom-caption',
                order: 9,
                isButton: false,
                appendTo: 'root',
                html: '',
                onInit: (el, pswp) => {
                    lightbox.pswp.on('change', () => {
                        const currSlideElement = lightbox.pswp.currSlide.data.element;
                        let captionHTML = '';
                        if (currSlideElement) {
                            const pathEl = currSlideElement.querySelector('.image-path');
                            if (pathEl) {
                                captionHTML = `
                                    <div class="pswp__dynamic-caption">
                                        ${pathEl.textContent}
                                    </div>
                                `;
                            }
                        }
                        el.innerHTML = captionHTML;
                    });
                }
            });
        });

        // Add scroll navigation
        lightbox.on('afterInit', () => {
            const pswp = lightbox.pswp;
            let scrollTimeout;

            const handleWheel = (e) => {
                // Check if zoomed in
                const currZoomLevel = pswp.currSlide.currZoomLevel || 1;
                const isZoomed = currZoomLevel > 1;

                // Only navigate if not zoomed in
                if (isZoomed) {
                    return;
                }

                e.preventDefault();
                e.stopPropagation();

                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    if (e.deltaY > 0) {
                        // Scroll down - next image
                        pswp.next();
                    } else if (e.deltaY < 0) {
                        // Scroll up - previous image
                        pswp.prev();
                    }
                }, 50);
            };

            // Add wheel event listener to the main element
            pswp.element.addEventListener('wheel', handleWheel, { passive: false });

            // Clean up on close
            pswp.on('destroy', () => {
                pswp.element.removeEventListener('wheel', handleWheel);
                clearTimeout(scrollTimeout);
            });
        });

        lightbox.init();

        // Re-initialize lightbox when filter changes
        document.querySelectorAll('.folder-item').forEach(item => {
            item.addEventListener('click', () => {
                setTimeout(() => {
                    lightbox.destroy();
                    lightbox.init();
                }, 100);
            });
        });
    </script>
</body>
</html>
'''


def build_folder_tree(directory):
    """Build a hierarchical folder tree structure"""
    base_path = Path(directory).resolve()
    folder_tree = {'name': base_path.name, 'path': '.', 'children': {}, 'image_count': 0}

    for root, dirs, files in os.walk(directory):
        dirs.sort()
        files.sort()

        # Count images in this folder
        image_count = sum(1 for f in files if Path(f).suffix.lower() in IMAGE_EXTENSIONS)

        if root == str(base_path):
            folder_tree['image_count'] = image_count
        else:
            rel_path = Path(root).relative_to(base_path)
            parts = rel_path.parts

            # Navigate to the correct position in the tree
            current = folder_tree
            for part in parts:
                if part not in current['children']:
                    current['children'][part] = {'name': part, 'path': str(Path(current['path']) / part if current['path'] != '.' else part), 'children': {}, 'image_count': 0}
                current = current['children'][part]

            current['image_count'] = image_count

    return folder_tree


def folder_tree_to_list(tree, level=0):
    """Convert folder tree to a flat list for rendering"""
    result = []
    result.append({
        'name': tree['name'],
        'path': tree['path'],
        'level': level,
        'image_count': tree['image_count'],
        'has_children': len(tree['children']) > 0
    })

    for child_name in sorted(tree['children'].keys()):
        child = tree['children'][child_name]
        result.extend(folder_tree_to_list(child, level + 1))

    return result


def scan_images(directory):
    """Recursively scan directory for images"""
    images = []
    base_path = Path(directory).resolve()

    for root, dirs, files in os.walk(directory):
        # Sort for consistent ordering
        dirs.sort()
        files.sort()

        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()

            if ext in IMAGE_EXTENSIONS:
                rel_path = file_path.relative_to(base_path)
                folder_path = str(rel_path.parent) if rel_path.parent != Path('.') else '.'

                # Get image dimensions
                width, height = 800, 600  # Default values
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                except Exception:
                    # If we can't read the image, use defaults
                    pass

                images.append({
                    'name': file,
                    'path': str(file_path),
                    'rel_path': str(rel_path),
                    'folder': folder_path,
                    'url': f'/image/{rel_path}',
                    'width': width,
                    'height': height
                })

    return images


@app.route('/')
def index():
    """Main page showing image gallery"""
    images = scan_images(BASE_DIR)
    folder_tree = build_folder_tree(BASE_DIR)
    folders = folder_tree_to_list(folder_tree)
    return render_template_string(
        HTML_TEMPLATE,
        images=images,
        folders=folders,
        base_path=BASE_DIR
    )


@app.route('/image/<path:filepath>')
def serve_image(filepath):
    """Serve image files"""
    full_path = Path(BASE_DIR) / filepath
    directory = str(full_path.parent)
    filename = full_path.name
    return send_from_directory(directory, filename)


def find_available_port(start_port=5000, max_port=5100):
    """Find an available port starting from start_port"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available ports found between {start_port} and {max_port}")


def main():
    global BASE_DIR

    # Get directory from command line argument or use current directory
    if len(sys.argv) > 1:
        BASE_DIR = sys.argv[1]
    else:
        BASE_DIR = os.getcwd()

    # Validate directory
    if not os.path.isdir(BASE_DIR):
        print(f"Error: '{BASE_DIR}' is not a valid directory")
        sys.exit(1)

    BASE_DIR = str(Path(BASE_DIR).resolve())

    # Count images
    images = scan_images(BASE_DIR)
    print(f"\n{'='*60}")
    print(f"Image Viewer")
    print(f"{'='*60}")
    print(f"Scanning: {BASE_DIR}")
    print(f"Found: {len(images)} image(s)")
    print(f"{'='*60}\n")

    if len(images) == 0:
        print("No images found in the directory.")
        print(f"Supported formats: {', '.join(sorted(IMAGE_EXTENSIONS))}")
        sys.exit(0)

    # Find available port
    try:
        port = find_available_port()
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Display server info
    print(f"Server running at: http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop\n")

    # Run Flask app
    try:
        app.run(host='127.0.0.1', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)


if __name__ == '__main__':
    main()

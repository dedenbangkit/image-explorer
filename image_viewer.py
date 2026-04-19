#!/usr/bin/env python3
"""
Simple Image Viewer - Scans folders recursively and displays images in a web browser
Usage: python image_viewer.py [folder_path]
"""

import os
import sys
import mimetypes
import socket
import subprocess
import json
from pathlib import Path
from flask import Flask, render_template_string, send_from_directory, jsonify, request
from PIL import Image

app = Flask(__name__)

# Supported image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico'}

# Supported video extensions
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi', '.mkv', '.m4v', '.ogv'}

# All supported media extensions
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

# Global variable to store the base directory
BASE_DIR = None

# Config paths from config.json
CONFIG_PATHS = []
CURRENT_PATH_INDEX = 0

# Cached data (populated at startup)
CACHED_MEDIA = None
CACHED_FOLDERS = None

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
        .gallery-item img,
        .gallery-item video {
            width: 100%;
            height: 200px;
            object-fit: cover;
            display: block;
        }
        .gallery-item .video-thumbnail {
            position: relative;
        }
        .gallery-item .play-icon {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 60px;
            height: 60px;
            background: rgba(0,0,0,0.7);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: none;
        }
        .gallery-item .play-icon::after {
            content: '';
            width: 0;
            height: 0;
            border-left: 20px solid white;
            border-top: 12px solid transparent;
            border-bottom: 12px solid transparent;
            margin-left: 5px;
        }
        .video-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.95);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }
        .video-modal.active {
            display: flex;
        }
        .video-modal video {
            max-width: 90%;
            max-height: 90%;
        }
        .video-modal .close-btn {
            position: absolute;
            top: 20px;
            right: 30px;
            font-size: 40px;
            color: white;
            cursor: pointer;
            z-index: 2001;
        }
        .video-modal .nav-btn {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            font-size: 50px;
            color: white;
            cursor: pointer;
            padding: 20px;
            user-select: none;
        }
        .video-modal .nav-btn.prev { left: 20px; }
        .video-modal .nav-btn.next { right: 20px; }
        .video-modal .nav-btn:hover { color: #ccc; }
        .video-modal .video-caption {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.75);
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
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
        .path-selector {
            width: 100%;
            padding: 8px 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 13px;
            background: white;
            cursor: pointer;
            margin-top: 10px;
        }
        .path-selector:focus {
            outline: none;
            border-color: #1976d2;
        }
    </style>
</head>
<body>
    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-toggle" id="sidebarToggle">☰</div>
        <div class="sidebar-header">
            <div class="sidebar-title">Folders</div>
            <div class="sidebar-subtitle">{{ images|length }} total files</div>
            {% if config_paths|length > 1 %}
            <select class="path-selector" id="pathSelector">
                {% for p in config_paths %}
                <option value="{{ loop.index0 }}" {% if loop.index0 == current_path_index %}selected{% endif %}>{{ p.name }}</option>
                {% endfor %}
            </select>
            {% endif %}
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
        <div class="gallery" id="gallery">
            {% for img in images %}
            {% if img.is_video %}
            <div class="gallery-item video-item"
                 data-folder="{{ img.folder }}"
                 data-url="{{ img.url }}"
                 data-path="{{ img.rel_path }}"
                 data-width="{{ img.width }}"
                 data-height="{{ img.height }}">
                <div class="video-thumbnail">
                    <video src="{{ img.url }}" preload="metadata" muted></video>
                    <div class="play-icon"></div>
                </div>
                <div class="image-info">
                    <div class="image-path" title="{{ img.rel_path }}">{{ img.rel_path }}</div>
                </div>
            </div>
            {% else %}
            <a href="{{ img.url }}"
               data-pswp-width="{{ img.width }}"
               data-pswp-height="{{ img.height }}"
               data-folder="{{ img.folder }}"
               class="gallery-item image-item"
               target="_blank">
                <img src="{{ img.url }}" alt="{{ img.name }}" loading="lazy">
                <div class="image-info">
                    <div class="image-path" title="{{ img.rel_path }}">{{ img.rel_path }}</div>
                </div>
            </a>
            {% endif %}
            {% endfor %}
        </div>
        <div class="no-images" id="noImages" style="display: none;">
            No media in this folder
        </div>
    </div>

    <!-- Video Modal -->
    <div class="video-modal" id="videoModal">
        <span class="close-btn" id="closeVideo">&times;</span>
        <span class="nav-btn prev" id="prevVideo">&#10094;</span>
        <span class="nav-btn next" id="nextVideo">&#10095;</span>
        <video id="modalVideo" controls></video>
        <div class="video-caption" id="videoCaption"></div>
    </div>

    <script>
        // Sidebar toggle
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebarToggle');

        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            sidebarToggle.textContent = sidebar.classList.contains('collapsed') ? '☰' : '✕';
        });

        // Path selector
        const pathSelector = document.getElementById('pathSelector');
        if (pathSelector) {
            pathSelector.addEventListener('change', () => {
                window.location.href = '/switch/' + pathSelector.value;
            });
        }

        // Folder filtering
        const folderItems = document.querySelectorAll('.folder-item');
        const galleryItems = document.querySelectorAll('.gallery-item');
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

                // Get folder path
                const folderPath = item.getAttribute('data-folder');

                // Filter images
                filterImages(folderPath);
            });
        });

        // Video modal handling
        const videoModal = document.getElementById('videoModal');
        const modalVideo = document.getElementById('modalVideo');
        const videoCaption = document.getElementById('videoCaption');
        const closeVideo = document.getElementById('closeVideo');
        const prevVideo = document.getElementById('prevVideo');
        const nextVideo = document.getElementById('nextVideo');
        let currentVideoIndex = 0;
        let visibleVideos = [];

        function updateVisibleVideos() {
            visibleVideos = Array.from(document.querySelectorAll('.video-item:not(.hidden)'));
        }

        function openVideo(index) {
            updateVisibleVideos();
            if (visibleVideos.length === 0) return;

            currentVideoIndex = index;
            const videoItem = visibleVideos[index];
            const url = videoItem.getAttribute('data-url');
            const path = videoItem.getAttribute('data-path');

            modalVideo.src = url;
            videoCaption.textContent = path;
            videoModal.classList.add('active');
            document.body.style.overflow = 'hidden';

            // Update nav visibility
            prevVideo.style.display = currentVideoIndex > 0 ? 'block' : 'none';
            nextVideo.style.display = currentVideoIndex < visibleVideos.length - 1 ? 'block' : 'none';
        }

        function closeVideoModal() {
            videoModal.classList.remove('active');
            modalVideo.pause();
            modalVideo.src = '';
            document.body.style.overflow = '';
        }

        document.querySelectorAll('.video-item').forEach(item => {
            item.addEventListener('click', () => {
                updateVisibleVideos();
                const index = visibleVideos.indexOf(item);
                if (index >= 0) openVideo(index);
            });
        });

        closeVideo.addEventListener('click', closeVideoModal);

        prevVideo.addEventListener('click', () => {
            if (currentVideoIndex > 0) openVideo(currentVideoIndex - 1);
        });

        nextVideo.addEventListener('click', () => {
            if (currentVideoIndex < visibleVideos.length - 1) openVideo(currentVideoIndex + 1);
        });

        videoModal.addEventListener('click', (e) => {
            if (e.target === videoModal) closeVideoModal();
        });

        document.addEventListener('keydown', (e) => {
            if (!videoModal.classList.contains('active')) return;
            if (e.key === 'Escape') closeVideoModal();
            if (e.key === 'ArrowLeft' && currentVideoIndex > 0) openVideo(currentVideoIndex - 1);
            if (e.key === 'ArrowRight' && currentVideoIndex < visibleVideos.length - 1) openVideo(currentVideoIndex + 1);
        });

        // Scroll navigation for video modal
        let videoScrollTimeout;
        videoModal.addEventListener('wheel', (e) => {
            if (!videoModal.classList.contains('active')) return;
            e.preventDefault();
            clearTimeout(videoScrollTimeout);
            videoScrollTimeout = setTimeout(() => {
                if (e.deltaY > 0 && currentVideoIndex < visibleVideos.length - 1) {
                    openVideo(currentVideoIndex + 1);
                } else if (e.deltaY < 0 && currentVideoIndex > 0) {
                    openVideo(currentVideoIndex - 1);
                }
            }, 50);
        }, { passive: false });
    </script>

    <script type="module">
        import PhotoSwipeLightbox from 'https://cdnjs.cloudflare.com/ajax/libs/photoswipe/5.3.8/photoswipe-lightbox.esm.min.js';

        const lightbox = new PhotoSwipeLightbox({
            gallery: '#gallery',
            children: 'a.image-item:not(.hidden)',
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


def get_video_dimensions(file_path):
    """Get video dimensions using ffprobe"""
    try:
        result = subprocess.run(
            [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-select_streams', 'v:0', str(file_path)
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('streams'):
                stream = data['streams'][0]
                return stream.get('width', 800), stream.get('height', 600)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return 800, 600  # Default dimensions


def build_folder_tree(directory):
    """Build a hierarchical folder tree structure"""
    base_path = Path(directory).resolve()
    folder_tree = {'name': base_path.name, 'path': '.', 'children': {}, 'image_count': 0}

    for root, dirs, files in os.walk(directory):
        dirs.sort()
        files.sort()

        # Count media files in this folder
        image_count = sum(1 for f in files if Path(f).suffix.lower() in MEDIA_EXTENSIONS)

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


def scan_media(directory):
    """Recursively scan directory for images and videos"""
    media = []
    base_path = Path(directory).resolve()

    for root, dirs, files in os.walk(directory):
        # Sort for consistent ordering
        dirs.sort()
        files.sort()

        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()

            if ext in MEDIA_EXTENSIONS:
                rel_path = file_path.relative_to(base_path)
                folder_path = str(rel_path.parent) if rel_path.parent != Path('.') else '.'

                is_video = ext in VIDEO_EXTENSIONS

                # Get dimensions (skip for videos - use defaults)
                width, height = 800, 600  # Default values
                if not is_video:
                    try:
                        with Image.open(file_path) as img:
                            width, height = img.size
                    except Exception:
                        pass

                media.append({
                    'name': file,
                    'path': str(file_path),
                    'rel_path': str(rel_path),
                    'folder': folder_path,
                    'url': f'/media/{rel_path}',
                    'width': width,
                    'height': height,
                    'is_video': is_video,
                    'type': 'video' if is_video else 'image'
                })

    return media


@app.route('/')
def index():
    """Main page showing media gallery"""
    return render_template_string(
        HTML_TEMPLATE,
        images=CACHED_MEDIA,
        folders=CACHED_FOLDERS,
        config_paths=CONFIG_PATHS,
        current_path_index=CURRENT_PATH_INDEX
    )


@app.route('/switch/<int:path_index>')
def switch_path(path_index):
    """Switch to a different configured path"""
    global BASE_DIR, CACHED_MEDIA, CACHED_FOLDERS, CURRENT_PATH_INDEX

    if path_index < 0 or path_index >= len(CONFIG_PATHS):
        return "Invalid path index", 400

    CURRENT_PATH_INDEX = path_index
    path_config = CONFIG_PATHS[path_index]
    BASE_DIR = str(Path(path_config['path']).expanduser().resolve())

    # Re-scan the new path
    CACHED_MEDIA = scan_media(BASE_DIR)
    folder_tree = build_folder_tree(BASE_DIR)
    CACHED_FOLDERS = folder_tree_to_list(folder_tree)

    return index()


@app.route('/media/<path:filepath>')
def serve_media(filepath):
    """Serve image and video files"""
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


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / 'config.json'
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('paths', [])
    return []


def main():
    global BASE_DIR, CACHED_MEDIA, CACHED_FOLDERS, CONFIG_PATHS, CURRENT_PATH_INDEX

    # Load config
    CONFIG_PATHS = load_config()

    # Get directory from command line argument, config, or current directory
    if len(sys.argv) > 1:
        BASE_DIR = sys.argv[1]
    elif CONFIG_PATHS:
        BASE_DIR = CONFIG_PATHS[0]['path']
        CURRENT_PATH_INDEX = 0
    else:
        BASE_DIR = os.getcwd()

    # Expand ~ and resolve path
    BASE_DIR = str(Path(BASE_DIR).expanduser().resolve())

    # Validate directory
    if not os.path.isdir(BASE_DIR):
        print(f"Error: '{BASE_DIR}' is not a valid directory")
        sys.exit(1)

    # Scan and cache media files at startup
    print(f"\nScanning {BASE_DIR}...")
    CACHED_MEDIA = scan_media(BASE_DIR)
    folder_tree = build_folder_tree(BASE_DIR)
    CACHED_FOLDERS = folder_tree_to_list(folder_tree)

    image_count = sum(1 for m in CACHED_MEDIA if not m['is_video'])
    video_count = sum(1 for m in CACHED_MEDIA if m['is_video'])
    print(f"Found: {image_count} image(s), {video_count} video(s)")

    if len(CACHED_MEDIA) == 0:
        print("No media files found in the directory.")
        print(f"Supported image formats: {', '.join(sorted(IMAGE_EXTENSIONS))}")
        print(f"Supported video formats: {', '.join(sorted(VIDEO_EXTENSIONS))}")
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

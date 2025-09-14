"""
Static File Management and Optimization for Korean Reading Comprehension System
Handles CSS/JS minification, compression, caching, and Korean font optimization
"""

import os
import gzip
import hashlib
import json
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import time
from datetime import datetime, timedelta
import logging

from config.config import get_config
from utils.logging_config import get_logger

logger = get_logger(__name__)


class StaticFileOptimizer:
    """Optimizes static files for production deployment"""
    
    def __init__(self, static_dir: str = "/app/static"):
        self.static_dir = Path(static_dir)
        self.config = get_config()
        self.optimized_dir = self.static_dir / "optimized"
        self.cache_dir = self.static_dir / "cache"
        
        # Create directories
        self.optimized_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # File type configurations
        self.compressible_types = {
            '.css', '.js', '.html', '.json', '.xml', '.svg', '.txt',
            '.woff', '.woff2', '.ttf', '.eot'  # Include fonts for Korean support
        }
        
        self.minifiable_types = {
            '.css': self._minify_css,
            '.js': self._minify_js,
            '.html': self._minify_html
        }
        
        # Cache manifest for file versioning
        self.cache_manifest_file = self.static_dir / "cache_manifest.json"
        self.cache_manifest = self._load_cache_manifest()
    
    def _load_cache_manifest(self) -> Dict[str, Any]:
        """Load cache manifest from file"""
        if self.cache_manifest_file.exists():
            try:
                return json.loads(self.cache_manifest_file.read_text())
            except Exception as e:
                logger.warning(f"Failed to load cache manifest: {e}")
        
        return {
            "version": 1,
            "generated_at": datetime.now().isoformat(),
            "files": {}
        }
    
    def _save_cache_manifest(self):
        """Save cache manifest to file"""
        try:
            self.cache_manifest["generated_at"] = datetime.now().isoformat()
            self.cache_manifest_file.write_text(
                json.dumps(self.cache_manifest, indent=2)
            )
        except Exception as e:
            logger.error(f"Failed to save cache manifest: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()[:8]  # Use first 8 characters
    
    def _minify_css(self, content: str) -> str:
        """Minify CSS content"""
        try:
            # Remove comments
            import re
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            
            # Remove unnecessary whitespace
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r';\s*}', '}', content)
            content = re.sub(r'{\s*', '{', content)
            content = re.sub(r'}\s*', '}', content)
            content = re.sub(r':\s*', ':', content)
            content = re.sub(r';\s*', ';', content)
            
            return content.strip()
            
        except Exception as e:
            logger.warning(f"CSS minification failed: {e}")
            return content
    
    def _minify_js(self, content: str) -> str:
        """Minify JavaScript content"""
        try:
            # Simple JS minification (for production, consider using a proper minifier)
            import re
            
            # Remove single-line comments (but preserve URLs)
            content = re.sub(r'(?<!:)//.*$', '', content, flags=re.MULTILINE)
            
            # Remove multi-line comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            
            # Remove unnecessary whitespace
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r';\s*}', ';}', content)
            content = re.sub(r'{\s*', '{', content)
            content = re.sub(r'}\s*', '}', content)
            
            return content.strip()
            
        except Exception as e:
            logger.warning(f"JS minification failed: {e}")
            return content
    
    def _minify_html(self, content: str) -> str:
        """Minify HTML content"""
        try:
            import re
            
            # Remove HTML comments (but preserve conditional comments)
            content = re.sub(r'<!--(?!\[if).*?-->', '', content, flags=re.DOTALL)
            
            # Remove unnecessary whitespace between tags
            content = re.sub(r'>\s+<', '><', content)
            
            # Remove leading/trailing whitespace on lines
            content = re.sub(r'^\s+|\s+$', '', content, flags=re.MULTILINE)
            
            return content.strip()
            
        except Exception as e:
            logger.warning(f"HTML minification failed: {e}")
            return content
    
    def _compress_file(self, file_path: Path) -> Path:
        """Compress file using gzip"""
        compressed_path = self.cache_dir / f"{file_path.name}.gz"
        
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb', compresslevel=9) as f_out:
                    f_out.writelines(f_in)
            
            logger.debug(f"Compressed {file_path.name}: {file_path.stat().st_size} -> {compressed_path.stat().st_size} bytes")
            return compressed_path
            
        except Exception as e:
            logger.warning(f"Failed to compress {file_path}: {e}")
            return file_path
    
    def optimize_file(self, file_path: Path) -> Dict[str, Any]:
        """Optimize a single file"""
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return {}
        
        file_info = {
            "original_path": str(file_path),
            "original_size": file_path.stat().st_size,
            "optimized_path": str(file_path),
            "optimized_size": file_path.stat().st_size,
            "hash": self._calculate_file_hash(file_path),
            "compressed": False,
            "minified": False,
            "optimization_time": time.time()
        }
        
        # Check if file needs optimization
        file_hash = file_info["hash"]
        if file_path.suffix.lower() in self.minifiable_types:
            # Minify file
            try:
                content = file_path.read_text(encoding='utf-8')
                minified_content = self.minifiable_types[file_path.suffix.lower()](content)
                
                # Save minified version
                optimized_path = self.optimized_dir / f"{file_path.stem}_{file_hash}{file_path.suffix}"
                optimized_path.write_text(minified_content, encoding='utf-8')
                
                file_info.update({
                    "optimized_path": str(optimized_path),
                    "optimized_size": optimized_path.stat().st_size,
                    "minified": True
                })
                
                logger.info(f"Minified {file_path.name}: {file_info['original_size']} -> {file_info['optimized_size']} bytes")
                
            except Exception as e:
                logger.warning(f"Failed to minify {file_path}: {e}")
        
        # Compress file if it's compressible
        if file_path.suffix.lower() in self.compressible_types:
            optimized_path = Path(file_info["optimized_path"])
            compressed_path = self._compress_file(optimized_path)
            
            if compressed_path != optimized_path:
                file_info.update({
                    "compressed_path": str(compressed_path),
                    "compressed_size": compressed_path.stat().st_size,
                    "compressed": True
                })
        
        return file_info
    
    def optimize_directory(self, directory: Optional[Path] = None) -> Dict[str, Any]:
        """Optimize all files in a directory"""
        if directory is None:
            directory = self.static_dir
        
        optimization_results = {
            "started_at": datetime.now().isoformat(),
            "files_processed": 0,
            "total_original_size": 0,
            "total_optimized_size": 0,
            "files": {}
        }
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and not file_path.is_relative_to(self.optimized_dir) and not file_path.is_relative_to(self.cache_dir):
                file_info = self.optimize_file(file_path)
                
                if file_info:
                    relative_path = str(file_path.relative_to(self.static_dir))
                    optimization_results["files"][relative_path] = file_info
                    optimization_results["files_processed"] += 1
                    optimization_results["total_original_size"] += file_info["original_size"]
                    optimization_results["total_optimized_size"] += file_info["optimized_size"]
        
        optimization_results["completed_at"] = datetime.now().isoformat()
        optimization_results["compression_ratio"] = (
            optimization_results["total_original_size"] / optimization_results["total_optimized_size"]
            if optimization_results["total_optimized_size"] > 0 else 1.0
        )
        
        # Update cache manifest
        self.cache_manifest["files"].update(optimization_results["files"])
        self._save_cache_manifest()
        
        logger.info(f"Optimized {optimization_results['files_processed']} files. "
                   f"Total size: {optimization_results['total_original_size']} -> "
                   f"{optimization_results['total_optimized_size']} bytes "
                   f"(ratio: {optimization_results['compression_ratio']:.2f})")
        
        return optimization_results


class KoreanFontManager:
    """Manages Korean font loading and optimization"""
    
    def __init__(self, static_dir: str = "/app/static"):
        self.static_dir = Path(static_dir)
        self.fonts_dir = self.static_dir / "fonts"
        self.fonts_dir.mkdir(parents=True, exist_ok=True)
        
        # Korean font configurations
        self.korean_fonts = {
            "noto_sans_kr": {
                "name": "Noto Sans KR",
                "weights": [100, 300, 400, 500, 700, 900],
                "display": "swap",
                "unicode_range": "U+0-10FFFF"
            },
            "malgun_gothic": {
                "name": "Malgun Gothic",
                "weights": [400, 700],
                "display": "swap",
                "fallback": ["Apple SD Gothic Neo", "sans-serif"]
            },
            "nanum_gothic": {
                "name": "NanumGothic",
                "weights": [400, 700, 800],
                "display": "swap",
                "unicode_range": "U+AC00-D7AF, U+1100-11FF, U+3130-318F"
            }
        }
    
    def generate_font_css(self) -> str:
        """Generate optimized CSS for Korean fonts"""
        css_parts = []
        
        # Add font preload hints
        css_parts.append("/* Korean Font Preload Hints */")
        
        for font_key, font_config in self.korean_fonts.items():
            font_name = font_config["name"]
            
            # Add @font-face declarations
            for weight in font_config["weights"]:
                css_parts.append(f"""
@font-face {{
    font-family: '{font_name}';
    font-style: normal;
    font-weight: {weight};
    font-display: {font_config.get('display', 'swap')};
    src: url('/static/fonts/{font_key}-{weight}.woff2') format('woff2'),
         url('/static/fonts/{font_key}-{weight}.woff') format('woff');
    {f"unicode-range: {font_config['unicode_range']};" if 'unicode_range' in font_config else ""}
}}""")
        
        # Add optimized font stack
        css_parts.append("""
/* Optimized Korean Font Stack */
.korean-text, body {{
    font-family: 'Noto Sans KR', 'Malgun Gothic', 'NanumGothic', 
                 'Apple SD Gothic Neo', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-feature-settings: 'kern' 1;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

/* Font loading optimization */
.font-loading {{
    font-family: system-ui, -apple-system, sans-serif;
}}

.font-loaded {{
    font-family: 'Noto Sans KR', 'Malgun Gothic', 'NanumGothic', 
                 'Apple SD Gothic Neo', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}}

/* Performance optimizations for Korean text */
.korean-content {{
    word-break: keep-all;
    overflow-wrap: break-word;
    line-height: 1.6;
    letter-spacing: -0.02em;
}}

/* Reading-specific optimizations */
.reading-passage {{
    font-size: 16px;
    line-height: 1.8;
    max-width: 65ch;
    margin: 0 auto;
}}

.question-text {{
    font-size: 15px;
    line-height: 1.6;
    font-weight: 500;
}}

@media (max-width: 768px) {{
    .reading-passage {{
        font-size: 14px;
        line-height: 1.7;
        padding: 0 16px;
    }}
    
    .question-text {{
        font-size: 14px;
    }}
}}""")
        
        return "\n".join(css_parts)
    
    def generate_font_loading_script(self) -> str:
        """Generate JavaScript for optimized font loading"""
        return """
// Korean Font Loading Optimization
(function() {
    'use strict';
    
    // Check if fonts are already loaded
    if (sessionStorage.getItem('korean-fonts-loaded')) {
        document.documentElement.classList.add('font-loaded');
        return;
    }
    
    // Add loading class
    document.documentElement.classList.add('font-loading');
    
    // Font loading with timeout
    function loadKoreanFonts() {
        const fontPromises = [
            new FontFace('Noto Sans KR', 'url(/static/fonts/noto_sans_kr-400.woff2)', {
                weight: '400',
                display: 'swap'
            }).load(),
            new FontFace('Malgun Gothic', 'url(/static/fonts/malgun_gothic-400.woff2)', {
                weight: '400',
                display: 'swap'
            }).load()
        ];
        
        Promise.allSettled(fontPromises).then(results => {
            const loadedFonts = results.filter(result => result.status === 'fulfilled');
            
            if (loadedFonts.length > 0) {
                // Add loaded fonts to document
                loadedFonts.forEach(result => {
                    document.fonts.add(result.value);
                });
                
                // Update classes
                document.documentElement.classList.remove('font-loading');
                document.documentElement.classList.add('font-loaded');
                
                // Cache success
                sessionStorage.setItem('korean-fonts-loaded', 'true');
                
                console.log(`Loaded ${loadedFonts.length} Korean fonts`);
            } else {
                // Fallback to system fonts
                document.documentElement.classList.remove('font-loading');
                console.warn('Failed to load Korean fonts, using fallback');
            }
        });
    }
    
    // Load fonts when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadKoreanFonts);
    } else {
        loadKoreanFonts();
    }
    
    // Preload critical fonts
    const preloadLink = document.createElement('link');
    preloadLink.rel = 'preload';
    preloadLink.href = '/static/fonts/noto_sans_kr-400.woff2';
    preloadLink.as = 'font';
    preloadLink.type = 'font/woff2';
    preloadLink.crossOrigin = 'anonymous';
    document.head.appendChild(preloadLink);
})();
"""


class CacheManager:
    """Manages static file caching and cache busting"""
    
    def __init__(self, static_dir: str = "/app/static"):
        self.static_dir = Path(static_dir)
        self.config = get_config()
        
        # Cache settings
        self.cache_ttl = self.config.static_file_cache_ttl if hasattr(self.config, 'static_file_cache_ttl') else 86400
        self.cache_headers = {
            '.css': {'Cache-Control': f'max-age={self.cache_ttl}, public', 'Content-Type': 'text/css'},
            '.js': {'Cache-Control': f'max-age={self.cache_ttl}, public', 'Content-Type': 'application/javascript'},
            '.woff2': {'Cache-Control': f'max-age={self.cache_ttl * 7}, public', 'Content-Type': 'font/woff2'},
            '.woff': {'Cache-Control': f'max-age={self.cache_ttl * 7}, public', 'Content-Type': 'font/woff'},
            '.png': {'Cache-Control': f'max-age={self.cache_ttl}, public', 'Content-Type': 'image/png'},
            '.jpg': {'Cache-Control': f'max-age={self.cache_ttl}, public', 'Content-Type': 'image/jpeg'},
            '.jpeg': {'Cache-Control': f'max-age={self.cache_ttl}, public', 'Content-Type': 'image/jpeg'},
            '.svg': {'Cache-Control': f'max-age={self.cache_ttl}, public', 'Content-Type': 'image/svg+xml'},
        }
    
    def get_cache_headers(self, file_path: str) -> Dict[str, str]:
        """Get appropriate cache headers for file"""
        file_ext = Path(file_path).suffix.lower()
        headers = self.cache_headers.get(file_ext, {
            'Cache-Control': f'max-age={self.cache_ttl}, public'
        })
        
        # Add CORS headers for fonts
        if file_ext in ['.woff', '.woff2', '.ttf', '.eot']:
            headers['Access-Control-Allow-Origin'] = '*'
        
        return headers
    
    def get_versioned_url(self, file_path: str, file_hash: Optional[str] = None) -> str:
        """Get versioned URL for cache busting"""
        if not file_hash:
            full_path = self.static_dir / file_path.lstrip('/')
            if full_path.exists():
                file_hash = hashlib.md5(full_path.read_bytes()).hexdigest()[:8]
            else:
                file_hash = "unknown"
        
        return f"/static/{file_path}?v={file_hash}"


class StaticFileManager:
    """Main static file management system"""
    
    def __init__(self, static_dir: str = "/app/static"):
        self.static_dir = Path(static_dir)
        self.optimizer = StaticFileOptimizer(static_dir)
        self.font_manager = KoreanFontManager(static_dir)
        self.cache_manager = CacheManager(static_dir)
        
        logger.info(f"Static file manager initialized: {static_dir}")
    
    def optimize_all_files(self) -> Dict[str, Any]:
        """Optimize all static files"""
        return self.optimizer.optimize_directory()
    
    def setup_korean_fonts(self) -> bool:
        """Setup Korean font CSS and loading scripts"""
        try:
            # Generate font CSS
            font_css = self.font_manager.generate_font_css()
            css_file = self.static_dir / "css" / "korean-fonts.css"
            css_file.parent.mkdir(parents=True, exist_ok=True)
            css_file.write_text(font_css, encoding='utf-8')
            
            # Generate font loading script
            font_script = self.font_manager.generate_font_loading_script()
            js_file = self.static_dir / "js" / "font-loader.js"
            js_file.parent.mkdir(parents=True, exist_ok=True)
            js_file.write_text(font_script, encoding='utf-8')
            
            logger.info("Korean fonts CSS and JS generated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Korean fonts: {e}")
            return False
    
    def create_manifest(self) -> Dict[str, Any]:
        """Create asset manifest for template rendering"""
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "assets": {}
        }
        
        # Process CSS files
        css_dir = self.static_dir / "css"
        if css_dir.exists():
            for css_file in css_dir.glob("*.css"):
                relative_path = str(css_file.relative_to(self.static_dir))
                file_hash = self.optimizer._calculate_file_hash(css_file)
                manifest["assets"][relative_path] = {
                    "url": self.cache_manager.get_versioned_url(relative_path, file_hash),
                    "hash": file_hash,
                    "size": css_file.stat().st_size
                }
        
        # Process JS files
        js_dir = self.static_dir / "js"
        if js_dir.exists():
            for js_file in js_dir.glob("*.js"):
                relative_path = str(js_file.relative_to(self.static_dir))
                file_hash = self.optimizer._calculate_file_hash(js_file)
                manifest["assets"][relative_path] = {
                    "url": self.cache_manager.get_versioned_url(relative_path, file_hash),
                    "hash": file_hash,
                    "size": js_file.stat().st_size
                }
        
        # Save manifest
        manifest_file = self.static_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        
        return manifest
    
    def prepare_for_production(self) -> Dict[str, Any]:
        """Prepare all static files for production deployment"""
        logger.info("Preparing static files for production...")
        
        results = {
            "started_at": datetime.now().isoformat(),
            "steps": {}
        }
        
        # Step 1: Setup Korean fonts
        results["steps"]["korean_fonts"] = self.setup_korean_fonts()
        
        # Step 2: Optimize all files
        results["steps"]["optimization"] = self.optimize_all_files()
        
        # Step 3: Create manifest
        results["steps"]["manifest"] = self.create_manifest()
        
        results["completed_at"] = datetime.now().isoformat()
        results["success"] = all(
            step for step in results["steps"].values()
            if isinstance(step, bool)
        )
        
        logger.info(f"Static file preparation completed. Success: {results['success']}")
        return results


# Global static file manager
_static_manager = None

def get_static_manager() -> StaticFileManager:
    """Get global static file manager"""
    global _static_manager
    if _static_manager is None:
        _static_manager = StaticFileManager()
    return _static_manager


def prepare_static_files():
    """Prepare static files for production - convenience function"""
    return get_static_manager().prepare_for_production()


if __name__ == "__main__":
    # Test static file management
    manager = get_static_manager()
    
    # Setup Korean fonts
    manager.setup_korean_fonts()
    
    # Optimize files
    optimization_results = manager.optimize_all_files()
    print(f"Optimization results: {optimization_results}")
    
    # Create manifest
    manifest = manager.create_manifest()
    print(f"Asset manifest created with {len(manifest['assets'])} assets")
    
    print("Static file management test completed")
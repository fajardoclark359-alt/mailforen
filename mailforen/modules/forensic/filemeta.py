from datetime import datetime
from pathlib import Path
from typing import Any

from ...core.logger import logger


class FileMetaExtractor:
    """Extract metadata from files"""
    
    def extract(self, file_path: Path) -> dict[str, Any]:
        """Extract file metadata"""
        try:
            if not file_path.exists():
                return {"error": "File not found"}
            
            stat = file_path.stat()
            results = {
                "filename": file_path.name,
                "path": str(file_path.absolute()),
                "size_bytes": stat.st_size,
                "size_human": self.human_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "extension": file_path.suffix.lower()
            }
            
            # Try to extract EXIF for images
            if file_path.suffix.lower() in ['.jpg', '.jpeg', '.tiff', '.tif']:
                try:
                    import exifread
                    with open(file_path, 'rb') as f:
                        tags = exifread.process_file(f)
                    exif_data = {}
                    for tag in tags:
                        if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                            exif_data[tag] = str(tags[tag])
                    if exif_data:
                        results["exif"] = exif_data
                except Exception as e:
                    logger.debug(f"EXIF extraction failed: {e}")
            
            return results
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {"error": str(e)}
    
    def human_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

file_meta = FileMetaExtractor()

export interface ExifLocation {
  latitude: number;
  longitude: number;
}

/**
 * Extract GPS coordinates from image EXIF metadata before any resizing or compression.
 * Uses dynamic import so exifr is only loaded on demand when a photo is selected.
 */
export async function extractExifGps(file: File): Promise<ExifLocation | null> {
  try {
    const exifr = (await import('exifr')).default;
    const output = await exifr.gps(file);
    if (output && typeof output.latitude === 'number' && typeof output.longitude === 'number') {
      return {
        latitude: output.latitude,
        longitude: output.longitude,
      };
    }
  } catch (err) {
    console.warn('Could not extract EXIF GPS data from file:', err);
  }
  return null;
}

/**
 * Resize image to maximum target dimension (default 1600px) and convert to WebP format.
 */
export async function compressAndConvertToWebP(
  file: File,
  maxDimension = 1600,
  quality = 0.85
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = () => {
      const img = new Image();
      img.onerror = reject;
      img.onload = () => {
        let width = img.width;
        let height = img.height;

        // Scale down if either dimension exceeds maxDimension
        if (width > maxDimension || height > maxDimension) {
          if (width > height) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          } else {
            width = Math.round((width * maxDimension) / height);
            height = maxDimension;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Canvas 2D context not available'));
          return;
        }

        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob);
            } else {
              reject(new Error('Canvas toBlob WebP conversion failed'));
            }
          },
          'image/webp',
          quality
        );
      };
      img.src = reader.result as string;
    };
    reader.readAsDataURL(file);
  });
}


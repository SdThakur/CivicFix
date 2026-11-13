// Google Maps JavaScript API Loader with Places Library
declare const google: any;

const GOOGLE_MAPS_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || '';

export function isGoogleMapsConfigured(): boolean {
  return Boolean(
    GOOGLE_MAPS_API_KEY && 
    GOOGLE_MAPS_API_KEY.trim().length > 5 && 
    !GOOGLE_MAPS_API_KEY.includes('your_google_maps')
  );
}

let loadPromise: Promise<any> | null = null;

export function loadGoogleMaps(): Promise<any> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Google Maps can only be loaded in the browser.'));
  }

  if ((window as any).google && (window as any).google.maps) {
    return Promise.resolve((window as any).google);
  }

  // Prevent unauthenticated API requests that trigger console quota warnings
  if (!isGoogleMapsConfigured()) {
    return Promise.reject(new Error('Google Maps API key is not configured or unverified.'));
  }

  if (loadPromise) {
    return loadPromise;
  }

  loadPromise = new Promise((resolve, reject) => {
    const existingScript = document.querySelector('script[src*="maps.googleapis.com/maps/api/js"]');
    if (existingScript) {
      existingScript.addEventListener('load', () => resolve((window as any).google));
      existingScript.addEventListener('error', (e) => reject(e));
      return;
    }

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places`;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      if ((window as any).google && (window as any).google.maps) {
        resolve((window as any).google);
      } else {
        reject(new Error('Google Maps API failed to initialize.'));
      }
    };
    script.onerror = (err) => reject(err);
    document.head.appendChild(script);
  });

  return loadPromise;
}

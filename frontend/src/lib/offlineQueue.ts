/**
 * Native IndexedDB Offline Draft & Upload Queue Management
 */

const DB_NAME = 'civicfix_offline_db';
const DB_VERSION = 1;
const STORE_DRAFTS = 'report_drafts';
const STORE_QUEUE = 'queued_uploads';

export interface OfflineDraft {
  id: string;
  photoBlob: Blob;
  lat: number;
  lng: number;
  address: string;
  isApproximate: boolean;
  category: string;
  description: string;
  updatedAt: string;
}

export interface QueuedUpload {
  id: string;
  userId: string;
  imageBlob: Blob;
  lat: number;
  lng: number;
  description: string;
  category: string;
  queuedAt: string;
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.indexedDB) {
      reject(new Error('IndexedDB not supported in this environment'));
      return;
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_DRAFTS)) {
        db.createObjectStore(STORE_DRAFTS, { keyPath: 'id' });
      }
      if (!db.objectStoreNames.contains(STORE_QUEUE)) {
        db.createObjectStore(STORE_QUEUE, { keyPath: 'id' });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

// ─── DRAFT STORAGE ────────────────────────────────────────────────────────────
export async function saveDraftToIndexedDb(draft: OfflineDraft): Promise<void> {
  try {
    const db = await openDatabase();
    const tx = db.transaction(STORE_DRAFTS, 'readwrite');
    tx.objectStore(STORE_DRAFTS).put(draft);
    return new Promise((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (err) {
    console.warn('Could not save draft to IndexedDB:', err);
  }
}

export async function getLatestDraftFromIndexedDb(): Promise<OfflineDraft | null> {
  try {
    const db = await openDatabase();
    const tx = db.transaction(STORE_DRAFTS, 'readonly');
    const store = tx.objectStore(STORE_DRAFTS);
    const req = store.getAll();
    return new Promise((resolve) => {
      req.onsuccess = () => {
        const drafts = req.result as OfflineDraft[];
        if (!drafts || drafts.length === 0) {
          resolve(null);
        } else {
          drafts.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
          resolve(drafts[0]);
        }
      };
      req.onerror = () => resolve(null);
    });
  } catch {
    return null;
  }
}

export async function clearDraftFromIndexedDb(id: string): Promise<void> {
  try {
    const db = await openDatabase();
    const tx = db.transaction(STORE_DRAFTS, 'readwrite');
    tx.objectStore(STORE_DRAFTS).delete(id);
  } catch (err) {
    console.warn('Could not clear draft from IndexedDB:', err);
  }
}

// ─── OFFLINE UPLOAD QUEUE ─────────────────────────────────────────────────────
export async function enqueueOfflineUpload(item: QueuedUpload): Promise<void> {
  try {
    const db = await openDatabase();
    const tx = db.transaction(STORE_QUEUE, 'readwrite');
    tx.objectStore(STORE_QUEUE).put(item);
  } catch (err) {
    console.warn('Could not enqueue offline upload:', err);
  }
}

export async function getQueuedUploads(): Promise<QueuedUpload[]> {
  try {
    const db = await openDatabase();
    const tx = db.transaction(STORE_QUEUE, 'readonly');
    const req = tx.objectStore(STORE_QUEUE).getAll();
    return new Promise((resolve) => {
      req.onsuccess = () => resolve((req.result as QueuedUpload[]) || []);
      req.onerror = () => resolve([]);
    });
  } catch {
    return [];
  }
}

export async function removeQueuedUpload(id: string): Promise<void> {
  try {
    const db = await openDatabase();
    const tx = db.transaction(STORE_QUEUE, 'readwrite');
    tx.objectStore(STORE_QUEUE).delete(id);
  } catch (err) {
    console.warn('Could not remove queued upload:', err);
  }
}


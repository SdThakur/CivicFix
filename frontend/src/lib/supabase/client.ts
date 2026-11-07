import { createBrowserClient } from '@supabase/ssr';
import { Database } from '@/types/supabase';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://tywmyjecafmpufdfxbus.supabase.co';
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'sb_publishable_dSoVH6SAgzYJ7dWeo_drOg_UCcqNmuw';

let client: ReturnType<typeof createBrowserClient<Database>> | null = null;

export function getSupabaseBrowserClient() {
  if (typeof window === 'undefined') {
    return createBrowserClient<Database>(supabaseUrl, supabaseKey);
  }

  if (!client) {
    client = createBrowserClient<Database>(supabaseUrl, supabaseKey);
  }

  return client;
}

export const supabase = getSupabaseBrowserClient();


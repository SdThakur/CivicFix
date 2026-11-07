'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { getSupabaseBrowserClient } from '@/lib/supabase/client';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  isAnonymous: boolean;
  signInAnonymously: () => Promise<{ user: User | null; error: any }>;
  signInWithEmail: (email: string, password: string) => Promise<{ error: any }>;
  signUpWithEmail: (email: string, password: string, fullName?: string) => Promise<{ error: any }>;
  upgradeAnonymousAccount: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  isAnonymous: false,
  signInAnonymously: async () => ({ user: null, error: null }),
  signInWithEmail: async () => ({ error: null }),
  signUpWithEmail: async () => ({ error: null }),
  upgradeAnonymousAccount: async () => ({ error: null }),
  signOut: async () => {},
});

export function SupabaseAuthProvider({ children }: { children: React.ReactNode }) {
  const supabase = getSupabaseBrowserClient();
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Initial session retrieval
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // 2. Auth state subscription
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [supabase]);

  const isAnonymous = Boolean(user?.is_anonymous);

  const signInAnonymously = async () => {
    try {
      const { data, error } = await supabase.auth.signInAnonymously();
      return { user: data.user, error };
    } catch (err: any) {
      return { user: null, error: err };
    }
  };

  const signInWithEmail = async (email: string, password: string) => {
    try {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      return { error };
    } catch (err: any) {
      return { error: err };
    }
  };

  const signUpWithEmail = async (email: string, password: string, fullName?: string) => {
    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: fullName || 'Citizen', role: 'CITIZEN' },
        },
      });
      return { error };
    } catch (err: any) {
      return { error: err };
    }
  };

  const upgradeAnonymousAccount = async (email: string, password: string) => {
    try {
      // Link email and password to the current anonymous session so report history is preserved
      const { error } = await supabase.auth.updateUser({ email, password });
      return { error };
    } catch (err: any) {
      return { error: err };
    }
  };

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        isAnonymous,
        signInAnonymously,
        signInWithEmail,
        signUpWithEmail,
        upgradeAnonymousAccount,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}


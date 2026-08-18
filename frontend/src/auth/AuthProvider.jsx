import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { api } from '../lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [role, setRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const [profileError, setProfileError] = useState(null);

  useEffect(() => {
    let mounted = true;

    const fetchProfileAndRole = async () => {
      try {
        setProfileError(null);
        const profileData = await api.get('/users/me/');
        if (!mounted) return;
        setProfile(profileData);
        
        const roleData = await api.get('/users/me/role/');
        if (!mounted) return;
        setRole(roleData.role);
      } catch (error) {
        if (!mounted) return;
        console.error('Failed to fetch profile or role:', error);
        setProfileError(error.data?.detail || error.message || 'Failed to load profile');
        
        if (error.status === 401) {
          await supabase.auth.signOut();
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };

    // Use onAuthStateChange as the single source of truth to avoid race conditions.
    // It fires immediately with INITIAL_SESSION if a session exists.
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      if (!mounted) return;
      
      setSession(currentSession);
      setUser(currentSession?.user ?? null);
      
      if (currentSession) {
        // If we don't have a profile yet, or the user changed, fetch it
        setLoading(true);
        fetchProfileAndRole();
      } else {
        setProfile(null);
        setRole(null);
        setProfileError(null);
        setLoading(false);
      }
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  const signIn = async (email, password) => {
    setLoading(true);
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      setLoading(false);
      throw error;
    }
    return data;
  };

  const signOut = async () => {
    setLoading(true);
    await supabase.auth.signOut();
    setSession(null);
    setUser(null);
    setProfile(null);
    setRole(null);
    setProfileError(null);
    setLoading(false);
  };

  const value = {
    session,
    user,
    profile,
    role,
    loading,
    profileError,
    signIn,
    signOut,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

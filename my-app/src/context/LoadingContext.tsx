import { createContext, useContext, useState } from 'react';

interface LoadingContextType {
    loading: boolean;
    setLoading: (value: boolean) => void;
}

const LoadingContext = createContext<LoadingContextType | null>(null);

export function LoadingProvider({ children }: { children: React.ReactNode }) {
    const [loading, setLoading] = useState(false);

    return (
        <LoadingContext.Provider value={{ loading, setLoading }}>
            {children}
        </LoadingContext.Provider>
    );
}

export function useLoading() {
    const ctx = useContext(LoadingContext);
    if (!ctx) throw new Error('useLoading must be used within a LoadingProvider');
    return ctx;
}

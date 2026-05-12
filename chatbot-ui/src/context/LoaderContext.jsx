/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState } from 'react';

const LoaderContext = createContext();

export const LoaderProvider = ({ children }) => {
    const [isLoading, setIsLoading] = useState(false);

    return (
        <LoaderContext.Provider value={{ isLoading, setIsLoading }}>
            {children}
            {isLoading && (
                <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/30 backdrop-blur-sm">
                    <div className="w-12 h-12 rounded-full border-4 border-white/20 border-t-white animate-spin shadow-xl" />
                </div>
            )}
        </LoaderContext.Provider>
    );
};

export const useLoader = () => useContext(LoaderContext);
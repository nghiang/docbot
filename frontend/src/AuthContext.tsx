import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import type { User } from "./types";
import { getMe, login as apiLogin, logout as apiLogout, register as apiRegister, getAuthToken } from "./api";
import type { LoginRequest, RegisterRequest } from "./types";

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (data: LoginRequest) => Promise<void>;
    register: (data: RegisterRequest) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check for existing token on mount
    useEffect(() => {
        const checkAuth = async () => {
            const token = getAuthToken();
            if (token) {
                try {
                    const userData = await getMe();
                    setUser(userData);
                } catch {
                    // Token invalid, clear it
                    apiLogout();
                }
            }
            setIsLoading(false);
        };
        checkAuth();
    }, []);

    const login = useCallback(async (data: LoginRequest) => {
        await apiLogin(data);
        const userData = await getMe();
        setUser(userData);
    }, []);

    const register = useCallback(async (data: RegisterRequest) => {
        await apiRegister(data);
        // Auto-login after register
        await apiLogin({ email: data.email, password: data.password });
        const userData = await getMe();
        setUser(userData);
    }, []);

    const logout = useCallback(() => {
        apiLogout();
        setUser(null);
    }, []);

    return (
        <AuthContext.Provider
            value={{
                user,
                isLoading,
                isAuthenticated: !!user,
                login,
                register,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}

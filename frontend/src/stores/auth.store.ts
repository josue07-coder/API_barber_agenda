import { create } from "zustand";
import { TOKEN_STORAGE_KEY } from "@/lib/api";
import { getMe, login as loginRequest, type LoginInput } from "@/services/auth.api";
import type { User } from "@/types/api";

type AuthState = {
  token: string | null;
  user: User | null;
  isBootstrapping: boolean;
  login: (input: LoginInput) => Promise<User>;
  bootstrap: () => Promise<void>;
  logout: () => void;
};

export const useAuthStore = create<AuthState>((set, get) => ({
  token: window.localStorage.getItem(TOKEN_STORAGE_KEY),
  user: null,
  isBootstrapping: false,

  async login(input) {
    const token = await loginRequest(input);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token.access_token);
    set({ token: token.access_token });
    const user = await getMe();
    set({ user });
    return user;
  },

  async bootstrap() {
    if (!get().token || get().user) return;
    set({ isBootstrapping: true });
    try {
      const user = await getMe();
      set({ user });
    } catch {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
      set({ token: null, user: null });
    } finally {
      set({ isBootstrapping: false });
    }
  },

  logout() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    set({ token: null, user: null });
  }
}));

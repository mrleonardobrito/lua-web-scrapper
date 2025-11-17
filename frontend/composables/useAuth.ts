import { useToast } from "vue-toast-notification";
import { useApi } from "./useApi";

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_superuser: boolean;
}

export const useAuth = () => {
  const user = ref<User | null>(null);
  const isAuthenticated = ref(false);
  const isLoading = ref(false);
  const { get, post, redirect, clearCsrfToken } = useApi();
  const toast = useToast();

  const checkAuth = async (silent = false) => {
    isLoading.value = true;
    try {
      const data = await get<User>(
        "/api/auth/user/",
        {},
        { showLog: false, logError: false }
      );
      user.value = data;
      isAuthenticated.value = !!data;
      return true;
    } catch (error: any) {
      user.value = null;
      isAuthenticated.value = false;

      if (!silent && error?.status !== 401 && error?.status !== 403) {
        toast.error("Erro ao verificar autenticação");
      }
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const login = () => {
    redirect("/api/auth/google");
  };

  const logout = async () => {
    try {
      await post(
        "/api/auth/logout/",
        {},
        {},
        { showLog: false, logError: false }
      );
    } catch (error) {
      console.warn("Erro ao fazer logout no servidor:", error);
    } finally {
      user.value = null;
      isAuthenticated.value = false;
      clearCsrfToken();
    }
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    checkAuth,
    login,
    logout,
  };
};

import { $fetch, type FetchError } from "ofetch";
import { useErrorHandler, type ErrorHandlerOptions } from "./useErrorHandler";

export function useApi() {
  const config = useRuntimeConfig();
  const { handleApiError } = useErrorHandler();

  let csrfToken: string | null = null;

  function redirect(url: string) {
    window.location.href = `${config.public.apiBase as string}${url}`;
  }

  async function getCsrfToken(): Promise<string> {
    if (csrfToken) {
      return csrfToken;
    }

    try {
      const response = await $fetch<{ csrfToken: string }>(
        "/api/auth/csrf-token/",
        {
          baseURL: config.public.apiBase as string,
          credentials: "include",
        }
      );
      csrfToken = response.csrfToken;
      return csrfToken;
    } catch (error) {
      console.error("Erro ao obter token CSRF:", error);
      throw error;
    }
  }

  function clearCsrfToken() {
    csrfToken = null;
  }

  async function get<T>(
    url: string,
    options: Record<string, any> = {},
    errorOptions?: ErrorHandlerOptions
  ): Promise<T> {
    try {
      return await $fetch<T>(url, {
        baseURL: config.public.apiBase as string,
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        ...options,
      });
    } catch (err) {
      const error = err as FetchError;

      if (errorOptions !== undefined) {
        handleApiError(error, errorOptions);
      } else {
        handleApiError(error, {
          showLog: false,
          logError: true,
        });
      }

      throw error;
    }
  }

  async function post<T>(
    url: string,
    body?: any,
    options: Record<string, any> = {},
    errorOptions?: ErrorHandlerOptions
  ): Promise<T> {
    try {
      const token = await getCsrfToken();
      return await $fetch<T>(url, {
        method: "POST",
        baseURL: config.public.apiBase as string,
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": token,
        },
        credentials: "include",
        body,
        ...options,
      });
    } catch (err) {
      const error = err as FetchError;

      if (errorOptions !== undefined) {
        handleApiError(error, errorOptions);
      } else {
        handleApiError(error, {
          showLog: false,
          logError: true,
        });
      }

      throw error;
    }
  }

  async function patch<T>(
    url: string,
    body?: any,
    options: Record<string, any> = {},
    errorOptions?: ErrorHandlerOptions
  ): Promise<T> {
    try {
      const token = await getCsrfToken();
      return await $fetch<T>(url, {
        method: "PATCH",
        baseURL: config.public.apiBase as string,
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": token,
        },
        credentials: "include",
        body,
        ...options,
      });
    } catch (err) {
      const error = err as FetchError;
      if (errorOptions !== undefined) {
        handleApiError(error, errorOptions);
      } else {
        handleApiError(error, {
          showLog: false,
          logError: true,
        });
      }
      throw error;
    }
  }

  async function del<T>(
    url: string,
    options: Record<string, any> = {},
    errorOptions?: ErrorHandlerOptions
  ): Promise<T> {
    try {
      const token = await getCsrfToken();
      return await $fetch<T>(url, {
        method: "DELETE",
        baseURL: config.public.apiBase as string,
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": token,
        },
        credentials: "include",
        ...options,
      });
    } catch (err) {
      const error = err as FetchError;
      if (errorOptions !== undefined) {
        handleApiError(error, errorOptions);
      } else {
        handleApiError(error, {
          showLog: false,
          logError: true,
        });
      }
      throw error;
    }
  }

  return {
    get,
    post,
    patch,
    delete: del,
    redirect,
    clearCsrfToken,
  };
}

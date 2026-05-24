import { api } from "@/lib/api";
import type { TokenResponse, User } from "@/types/api";

export type LoginInput = {
  email: string;
  password: string;
};

export async function login(input: LoginInput) {
  const form = new URLSearchParams();
  form.set("username", input.email);
  form.set("password", input.password);

  const { data } = await api.post<TokenResponse>("/auth/login", form, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    }
  });
  return data;
}

export async function getMe() {
  const { data } = await api.get<User>("/me");
  return data;
}

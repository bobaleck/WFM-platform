import { apiGet, apiPost, apiPut } from "./client";

export type OneCSettings = {
  connection_mode: "gateway_http" | "direct_com";
  gateway_url: string | null;
  gateway_token_saved: boolean;
  infobase_type: "server" | "file";
  onec_server: string | null;
  onec_database: string | null;
  onec_cluster: string | null;
  file_base_path: string | null;
  onec_username: string | null;
  password_saved: boolean;
  auth_type: string;
  request_timeout_seconds: number;
  enabled: boolean;
  verify_tls: boolean;
  auto_disable_dismissed: boolean;
  check_on_employee_create: boolean;
  enable_weekly_1c_status_check: boolean;
  weekly_1c_status_check_day: string;
  weekly_1c_status_check_time: string;
  onec_check_batch_size: number;
  onec_check_pause_ms: number;
  configured: boolean;
  last_check_status: string | null;
  last_check_message: string | null;
  last_check_at: string | null;
};

export type OneCSettingsPayload = OneCSettings & { password?: string; gateway_token?: string };

export function getOneCSettings(): Promise<OneCSettings> {
  return apiGet("/api/v1/integrations/onec/settings");
}

export function saveOneCSettings(payload: OneCSettingsPayload): Promise<OneCSettings> {
  return apiPut("/api/v1/integrations/onec/settings", payload);
}

export function checkOneC(): Promise<Record<string, unknown>> {
  return apiPost("/api/v1/integrations/onec/check", {});
}

export function diagnoseOneC(): Promise<Record<string, unknown>> {
  return apiPost("/api/v1/integrations/onec/diagnose", {});
}

export function diagnoseOneCEmployeeLookup(inn: string): Promise<Record<string, unknown>> {
  return apiPost("/api/v1/integrations/onec/diagnose-employee-lookup", { inn });
}

export type NaumenSettings = {
  base_url: string | null;
  api_version: "v2" | "current";
  auth_mode: "api_key" | "basic";
  username: string | null;
  api_key_masked: string | null;
  basic_password_masked: string | null;
  request_timeout_seconds: number;
  verify_ssl: boolean;
  enabled: boolean;
  configured: boolean;
  last_check_status: string | null;
  last_check_message: string | null;
  last_check_http_status: number | null;
  last_check_endpoint: string | null;
  last_check_at: string | null;
};

export type NaumenSettingsPayload = NaumenSettings & { api_key?: string; basic_password?: string };

export function getNaumenSettings(): Promise<NaumenSettings> {
  return apiGet("/api/v1/integrations/naumen/settings");
}

export function saveNaumenSettings(payload: NaumenSettingsPayload): Promise<NaumenSettings> {
  return apiPut("/api/v1/integrations/naumen/settings", payload);
}

export function checkNaumen(): Promise<Record<string, unknown>> {
  return apiPost("/api/v1/integrations/naumen/check", {});
}

export function diagnoseNaumen(): Promise<Record<string, unknown>> {
  return apiPost("/api/v1/integrations/naumen/diagnose", {});
}

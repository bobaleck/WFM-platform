export function Alert({ type = "success", children }: { type?: "success" | "error"; children: string }) {
  return <p className={type === "error" ? "error-text" : "success-text"}>{children}</p>;
}

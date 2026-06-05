import type { ButtonHTMLAttributes, ReactNode } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean;
  loadingText?: string;
  children: ReactNode;
};

export function AsyncButton({ loading = false, loadingText = "Выполняется...", children, disabled, ...props }: Props) {
  return (
    <button {...props} disabled={disabled || loading} aria-busy={loading}>
      {loading ? <span className="button-spinner" aria-hidden="true" /> : null}
      {loading ? loadingText : children}
    </button>
  );
}

import { useState } from "react";

export function BrandLogo() {
  const [failed, setFailed] = useState(false);
  return (
    <div className="brand-logo">
      {failed ? <span className="brand-logo-fallback">ТС</span> : <img src="/assets/cvet_tss.svg" alt="Телесейлз Сервис" onError={() => setFailed(true)} />}
      <div>
        <strong>Телесейлз Сервис</strong>
        <small>WFM-платформа</small>
      </div>
    </div>
  );
}

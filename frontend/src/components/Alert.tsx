import React from "react";

type Props = {
  kind?: "error" | "info" | "success" | "warning";
  message: string;
  onClose?: () => void;
};

export default function Alert({ kind = "info", message, onClose }: Props) {
  const bg =
    kind === "error"
      ? "#3b0d0d"
      : kind === "success"
      ? "#12351b"
      : kind === "warning"
      ? "#3b2f0d"
      : "#0d223b";
  const border =
    kind === "error"
      ? "#7f1d1d"
      : kind === "success"
      ? "#14532d"
      : kind === "warning"
      ? "#854d0e"
      : "#1d4ed8";
  return (
    <div
      style={{
        background: bg,
        border: `1px solid ${border}`,
        color: "white",
        padding: "10px 12px",
        borderRadius: 8,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
      }}
      role="alert"
    >
      <span>{message}</span>
      {onClose && (
        <button
          onClick={onClose}
          style={{
            background: "transparent",
            color: "white",
            border: "1px solid rgba(255,255,255,.2)",
            padding: "4px 8px",
            borderRadius: 6,
            cursor: "pointer",
          }}
        >
          닫기
        </button>
      )}
    </div>
  );
}

export const orangeColors = {
  primary: "#FF6600",      // Orange vif
  dark: "#1a1a1a",         // Noir/Gris foncé
  light: "#fff7ed",        // Blanc cassé
  gray: "#6b7280",         // Gris
  border: "#e5e7eb",       // Bordure grise
  success: "#10b981",      // Vert (LOW)
  warning: "#f59e0b",      // Jaune (MEDIUM)
  danger: "#ef4444",       // Rouge (HIGH/CRITICAL)
};

export const riskLevels = {
  LOW: { color: orangeColors.success, label: "Faible" },
  MEDIUM: { color: orangeColors.warning, label: "Moyen" },
  HIGH: { color: orangeColors.danger, label: "Élevé" },
  CRITICAL: { color: "#991b1b", label: "Critique" },
};
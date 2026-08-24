/**
 * Bouton personnalisé Orange
 */

import React from "react";
import { Button } from "@/src/components/ui/button";

interface OrangeButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "danger";
  size?: "sm" | "md" | "lg";
  children: React.ReactNode;
  loading?: boolean;
}

export function OrangeButton({
  variant = "primary",
  size = "md",
  loading = false,
  className = "",
  disabled = false,
  ...props
}: OrangeButtonProps) {
  const variants = {
    primary: "bg-orange-primary hover:bg-orange-600 text-white",
    secondary: "bg-gray-200 hover:bg-gray-300 text-gray-900",
    outline: "border-2 border-orange-primary text-orange-primary hover:bg-orange-primary hover:text-white",
    danger: "bg-red-600 hover:bg-red-700 text-white",
  };

  const sizes = {
    sm: "px-3 py-1 text-sm",
    md: "px-4 py-2 text-base",
    lg: "px-6 py-3 text-lg",
  };

  return (
    <Button
      className={`${variants[variant]} ${sizes[size]} ${className} transition duration-200`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? "Chargement..." : props.children}
    </Button>
  );
}
/**
 * Composant Card personnalisé Orange
 */

import React from "react";
import { Card as UICard, CardContent, CardDescription, CardHeader, CardTitle } from "@/src/components/ui/card";

interface CardProps {
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
  highlight?: boolean;
}

export function Card({ title, description, children, className = "", highlight = false }: CardProps) {
  return (
    <UICard className={`${highlight ? 'border-orange-primary border-2' : ''} ${className}`}>
      {(title || description) && (
        <CardHeader>
          {title && <CardTitle className="text-orange-primary">{title}</CardTitle>}
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
      )}
      <CardContent>
        {children}
      </CardContent>
    </UICard>
  );
}
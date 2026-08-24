/**
 * Types TypeScript pour le projet KYC
 */

export interface Document {
  id: string;
  name: string;
  type: "passport" | "id_card" | "driving_license" | "other";
  uploadedAt: Date;
  status: "pending" | "analyzing" | "completed" | "failed";
}

export interface Anomaly {
  id: string;
  type: string;
  description: string;
  riskLevel: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  location?: string;
}

export interface AnalysisResult {
  id: string;
  documentId: string;
  anomalies: Anomaly[];
  overallRisk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  analyzedAt: Date;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "analyst" | "user";
}
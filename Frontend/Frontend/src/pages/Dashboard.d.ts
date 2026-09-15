import type { ComponentType } from "react";

declare const Dashboard: ComponentType<{
  onLogout: () => void;
  initialPlan?: string;
}>;

export default Dashboard;

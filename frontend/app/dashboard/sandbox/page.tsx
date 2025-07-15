import { Metadata } from 'next';
import SandboxDashboard from '@/components/dashboard/sandbox-dashboard';

export const metadata: Metadata = {
  title: 'Sandbox Messagerie | BerinIA',
  description: 'Testez vos stratégies de messaging en simulant des conversations avec des prospects',
};

export default function SandboxPage() {
  return <SandboxDashboard />;
}

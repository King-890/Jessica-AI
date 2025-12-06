import Dashboard from '@/pages/Dashboard'

export type RouteDef = { path: string; name: string; element: JSX.Element }

export const routes: RouteDef[] = [
  { path: '/dashboard', name: 'Dashboard', element: <Dashboard /> },
]

export default routes
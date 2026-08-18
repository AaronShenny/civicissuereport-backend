import { createBrowserRouter, Navigate } from 'react-router-dom';

// Layout
import AppLayout from './layouts/AppLayout';

// Pages
import Landing from './pages/Landing';
import TrackComplaint from './pages/TrackComplaint';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Assets from './pages/Assets';
import AssetDetail from './pages/AssetDetail';
import AssetForm from './pages/AssetForm';
import Categories from './pages/Categories';
import Assignments from './pages/Assignments';
import Maintenance from './pages/Maintenance';
import Reports from './pages/Reports';
import Users from './pages/Users';
import Settings from './pages/Settings';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Landing />,
  },
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/track',
    element: <TrackComplaint />,
  },
  {
    element: <AppLayout />, // wraps all authenticated pages
    children: [
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'assets', element: <Assets /> },
      { path: 'assets/new', element: <AssetForm /> },
      { path: 'assets/:id', element: <AssetDetail /> },
      { path: 'assets/:id/edit', element: <AssetForm /> },
      { path: 'categories', element: <Categories /> },
      { path: 'assignments', element: <Assignments /> },
      { path: 'maintenance', element: <Maintenance /> },
      { path: 'reports', element: <Reports /> },
      { path: 'users', element: <Users /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);
